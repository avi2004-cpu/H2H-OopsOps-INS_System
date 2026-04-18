# ml_model/test_run.py
from data_loader import load_data, get_latest_snapshot
from model import AnomalyDetector

df = load_data()
latest = get_latest_snapshot(df)

detector = AnomalyDetector(contamination=0.1)
detector.train(df)

results = detector.predict(latest)

print("\n=== ANOMALY DETECTION RESULTS ===")
anomalies = results[results['is_anomaly']]
print(f"Anomalies detected: {len(anomalies)} / {len(results)} devices\n")
for _, row in anomalies.iterrows():
    print(f"  ⚠️  [{row['anomaly_type'].upper()}] {row['explanation']}")

print("\n=== ALL DEVICES ===")
print(results[['device_id', 'traffic', 'signal',
               'status', 'is_anomaly', 'anomaly_type']].to_string())