# ml_model/model.py
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

# ── Feature set ──────────────────────────────────────────────────────
BASE_FEATURES = ['traffic', 'packet_rate', 'signal']

TRAFFIC_FLOOD_THRESH  = 50
SIGNAL_DROP_THRESH    = 40
PACKET_FLOOD_THRESH   = 80


class AnomalyDetector:

    def __init__(self, contamination=0.1):
        self.contamination    = contamination
        self.global_model     = None
        self.global_scaler    = StandardScaler()
        self.device_baselines = {}
        self.type_baselines   = {}
        self.trained          = False
        self.baseline_stats   = {}
        self.all_features     = BASE_FEATURES + ['traffic_to_packet_ratio', 'signal_quality']

    # ── Training ─────────────────────────────────────────────────────

    def train(self, df: pd.DataFrame):
        clean = df[
            (df['status'] == 'active') &
            (~df['device_id'].str.contains('rogue', case=False, na=False)) &
            (~df.get('mac', pd.Series([''] * len(df))).str.upper().str.contains('FA:KE', na=False))
        ].copy()

        clean = self._engineer_features(clean)
        X = clean[self.all_features].fillna(0)
        X_scaled = self.global_scaler.fit_transform(X)

        self.global_model = IsolationForest(
            contamination=self.contamination,
            n_estimators=200,
            max_samples='auto',
            random_state=42
        )
        self.global_model.fit(X_scaled)

        # Per-device baseline
        for dev_id, grp in clean.groupby('device_id'):
            if len(grp) >= 5:
                self.device_baselines[dev_id] = {
                    'traffic_mean':     grp['traffic'].mean(),
                    'traffic_std':      max(grp['traffic'].std(), 1),
                    'packet_rate_mean': grp['packet_rate'].mean(),
                    'packet_rate_std':  max(grp['packet_rate'].std(), 1),
                    'signal_mean':      grp['signal'].mean(),
                    'signal_std':       max(grp['signal'].std(), 1),
                }

        # Per-type baseline
        if 'type' in clean.columns:
            for dtype, grp in clean.groupby('type'):
                self.type_baselines[dtype] = {
                    'traffic_mean': grp['traffic'].mean(),
                    'signal_mean':  grp['signal'].mean(),
                }

        # Global stats
        self.baseline_stats = {
            'traffic_mean':     round(clean['traffic'].mean(), 1),
            'traffic_std':      round(clean['traffic'].std(), 1),
            'packet_rate_mean': round(clean['packet_rate'].mean(), 1),
            'signal_mean':      round(clean['signal'].mean(), 1),
        }

        self.trained = True
        print(f"[✓] Model trained on {len(clean)} clean samples "
              f"across {clean['device_id'].nunique()} devices")
        print(f"    Baseline → traffic: {self.baseline_stats['traffic_mean']} pkts/s | "
              f"signal: {self.baseline_stats['signal_mean']} dBm")

    # ── Prediction ───────────────────────────────────────────────────

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.trained:
            raise ValueError("Call train() first.")

        df = df.copy()
        df = self._engineer_features(df)

        X        = df[self.all_features].fillna(0)
        X_scaled = self.global_scaler.transform(X)

        df['anomaly_score'] = self.global_model.decision_function(X_scaled)
        df['is_anomaly']    = self.global_model.predict(X_scaled) == -1

        # Per-device z-scores
        df['z_traffic'] = df.apply(self._z_traffic, axis=1)
        df['z_packet']  = df.apply(self._z_packet, axis=1)

        # Z-score override — catch what global model misses
        df.loc[df['z_traffic'].abs() > 3.5, 'is_anomaly'] = True
        df.loc[df['z_packet'].abs()  > 3.5, 'is_anomaly'] = True

        # Hard rules — always flag
        df.loc[df['status'] == 'offline', 'is_anomaly'] = True
        if 'mac' in df.columns:
            df.loc[df['mac'].str.upper().str.contains('FA:KE', na=False), 'is_anomaly'] = True
        df.loc[df['device_id'].str.contains('rogue', case=False, na=False), 'is_anomaly'] = True

        df['anomaly_type'] = df.apply(self._classify, axis=1)
        df['explanation']  = df.apply(self._explain, axis=1)
        df['severity']     = df.apply(self._severity, axis=1)
        df['confidence']   = df.apply(self._confidence, axis=1)

        return df

    # ── Feature engineering ──────────────────────────────────────────

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['traffic_to_packet_ratio'] = (
            df['traffic'] / df['packet_rate'].replace(0, 1)
        ).clip(0, 100)
        df['signal_quality'] = (df['signal'] / 100.0).clip(0, 1)
        return df

    # ── Z-score helpers ──────────────────────────────────────────────

    def _z_traffic(self, row) -> float:
        dev = row['device_id']
        if dev in self.device_baselines:
            b = self.device_baselines[dev]
            return (row['traffic'] - b['traffic_mean']) / b['traffic_std']
        b = self.baseline_stats
        return (row['traffic'] - b['traffic_mean']) / max(b.get('traffic_std', 1), 1)

    def _z_packet(self, row) -> float:
        dev = row['device_id']
        if dev in self.device_baselines:
            b = self.device_baselines[dev]
            return (row['packet_rate'] - b['packet_rate_mean']) / b['packet_rate_std']
        return 0.0

    # ── Classification ───────────────────────────────────────────────

    def _classify(self, row) -> str:
        if not row['is_anomaly']:
            return 'normal'
        if row['status'] == 'offline':
            return 'device_offline'
        if 'mac' in row.index and 'FA:KE' in str(row.get('mac', '')).upper():
            return 'mac_spoof'
        if 'rogue' in str(row['device_id']).lower():
            return 'rogue_device'
        if row.get('z_traffic', 0) > 3.5 or row['traffic'] > TRAFFIC_FLOOD_THRESH:
            return 'traffic_flood'
        if row['signal'] < SIGNAL_DROP_THRESH:
            return 'signal_drop'
        if row.get('z_packet', 0) > 3.5 or row['packet_rate'] > PACKET_FLOOD_THRESH:
            return 'packet_flood'
        return 'suspicious_behavior'

    # ── Explainability ───────────────────────────────────────────────

    def _explain(self, row) -> str:
        t   = row['anomaly_type']
        dev = row['device_id']
        b   = self.device_baselines.get(dev, self.baseline_stats)

        if t == 'normal':
            return 'Normal behavior'

        if t == 'device_offline':
            return (f"{dev} is offline — "
                    f"signal: {row['signal']} dBm, traffic: {row['traffic']} pkts/s. "
                    f"Possible link failure or device powered down.")

        if t == 'mac_spoof':
            return (f"MAC address forgery on {dev}: "
                    f"{row.get('mac','?')} is not a valid hardware address. "
                    f"Possible identity spoofing attack.")

        if t == 'rogue_device':
            return (f"Unauthorised device {dev} on network. "
                    f"MAC {row.get('mac','?')} not in approved list. "
                    f"Possible intrusion attempt.")

        if t == 'traffic_flood':
            avg = round(b.get('traffic_mean', self.baseline_stats['traffic_mean']), 1)
            pct = round((row['traffic'] - avg) / max(avg, 1) * 100)
            z   = round(row.get('z_traffic', 0), 2)
            return (f"Traffic flood on {dev}: "
                    f"{row['traffic']} pkts/s vs device baseline {avg} pkts/s "
                    f"(+{pct}%, z-score: {z}). Possible DoS or misconfiguration.")

        if t == 'signal_drop':
            avg = round(b.get('signal_mean', self.baseline_stats['signal_mean']), 1)
            return (f"Signal degradation on {dev}: "
                    f"{row['signal']} dBm vs baseline {avg} dBm. "
                    f"Possible interference or hardware fault.")

        if t == 'packet_flood':
            avg = round(b.get('packet_rate_mean', self.baseline_stats['packet_rate_mean']), 1)
            z   = round(row.get('z_packet', 0), 2)
            return (f"Packet rate anomaly on {dev}: "
                    f"{row['packet_rate']} pkts/s vs baseline {avg} pkts/s "
                    f"(z-score: {z}). Possible scanning or DoS.")

        return (f"Behavioural anomaly on {dev} — "
                f"Isolation Forest score: {row['anomaly_score']:.3f}. "
                f"Multiple metrics deviate from learned baseline.")

    # ── Severity & Confidence ────────────────────────────────────────

    def _severity(self, row) -> str:
        if not row['is_anomaly']:
            return 'none'
        t = row['anomaly_type']
        if t in ('mac_spoof', 'rogue_device'):
            return 'critical'
        if t == 'device_offline':
            return 'high'
        z = max(abs(row.get('z_traffic', 0)), abs(row.get('z_packet', 0)))
        score = abs(row['anomaly_score'])
        if z > 4 or score > 0.15:
            return 'high'
        if z > 2.5 or score > 0.08:
            return 'medium'
        return 'low'

    def _confidence(self, row) -> str:
        if not row['is_anomaly']:
            return '—'
        t = row['anomaly_type']
        if t in ('mac_spoof', 'rogue_device', 'device_offline'):
            return 'high'
        z = max(abs(row.get('z_traffic', 0)), abs(row.get('z_packet', 0)))
        if z > 3.5:
            return 'high'
        if z > 2:
            return 'medium'
        return 'low'

    # ── Reporting ────────────────────────────────────────────────────

    def summary(self, results: pd.DataFrame) -> dict:
        anomalies = results[results['is_anomaly']]
        return {
            'total_devices':   len(results),
            'anomaly_count':   len(anomalies),
            'normal_count':    len(results) - len(anomalies),
            'anomaly_types':   anomalies['anomaly_type'].value_counts().to_dict(),
            'severity_counts': anomalies['severity'].value_counts().to_dict(),
            'baseline':        self.baseline_stats,
        }