"""Print NV1-to-NV4 reconciliation using the shared production pipeline."""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import RAW_DATA_FILE
from src.nv4_analysis import prepare_nv4_sessions, build_station_criteria

raw = pd.read_csv(RAW_DATA_FILE, encoding="utf-8-sig", low_memory=False)
sessions, ledger, metadata = prepare_nv4_sessions(raw)
stations, eligible = build_station_criteria(sessions)
ledger = pd.concat([
    ledger,
    pd.DataFrame([
        {"stage": "Distinct stations after NV4 filters", "rows_remaining": len(stations),
         "removed_at_stage": None, "rule": "Unique normalized Station Name"},
        {"stage": "Stations eligible for ranking", "rows_remaining": len(eligible),
         "removed_at_stage": len(stations) - len(eligible), "rule": "At least 500 NV4-valid sessions"},
        {"stage": "Sessions in eligible stations", "rows_remaining": int(eligible.C1_so_phien.sum()),
         "removed_at_stage": len(sessions) - int(eligible.C1_so_phien.sum()),
         "rule": "Sessions in stations meeting the 500-session threshold"},
    ])
], ignore_index=True)
print("NV4 session reconciliation")
print(ledger.to_string(index=False))
print("\nRun metadata")
print(pd.Series({**metadata, "station_count_after_cleaning": len(stations),
                 "eligible_station_count": len(eligible),
                 "sessions_in_eligible_stations": int(eligible.C1_so_phien.sum())}).to_string())
