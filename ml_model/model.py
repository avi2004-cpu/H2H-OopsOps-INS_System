# ml_model/model.py

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

# 🔥 UPDATED FEATURES (VERY IMPORTANT)
FEATURES = [
    'traffic',
    'packet_rate',
    'signal',
    'mac_changed',
    'flap_count'
]

# Baseline thresholds
TRAFFIC_FLOOD_THRESHOLD  = 50
SIGNAL_DROP_THRESHOLD    = 40
PACKET_FLOOD_THRESHOLD   = 80


class AnomalyDetector:

    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            random_state=42
        )
        self.scaler  = StandardScaler()
        self.trained = False
        self.baseline_stats = {}

    def train(self, df: pd.DataFrame):
        """Train on clean baseline data only"""

        normal = df[
            (df['status'] == 'active') &
            (df['mac_changed'] == 0) &
            (df['flap_count'] == 0)
        ][FEATURES].fillna(0)

        self.baseline_stats = {
            'traffic_mean':     round(normal['traffic'].mean(), 1),
            'traffic_std':      round(normal['traffic'].std(), 1),
            'packet_rate_mean': round(normal['packet_rate'].mean(), 1),
            'signal_mean':      round(normal['signal'].mean(), 1),
        }

        X_scaled = self.scaler.fit_transform(normal)
        self.model.fit(X_scaled)

        self.trained = True

        print(f"[✓] Model trained on {len(normal)} samples")
        print(f"    Baseline → traffic: {self.baseline_stats['traffic_mean']} | "
              f"signal: {self.baseline_stats['signal_mean']} | "
              f"packet_rate: {self.baseline_stats['packet_rate_mean']}")

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.trained:
            raise ValueError("Model not trained yet.")

        df = df.copy()

        X = df[FEATURES].fillna(0)
        X_scaled = self.scaler.transform(X)

        df['anomaly_score'] = self.model.decision_function(X_scaled)
        df['is_anomaly']    = self.model.predict(X_scaled) == -1
        df['anomaly_type']  = df.apply(self._classify, axis=1)
        df['explanation']   = df.apply(self._explain, axis=1)
        df['severity']      = df.apply(self._severity, axis=1)

        return df

    # ─────────────────────────────────────────────

    def _classify(self, row):

        if not row['is_anomaly']:
            return 'normal'

        if row['status'] == 'offline':
            return 'device_offline'

        if row['mac_changed'] == 1:
            return 'mac_spoof'

        if row['flap_count'] > 2:
            return 'link_flap'

        if 'unknown' in str(row['device_id']).lower():
            return 'rogue_device'

        if row['traffic'] > TRAFFIC_FLOOD_THRESHOLD:
            return 'traffic_flood'

        if row['signal'] < SIGNAL_DROP_THRESHOLD:
            return 'signal_drop'

        if row['packet_rate'] > PACKET_FLOOD_THRESHOLD:
            return 'packet_flood'

        return 'suspicious_behavior'

    def _explain(self, row):

        t   = row['anomaly_type']
        dev = row['device_id']
        base = self.baseline_stats

        if t == 'normal':
            return 'Normal behavior'

        if t == 'device_offline':
            return f"{dev} is offline — link failure or AP down"

        if t == 'mac_spoof':
            return f"{dev} MAC address changed — possible spoofing attack"

        if t == 'link_flap':
            return f"{dev} experiencing link instability (flapping)"

        if t == 'rogue_device':
            return f"Unknown device {dev} detected — not in whitelist"

        if t == 'traffic_flood':
            avg = base.get('traffic_mean', 30)
            return f"Traffic spike on {dev}: {row['traffic']} vs avg {avg}"

        if t == 'signal_drop':
            avg = base.get('signal_mean', 75)
            return f"Weak signal on {dev}: {row['signal']} vs avg {avg}"

        if t == 'packet_flood':
            avg = base.get('packet_rate_mean', 50)
            return f"Packet flood on {dev}: {row['packet_rate']} vs avg {avg}"

        return f"Behavior anomaly on {dev} (score: {row['anomaly_score']:.3f})"

    def _severity(self, row):

        if not row['is_anomaly']:
            return 'none'

        score = abs(row['anomaly_score'])

        if score > 0.1:
            return 'high'
        if score > 0.05:
            return 'medium'
        return 'low'
