# ml_model/data_loader.py
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'network_simulation', 'data', 'network_data.csv')

NUMERIC_COLS = ['traffic', 'packet_rate', 'signal', 'mac_changed', 'flap_count']

def load_data(path=CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    print(f"[✓] Loaded {len(df)} rows, {df['device_id'].nunique()} devices")
    return df

def get_latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values('timestamp').groupby('device_id').last().reset_index()