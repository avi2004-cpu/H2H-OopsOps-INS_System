from network_simulation.simulation.devices import generate_devices
from network_simulation.simulation.topology import create_topology, export_topology
from network_simulation.simulation.telemetry import generate_telemetry
from network_simulation.simulation.anomalies import (
    traffic_spike,
    rogue_device,
    device_offline,
    mac_spoof
)
from network_simulation.simulation.discovery import simulate_arp, simulate_lldp

from ml_model.model import AnomalyDetector

import pandas as pd
import time
import random

# Setup
devices = generate_devices(15)
G, connections = create_topology(devices)

export_topology(G)

# Initialize ML model
detector = AnomalyDetector(contamination=0.1)

print("\nReal-Time Network Simulation + ML Running...\n")

# =========================================
# STEP 1: TRAIN MODEL (BASELINE DATA)
# =========================================

print("[INFO] Collecting baseline data...")

baseline_data = []

for _ in range(10):   # collect normal cycles
    df = generate_telemetry(devices, connections)
    baseline_data.append(df)

baseline_df = pd.concat(baseline_data, ignore_index=True)

detector.train(baseline_df)

print("[INFO] Model trained successfully!\n")

# Random anomaly timer
next_anomaly_time = time.time() + random.randint(5, 10)

# =========================================
# STEP 2: REAL-TIME LOOP
# =========================================

try:
    while True:
        # Generate telemetry
        df = generate_telemetry(devices, connections)

        # =========================================
        # ML DETECTION
        # =========================================
        results = detector.predict(df)

        anomalies = results[results['is_anomaly'] == True]

        for _, row in anomalies.iterrows():
            print(
                f"🚨 [ML ALERT] {row['anomaly_type']} on {row['device_id']} → {row['explanation']}"
            )

        # Optional debug summary
        print("\n[SUMMARY]")
        print(results[['device_id', 'anomaly_type', 'is_anomaly']].head())

        # =========================================
        # TOPOLOGY DISCOVERY
        # =========================================
        arp = simulate_arp(devices, connections)
        lldp = simulate_lldp(connections)

        print("\n[DISCOVERY SAMPLE]")
        print("ARP:", list(arp.items())[:2])
        print("LLDP:", lldp[:2])

        # =========================================
        # RANDOM ANOMALY INJECTION
        # =========================================
        current_time = time.time()

        if current_time >= next_anomaly_time:
            anomaly = random.choices(
                ["spike", "rogue", "offline", "mac"],
                weights=[30, 20, 25, 25]
            )[0]

            print("\n⚠️ Injecting anomaly...")

            if anomaly == "spike":
                traffic_spike(devices)

            elif anomaly == "rogue":
                rogue_device(devices, connections)

            elif anomaly == "offline":
                device_offline(devices)

            elif anomaly == "mac":
                mac_spoof(devices)

            next_anomaly_time = current_time + random.randint(5, 10)

        time.sleep(1)

except KeyboardInterrupt:
    print("\nSimulation stopped.")
