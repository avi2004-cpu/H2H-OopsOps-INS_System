# ml_model/data_loader.py
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(
    BASE_DIR, 'network_simulation', 'data', 'network_data.csv'
)

def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    print(f"[✓] Loaded {len(df)} rows, {df['device_id'].nunique()} devices")
    return df

def get_latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Returns only the most recent reading per device."""
    return df.sort_values('timestamp').groupby('device_id').last().reset_index()