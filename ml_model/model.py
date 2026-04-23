# ml_model/model.py
"""
Anomaly Detection Model — INSS (Intelligent Network Surveillance System)
Hack2Hire 1.0 · Team OopsOps

Detection architecture:
  Layer 1 — Hard rules       (rule-based, always deterministic)
  Layer 2 — Per-device stats (dynamic thresholds: mean + k*std per device)
  Layer 3 — Global ML        (Isolation Forest with RobustScaler)

Anomaly priority (highest → lowest):
  1. rogue_device    — unknown MAC on network
  2. mac_spoof       — forged / changed MAC address
  3. device_offline  — link down or powered off
  4. link_flap       — repeated up/down cycling
  5. traffic_flood   — extreme traffic spike
  6. packet_flood    — extreme packet rate
  7. signal_drop     — weak RF signal
  8. suspicious_behavior — ML-only, no threshold match
"""

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler  
import pandas as pd
import numpy as np

# ── Feature set ───────────────────────────────────────────────────────
BASE_FEATURES = ['traffic', 'packet_rate', 'signal', 'mac_changed', 'flap_count']

# ── Global fallback thresholds (overridden per-device at runtime) ─────
# Calibrated to actual CSV ranges:
#   traffic:     1 – ~100 normal, spikes to millions
#   signal:      0 – 100
#   packet_rate: 0 – 335
GLOBAL_TRAFFIC_FLOOD  = 500
GLOBAL_SIGNAL_DROP    = 20
GLOBAL_PACKET_FLOOD   = 250

# Z-score sensitivity — 3.5 avoids over-triggering on normal variance
Z_THRESHOLD = 3.5

# Anomaly priority map — lower number = higher priority
PRIORITY = {
    'rogue_device':       1,
    'mac_spoof':          2,
    'device_offline':     3,
    'link_flap':          4,
    'traffic_flood':      5,
    'packet_flood':       6,
    'signal_drop':        7,
    'suspicious_behavior':8,
    'normal':             9,
}


class AnomalyDetector:

    def __init__(self, contamination=0.1):
        self.contamination    = contamination
        self.global_model     = None
        # RobustScaler uses median/IQR — resistant to extreme traffic spikes
        self.global_scaler    = RobustScaler()
        self.device_baselines = {}   # per-device dynamic thresholds
        self.type_baselines   = {}
        self.trained          = False
        self.baseline_stats   = {}
        self.all_features     = BASE_FEATURES + ['traffic_to_packet_ratio', 'signal_quality']

    # ══════════════════════════════════════════════════════════════════
    # TRAINING
    # ══════════════════════════════════════════════════════════════════

    def train(self, df: pd.DataFrame):
        """
        Train on clean baseline data only.
        Builds per-device dynamic thresholds (mean ± k*std) so each
        device is judged against its own normal behaviour.
        """
        for col in ['mac_changed', 'flap_count']:
            if col not in df.columns:
                df[col] = 0
        for col in ['traffic', 'packet_rate', 'signal', 'mac_changed', 'flap_count']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        clean = df[
            (df['status'] == 'active') &
            (df['mac_changed'] == 0) &
            (~df['mac'].astype(str).str.startswith('RG:')) &
            (~df['mac'].astype(str).str.upper().str.contains('FA:KE', na=False))
        ].copy()

        # Cap extreme traffic at 99th percentile so scaler isn't destroyed
        traffic_cap = clean['traffic'].quantile(0.99)
        clean['traffic'] = clean['traffic'].clip(upper=traffic_cap)

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

        # ── Per-device dynamic thresholds ─────────────────────────────
        # Each device gets its own flood/drop thresholds: mean + 3*std
        for dev_id, grp in clean.groupby('device_id'):
            if len(grp) < 5:
                continue
            t_mean = grp['traffic'].mean()
            t_std  = max(grp['traffic'].std(), 1)
            p_mean = grp['packet_rate'].mean()
            p_std  = max(grp['packet_rate'].std(), 1)
            s_mean = grp['signal'].mean()
            s_std  = max(grp['signal'].std(), 1)
            self.device_baselines[dev_id] = {
                'traffic_mean':          t_mean,
                'traffic_std':           t_std,
                'traffic_flood_thresh':  t_mean + 3 * t_std,  # dynamic
                'packet_rate_mean':      p_mean,
                'packet_rate_std':       p_std,
                'packet_flood_thresh':   p_mean + 3 * p_std,  # dynamic
                'signal_mean':           s_mean,
                'signal_std':            s_std,
                'signal_drop_thresh':    max(s_mean - 3 * s_std, 5),  # dynamic
            }

        # Per-type baseline
        if 'type' in clean.columns:
            for dtype, grp in clean.groupby('type'):
                self.type_baselines[dtype] = {
                    'traffic_mean': grp['traffic'].mean(),
                    'signal_mean':  grp['signal'].mean(),
                }

        # Global fallback stats
        self.baseline_stats = {
            'traffic_mean':     round(clean['traffic'].mean(), 1),
            'traffic_std':      round(clean['traffic'].std(), 1),
            'packet_rate_mean': round(clean['packet_rate'].mean(), 1),
            'signal_mean':      round(clean['signal'].mean(), 1),
        }

        self.trained = True
        print(f"[✓] Model trained on {len(clean)} clean samples "
              f"across {clean['device_id'].nunique()} devices")
        print(f"    Global baseline → "
              f"traffic: {self.baseline_stats['traffic_mean']} pkts/s | "
              f"signal: {self.baseline_stats['signal_mean']} dBm | "
              f"packet_rate: {self.baseline_stats['packet_rate_mean']}")

    # ══════════════════════════════════════════════════════════════════
    # PREDICTION
    # ══════════════════════════════════════════════════════════════════

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.trained:
            raise ValueError("Call train() first.")

        for col in ['mac_changed', 'flap_count']:
            if col not in df.columns:
                df[col] = 0
        for col in ['traffic', 'packet_rate', 'signal', 'mac_changed', 'flap_count']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df = df.copy()
        df = self._engineer_features(df)

        X        = df[self.all_features].fillna(0)
        X_scaled = self.global_scaler.transform(X)

        # Layer 3 — Global ML scores
        df['anomaly_score'] = self.global_model.decision_function(X_scaled)
        df['is_anomaly']    = self.global_model.predict(X_scaled) == -1
        df['detection_method'] = df['is_anomaly'].map({True: 'ml', False: 'normal'})

        # Per-device z-scores
        df['z_traffic'] = df.apply(self._z_traffic, axis=1)
        df['z_packet']  = df.apply(self._z_packet,  axis=1)

        # Layer 2 — Per-device dynamic threshold override
        df.loc[df['z_traffic'].abs() > Z_THRESHOLD, 'is_anomaly'] = True
        df.loc[df['z_packet'].abs()  > Z_THRESHOLD, 'is_anomaly'] = True
        # Mark these as stat-based
        mask_stat = (
            (df['z_traffic'].abs() > Z_THRESHOLD) |
            (df['z_packet'].abs()  > Z_THRESHOLD)
        )
        df.loc[mask_stat & (df['detection_method'] == 'normal'), 'detection_method'] = 'stat'
        df.loc[mask_stat & (df['detection_method'] == 'ml'),     'detection_method'] = 'ml+stat'

        # Layer 1 — Hard rules (always deterministic, highest priority)
        rule_mask = pd.Series(False, index=df.index)
        rule_mask |= df['status'] == 'offline'
        rule_mask |= df['mac_changed'] == 1
        rule_mask |= df['mac'].astype(str).str.startswith('RG:')
        rule_mask |= df['mac'].astype(str).str.upper().str.contains('FA:KE', na=False)
        rule_mask |= df['flap_count'] > 0

        df.loc[rule_mask, 'is_anomaly']        = True
        df.loc[rule_mask, 'detection_method']  = 'rule'

        # Classify, explain, score
        df['anomaly_type'] = df.apply(self._classify,   axis=1)
        df['explanation']  = df.apply(self._explain,    axis=1)
        df['severity']     = df.apply(self._severity,   axis=1)
        df['confidence']   = df.apply(self._confidence_pct, axis=1)  # 0–100
        df['priority']     = df['anomaly_type'].map(PRIORITY).fillna(9).astype(int)

        return df

    # ══════════════════════════════════════════════════════════════════
    # FEATURE ENGINEERING
    # ══════════════════════════════════════════════════════════════════

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['traffic_to_packet_ratio'] = (
            df['traffic'] / df['packet_rate'].replace(0, 1)
        ).clip(0, 1000)
        df['signal_quality'] = (df['signal'] / 100.0).clip(0, 1)
        for col in ['mac_changed', 'flap_count']:
            if col not in df.columns:
                df[col] = 0
        return df

    # ══════════════════════════════════════════════════════════════════
    # Z-SCORE HELPERS (use per-device baseline if available)
    # ══════════════════════════════════════════════════════════════════

    def _z_traffic(self, row) -> float:
        b = self.device_baselines.get(row['device_id'], None)
        if b:
            return (row['traffic'] - b['traffic_mean']) / b['traffic_std']
        return (row['traffic'] - self.baseline_stats['traffic_mean']) / \
               max(self.baseline_stats.get('traffic_std', 1), 1)

    def _z_packet(self, row) -> float:
        b = self.device_baselines.get(row['device_id'], None)
        if b:
            return (row['packet_rate'] - b['packet_rate_mean']) / b['packet_rate_std']
        return 0.0

    # ══════════════════════════════════════════════════════════════════
    # CLASSIFICATION — priority-ordered, single primary type
    # ══════════════════════════════════════════════════════════════════

    def _classify(self, row) -> str:
        if not row['is_anomaly']:
            return 'normal'

        mac = str(row.get('mac', ''))

        # ── Layer 1: Rule-based (security threats first) ──────────────
        if mac.startswith('RG:'):
            return 'rogue_device'
        if 'FA:KE' in mac.upper() or row.get('mac_changed', 0) == 1:
            return 'mac_spoof'
        if row['status'] == 'offline':
            return 'device_offline'
        if row.get('flap_count', 0) > 0:
            return 'link_flap'

        # ── Layer 2: Per-device dynamic thresholds ────────────────────
        b = self.device_baselines.get(row['device_id'], None)

        t_thresh = b['traffic_flood_thresh'] if b else GLOBAL_TRAFFIC_FLOOD
        p_thresh = b['packet_flood_thresh']  if b else GLOBAL_PACKET_FLOOD
        s_thresh = b['signal_drop_thresh']   if b else GLOBAL_SIGNAL_DROP

        if row['traffic'] > t_thresh:
            return 'traffic_flood'
        if row['packet_rate'] > p_thresh:
            return 'packet_flood'
        if row['signal'] < s_thresh and row['signal'] > 0:
            return 'signal_drop'

        # ── Layer 3: Z-score based ────────────────────────────────────
        if row.get('z_traffic', 0) > Z_THRESHOLD:
            return 'traffic_flood'
        if row.get('z_packet', 0) > Z_THRESHOLD:
            return 'packet_flood'

        return 'suspicious_behavior'

    # ══════════════════════════════════════════════════════════════════
    # EXPLAINABILITY
    # ══════════════════════════════════════════════════════════════════

    def _explain(self, row) -> str:
        t   = row['anomaly_type']
        dev = row['device_id']
        b   = self.device_baselines.get(dev, self.baseline_stats)
        dm  = row.get('detection_method', '?')

        if t == 'normal':
            return 'Normal behavior'

        if t == 'rogue_device':
            return (f"Unauthorised device {dev} on network — "
                    f"MAC {row.get('mac','?')} has RG: prefix, "
                    f"not in approved device registry. Possible intrusion.")

        if t == 'mac_spoof':
            return (f"MAC anomaly on {dev}: address {row.get('mac','?')} "
                    f"{'changed mid-session' if row.get('mac_changed',0)==1 else 'is forged'}. "
                    f"Possible ARP poisoning or identity spoofing.")

        if t == 'device_offline':
            return (f"{dev} is offline — signal: {row['signal']} dBm, "
                    f"traffic: {row['traffic']} pkts/s. "
                    f"Possible link failure or device powered down.")

        if t == 'link_flap':
            return (f"Link instability on {dev}: flap_count={row.get('flap_count',0)}. "
                    f"Repeated connect/disconnect cycles detected. "
                    f"Possible physical fault or DoS.")

        if t == 'traffic_flood':
            avg = round(b.get('traffic_mean', self.baseline_stats['traffic_mean']), 1)
            z   = round(row.get('z_traffic', 0), 2)
            thr = round(b.get('traffic_flood_thresh', GLOBAL_TRAFFIC_FLOOD), 1) if self.device_baselines.get(dev) else GLOBAL_TRAFFIC_FLOOD
            try:
                pct = round((row['traffic'] - avg) / max(avg, 1) * 100)
                return (f"Traffic flood on {dev} [{dm}]: {row['traffic']:,.0f} pkts/s "
                        f"vs device baseline {avg} pkts/s "
                        f"(+{pct}%, z={z}, threshold={thr}). "
                        f"Possible DoS or misconfigured device.")
            except Exception:
                return f"Traffic flood on {dev}: {row['traffic']} pkts/s (z={z})."

        if t == 'signal_drop':
            avg = round(b.get('signal_mean', self.baseline_stats['signal_mean']), 1)
            thr = round(b.get('signal_drop_thresh', GLOBAL_SIGNAL_DROP), 1) if self.device_baselines.get(dev) else GLOBAL_SIGNAL_DROP
            return (f"Signal drop on {dev}: {row['signal']} dBm "
                    f"vs baseline {avg} dBm (threshold={thr}). "
                    f"Possible RF interference or hardware fault.")

        if t == 'packet_flood':
            avg = round(b.get('packet_rate_mean', self.baseline_stats['packet_rate_mean']), 1)
            z   = round(row.get('z_packet', 0), 2)
            return (f"Packet flood on {dev} [{dm}]: {row['packet_rate']} pkts/s "
                    f"vs baseline {avg} pkts/s (z={z}). "
                    f"Possible scanning or UDP flood.")

        return (f"Suspicious behaviour on {dev} [{dm}]: "
                f"Isolation Forest score={row['anomaly_score']:.3f}, "
                f"z_traffic={row.get('z_traffic',0):.2f}, "
                f"z_packet={row.get('z_packet',0):.2f}. "
                f"Multiple metrics deviate from per-device baseline.")

    # ══════════════════════════════════════════════════════════════════
    # SEVERITY
    # ══════════════════════════════════════════════════════════════════

    def _severity(self, row) -> str:
        if not row['is_anomaly']:
            return 'none'
        t = row['anomaly_type']
        if t in ('rogue_device', 'mac_spoof'):
            return 'critical'
        if t in ('device_offline', 'link_flap'):
            return 'high'
        z = max(abs(row.get('z_traffic', 0)), abs(row.get('z_packet', 0)))
        s = abs(row.get('anomaly_score', 0))
        if z > 6 or s > 0.15:
            return 'high'
        if z > 3.5 or s > 0.08:
            return 'medium'
        return 'low'

    # ══════════════════════════════════════════════════════════════════
    # CONFIDENCE — 0 to 100 integer
    # ══════════════════════════════════════════════════════════════════

    def _confidence_pct(self, row) -> int:
        """
        0–100 confidence score.
        Rule-based detections start at 95.
        ML/stat detections scored from z-score + anomaly_score.
        """
        if not row['is_anomaly']:
            return 0

        dm = row.get('detection_method', 'ml')
        t  = row['anomaly_type']

        # Rule-based: very high confidence
        if dm == 'rule':
            if t in ('rogue_device', 'mac_spoof'):
                return 98
            if t == 'device_offline':
                return 95
            return 90

        # Stat/ML: combine z-score magnitude and IF score
        z     = max(abs(row.get('z_traffic', 0)), abs(row.get('z_packet', 0)))
        score = abs(row.get('anomaly_score', 0))

        # Normalise: z=3.5 → ~50%, z=7 → ~85%; score adds up to 15 pts
        z_component     = min(z / 10.0, 1.0) * 85      # 0–85
        score_component = min(score / 0.2, 1.0) * 15   # 0–15
        combined        = int(z_component + score_component)

        # Floor by severity
        floors = {'high': 60, 'medium': 40, 'low': 20, 'none': 0}
        floor  = floors.get(row.get('severity', 'low'), 20)

        return max(min(combined, 99), floor)

    # ══════════════════════════════════════════════════════════════════
    # SUMMARY REPORT
    # ══════════════════════════════════════════════════════════════════

    def summary(self, results: pd.DataFrame) -> dict:
        anomalies = results[results['is_anomaly']]
        return {
            'total_devices':    len(results),
            'anomaly_count':    len(anomalies),
            'normal_count':     len(results) - len(anomalies),
            'anomaly_types':    anomalies['anomaly_type'].value_counts().to_dict(),
            'severity_counts':  anomalies['severity'].value_counts().to_dict(),
            'detection_methods':anomalies['detection_method'].value_counts().to_dict(),
            'avg_confidence':   round(anomalies['confidence'].mean(), 1) if not anomalies.empty else 0,
            'baseline':         self.baseline_stats,
        }