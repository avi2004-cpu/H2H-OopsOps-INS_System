# ml_model/model.py
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

FEATURES = ['traffic', 'packet_rate', 'signal']

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.trained = False

    def train(self, df: pd.DataFrame):
    # Exclude known rogue devices from training baseline
        normal = df[
            (df['status'] == 'active') &
            (~df['device_id'].str.contains('rogue', case=False, na=False))
        ][FEATURES].fillna(0)
        X_scaled = self.scaler.fit_transform(normal)
        self.model.fit(X_scaled)
        self.trained = True
        print(f"[✓] Model trained on {len(normal)} normal samples")
        
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.trained:
            raise ValueError("Model not trained yet.")
        df = df.copy()
        X = df[FEATURES].fillna(0)
        X_scaled = self.scaler.transform(X)
        df['anomaly_score'] = self.model.decision_function(X_scaled)
        df['is_anomaly'] = self.model.predict(X_scaled) == -1
        df['anomaly_type'] = df.apply(self._classify, axis=1)
        df['explanation'] = df.apply(self._explain, axis=1)
        return df

    def _classify(self, row):
        if not row['is_anomaly']:
            return 'normal'
        if row['traffic'] > 150:
            return 'traffic_flood'
        if row['status'] == 'offline':
            return 'device_offline'
        if row['signal'] < 20:
            return 'signal_drop'
    # Catch rogue devices by MAC pattern or device_id
        if 'rogue' in str(row['device_id']).lower():
            return 'rogue_device'
        return 'unknown_anomaly'

    def _explain(self, row):
        t = row['anomaly_type']
        if t == 'normal':
            return 'Normal behavior'
        if t == 'traffic_flood':
            return (f"Traffic spike on {row['device_id']}: "
                    f"{row['traffic']} pkts/s (normal ~30)")
        if t == 'device_offline':
            return f"{row['device_id']} went offline"
        if t == 'signal_drop':
            return (f"Weak signal on {row['device_id']}: "
                    f"{row['signal']} dBm (normal >60)")
        return f"Anomaly score: {row['anomaly_score']:.3f}"