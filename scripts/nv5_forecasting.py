"""NV5: reproducible 15-minute EV port occupancy and session demand forecasting.

Run at repository root: python scripts/nv5_forecasting.py
Prefers NV1's processed parquet; falls back to the repository's raw CSV if pyarrow unavailable.
No existing NV1–NV4 modules/files are changed.
"""
from __future__ import annotations
import sys
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import SESSIONS_FEATURES_PARQUET, RAW_DATA_FILE

OUT = ROOT / 'outputs' / 'nv5'
OUT.mkdir(parents=True, exist_ok=True)
STEP = pd.Timedelta(minutes=15)
SEED = 42


def load_sessions():
    """Use NV1 validity flags if processed data readable; otherwise recompute NV1 flags."""
    if SESSIONS_FEATURES_PARQUET.exists():
        try:
            d = pd.read_parquet(SESSIONS_FEATURES_PARQUET)
            print('Source: NV1 processed sessions_features.parquet')
            return d, 'nv1_parquet'
        except (ImportError, ValueError, OSError) as e:
            print('Processed parquet unavailable:', str(e)[:150])
    from src.feature_engineering import build_clean_pipeline
    print('Fallback: recreate NV1 cleaning flags from repository raw CSV')
    raw = pd.read_csv(RAW_DATA_FILE, low_memory=False)
    d, _, _ = build_clean_pipeline(raw)
    return d, 'nv1_raw_recomputed'


def make_regular_series(df):
    needed = ['start_datetime_utc','end_datetime_utc','Energy (kWh)','is_valid_session','port_id']
    absent = [c for c in needed if c not in df]
    if absent: raise ValueError(f'Missing NV1 columns: {absent}')
    df = df.loc[df.is_valid_session, needed].copy()
    df['start_datetime_utc'] = pd.to_datetime(df['start_datetime_utc'], errors='coerce')
    df['end_datetime_utc'] = pd.to_datetime(df['end_datetime_utc'], errors='coerce')
    df['Energy (kWh)'] = pd.to_numeric(df['Energy (kWh)'], errors='coerce')
    df = df.dropna(subset=['start_datetime_utc','end_datetime_utc'])
    df = df.loc[df.end_datetime_utc > df.start_datetime_utc]
    df = df.sort_values('start_datetime_utc').reset_index(drop=True)
    # 15-min UTC bins [bin_start, bin_end). Occupied if connection interval overlaps bin.
    left = df.start_datetime_utc.min().floor('15min')
    right = df.end_datetime_utc.max().ceil('15min')
    index = pd.date_range(left, right - STEP, freq='15min')
    n = len(index)
    # Difference array avoids exploding each session into many time slots.
    starts = ((df.start_datetime_utc - left) // STEP).to_numpy(dtype=int)
    # End is exclusive. A session ending exactly on boundary does not occupy the next bin.
    ends = ((df.end_datetime_utc - left + STEP - pd.Timedelta(nanoseconds=1)) // STEP).to_numpy(dtype=int)
    ends = np.minimum(ends, n)
    diffs = np.zeros(n + 1, dtype=np.int64)
    np.add.at(diffs, starts, 1)
    np.add.at(diffs, ends, -1)
    occupancy = np.cumsum(diffs[:-1])
    arrivals = np.bincount(starts, minlength=n)
    # Energy belongs to sessions, NOT a measured 15-min electrical load.
    energy_at_start = np.bincount(starts, weights=df['Energy (kWh)'].fillna(0).to_numpy(), minlength=n)
    series = pd.DataFrame({'occupancy_ports':occupancy,'session_arrivals':arrivals,
                           'session_energy_kwh_at_start':energy_at_start}, index=index)
    series.index.name = 'time_utc'
    # For overflow diagnosis only: number of unique ports observed across whole dataset
    info = {'valid_sessions':int(len(df)), 'observed_ports':int(df.port_id.nunique()),
            'first_utc':str(left),'last_utc':str(right),'time_bins':int(n),
            'max_occupancy':int(occupancy.max()), 'max_arrivals':int(arrivals.max()),
            'overlap_port_limit_slots':int((occupancy > df.port_id.nunique()).sum())}
    return series, info


def add_features(series, target):
    s = series[[target]].copy()
    t = s.index
    slot = t.hour * 4 + t.minute // 15
    dow = t.dayofweek
    s['slot'] = slot.astype(int)
    s['dow'] = dow.astype(int)
    s['month'] = t.month.astype(int)
    s['weekend'] = (dow >= 5).astype(int)
    s['hour_sin'] = np.sin(2 * np.pi * slot / 96)
    s['hour_cos'] = np.cos(2 * np.pi * slot / 96)
    s['week_sin'] = np.sin(2 * np.pi * dow / 7)
    s['week_cos'] = np.cos(2 * np.pi * dow / 7)
    for lag in (1,4,96,672):
        s[f'lag_{lag}'] = s[target].shift(lag)
    for window in (4,96,672):
        s[f'rolling_mean_{window}'] = s[target].shift(1).rolling(window, min_periods=window).mean()
    return s.dropna().copy()


def metrics(y,p):
    y = np.asarray(y, dtype=float); p = np.asarray(p, dtype=float)
    return {'MAE':float(mean_absolute_error(y,p)),
            'RMSE':float(np.sqrt(mean_squared_error(y,p))),
            'R2':float(r2_score(y,p))}


def plot_examples(test, preds, target):
    # One week example from test; never present this as model-wide score.
    n = min(672,len(test))
    fig, ax = plt.subplots(figsize=(13,4))
    x = test.index[:n]
    ax.plot(x,test[target].iloc[:n],label='Actual',linewidth=1.1)
    ax.plot(x,preds['XGBoost'][:n],label='XGBoost',linewidth=1.1)
    ax.plot(x,preds['Lag-1 Day'][:n],label='Lag-1 Day',linewidth=1,alpha=.65)
    ax.set(ylabel='Occupied ports' if target=='occupancy_ports' else 'Arriving sessions',
           title=f'NV5: {target}, first 7 days of test (UTC)')
    ax.legend(); fig.autofmt_xdate(); fig.tight_layout()
    p=OUT/f'{target}_forecast_week.png';fig.savefig(p,dpi=135);plt.close(fig)


def run_target(series, target):
    from xgboost import XGBRegressor
    d=add_features(series,target)
    border=int(len(d)*.8)
    train,test=d.iloc[:border],d.iloc[border:]
    cols=[c for c in d.columns if c != target]
    ytr=train[target].to_numpy(); yte=test[target].to_numpy()
    # Mean by (day of week, 15-min slot) learned ONLY on training data.
    hist=train.groupby(['dow','slot'])[target].mean()
    default=float(train[target].mean())
    keys=list(zip(test['dow'],test['slot']))
    hist_pred=np.array([hist.get(key,default) for key in keys])
    predictions={'Historical Mean':hist_pred,
                 'Lag-1 Day':test['lag_96'].to_numpy(),
                 'Lag-1 Week':test['lag_672'].to_numpy()}
    models={
      'Ridge':Ridge(alpha=10.0),
      'Random Forest':RandomForestRegressor(n_estimators=80,max_depth=14,
                  min_samples_leaf=4,n_jobs=-1,random_state=SEED),
      'XGBoost':XGBRegressor(n_estimators=220,max_depth=6,learning_rate=.06,
                   subsample=.85,colsample_bytree=.9,tree_method='hist',
                   objective='reg:squarederror',n_jobs=4,random_state=SEED)
    }
    for name,model in models.items():
        # RF subsampling limits laptop memory while keeping chronological split untouched.
        Xtr=train[cols]
        ytrain=ytr
        if name=='Random Forest' and len(train)>100000:
            ii=np.linspace(0,len(train)-1,100000,dtype=int)
            Xtr=Xtr.iloc[ii];ytrain=ytr[ii]
        print('  fit',target,name,flush=True)
        model.fit(Xtr,ytrain)
        predictions[name]=np.maximum(0,model.predict(test[cols]))
    records=[]
    for name,p in predictions.items():
        records.append({'target':target,'model':name,'train_rows':len(train),'test_rows':len(test),
                        'train_end_utc':str(train.index[-1]),'test_start_utc':str(test.index[0]),
                        **metrics(yte,p)})
    scores=pd.DataFrame(records).sort_values('RMSE')
    scores.to_csv(OUT/f'{target}_metrics.csv',index=False)
    plot_examples(test,predictions,target)
    importance=pd.Series(models['XGBoost'].feature_importances_, index=cols).sort_values(ascending=False)
    importance.rename_axis('feature').reset_index(name='importance').to_csv(OUT/f'{target}_feature_importance.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,5));importance.head(12).sort_values().plot.barh(ax=ax)
    ax.set_title(f'XGBoost feature importance: {target}');fig.tight_layout()
    fig.savefig(OUT/f'{target}_feature_importance.png',dpi=135);plt.close(fig)
    return scores


def main():
    df, provenance=load_sessions()
    series,info=make_regular_series(df)
    info['source']=provenance
    pd.Series(info).to_json(OUT/'data_audit.json',indent=2,force_ascii=False)
    # Compact full-resolution time series; generated locally, not tracked by default.
    series.to_csv(OUT/'timeseries_15min.csv')
    fig,ax=plt.subplots(figsize=(10,4))
    hourly=series.groupby(series.index.hour)[['occupancy_ports','session_arrivals']].mean()
    hourly.plot(ax=ax);ax.set(xlabel='Hour (UTC)',title='Average 15-minute occupancy and arrivals by UTC hour')
    fig.tight_layout();fig.savefig(OUT/'nv5_seasonality.png',dpi=135);plt.close(fig)
    all_scores=[]
    for target in ('occupancy_ports','session_arrivals'):
        all_scores.append(run_target(series,target))
    summary=pd.concat(all_scores,ignore_index=True)
    summary.to_csv(OUT/'nv5_model_comparison.csv',index=False)
    print('\nNV5 COMPARISON\n',summary.to_string(index=False))
    print('Artifacts:',OUT)

if __name__=='__main__':main()
