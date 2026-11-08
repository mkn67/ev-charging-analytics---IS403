"""NV5 tests: boundary conventions, no future-dependent rolling features."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1]/'scripts'/'nv5_forecasting.py'
spec=importlib.util.spec_from_file_location('nv5_forecasting',SCRIPT)
nv5=importlib.util.module_from_spec(spec)
spec.loader.exec_module(nv5)


def test_occupancy_end_exclusive():
    d=pd.DataFrame({
        'start_datetime_utc':pd.to_datetime(['2020-01-01 00:00','2020-01-01 00:07']),
        'end_datetime_utc':pd.to_datetime(['2020-01-01 00:15','2020-01-01 00:22']),
        'Energy (kWh)':[1,2], 'is_valid_session':[True,True], 'port_id':['a','b']})
    s,info=nv5.make_regular_series(d)
    assert s['occupancy_ports'].tolist()==[2,1]
    assert s['session_arrivals'].tolist()==[2,0]
    assert s['session_energy_kwh_at_start'].tolist()==[3,0]


def test_rolling_features_exclude_present_and_future():
    idx=pd.date_range('2020-01-01',periods=700,freq='15min')
    a=pd.DataFrame({'occupancy_ports':np.arange(700,dtype=float)},index=idx)
    f=nv5.add_features(a,'occupancy_ports')
    # At the first retained time 672, rolling mean(4) uses 668..671 only.
    assert f.iloc[0].lag_1==671
    assert f.iloc[0].rolling_mean_4==np.mean([668,669,670,671])
    a.loc[idx[-1],'occupancy_ports']=999999
    f2=nv5.add_features(a,'occupancy_ports')
    assert np.array_equal(f.drop(columns='occupancy_ports').to_numpy(),f2.drop(columns='occupancy_ports').to_numpy())
