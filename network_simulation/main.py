import os
import sys
import json
import time
import random

import pandas as pd

# Path setup (portable — no hardcoded user paths) 
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from network_simulation.simulation.devices   import generate_devices
from network_simulation.simulation.topology  import create_topology, export_topology
from network_simulation.simulation.telemetry import generate_telemetry
from network_simulation.simulation.anomalies import (
    register_approved_macs,
    traffic_spike,
    mac_spoof,
    ap_offline,
    device_offline,
    rogue_device,
    start_link_flap,
    apply_flap_state,
)
from network_simulation.simulation.discovery import (
    simulate_arp,
    simulate_lldp,
    simulate_snmp_walk,
)
from ml_model.model import AnomalyDetector

STATUS_FILE = os.path.join(ROOT, "network_simulation", "data", "sim_status.json")


def write_status(tick, last_anomaly, anomaly_count, device_count):
    """Write a live status file so the dashboard knows the sim is running."""
    payload = {
        "tick":          tick,
        "timestamp":     int(time.time()),
        "last_anomaly":  last_anomaly,
        "anomaly_count": anomaly_count,
        "device_count":  device_count,
        "alive":         True,
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(payload, f, indent=2)


# SETUP
devices = generate_devices(15)
G, connections = create_topology(devices)
export_topology(G)

# Register all startup MACs as approved — MUST happen before telemetry starts
register_approved_macs(devices)

detector = AnomalyDetector(contamination=0.1)

print("\n🚀 Real-Time Network Simulation + ML Running...\n")

#Step 1: Collect baseline (normal traffic only) 
print("Collecting baseline data (10 cycles)...")
baseline_frames = []
for _ in range(10):
    df = generate_telemetry(devices, connections)
    baseline_frames.append(df)
    time.sleep(0.2)

baseline_df = pd.concat(baseline_frames, ignore_index=True)
detector.train(baseline_df)
print("Model trained ✓\n")

#Step 2: Real-time loop
next_anomaly_time = time.time() + random.randint(5, 10)
tick          = 0
anomaly_count = 0
last_anomaly  = "none"

    print(" \nSimulation stopped cleanly.")
ANOMALY_CHOICES = ["spike", "mac", "ap_offline", "device_offline", "rogue", "flap"]

except KeyboardInterrupt:
ANOMALY_WEIGHTS = [25,      20,    15,            15,               15,      10]

        time.sleep(1)
try:
    while True:
        tick += 1


        # Apply any active link-flap cycles
        apply_flap_state(tick)

        # Telemetry 
        df = generate_telemetry(devices, connections)

        # ML Detection
        write_status(tick, last_anomaly, anomaly_count, len(devices))
        results   = detector.predict(df)
        anomalies = results[results["is_anomaly"]]
                print(
        # Status file for dashboard
                    f"🚨 [ML ALERT] [{row['severity'].upper()}] "

            next_anomaly_time = time.time() + random.randint(5, 10)

            anomaly_count += 1
            elif choice == "ap_offline":
                ap = ap_offline(devices, connections)
                last_anomaly = f"ap_offline: {ap}"
                last_anomaly = f"link_flap on {dev}"

                dev = start_link_flap(devices)
            elif choice == "device_offline":
                last_anomaly = f"device_offline: {device_offline(devices)}"
            elif choice == "flap":

            elif choice == "rogue":
                dev = rogue_device(devices, connections)
                last_anomaly = f"rogue_device: {dev}"

                    f"{row['anomaly_type']} on {row['device_id']} "
                )

                last_anomaly = f"mac_spoof on {mac_spoof(devices)}"

        # Discovery (ARP + LLDP + SNMP) 
        arp  = simulate_arp(devices, connections)

            elif choice == "mac":
        lldp = simulate_lldp(connections)
        snmp = simulate_snmp_walk(devices, connections)

        if tick % 5 == 0:   # print sample every 5 ticks to reduce noise
                last_anomaly = f"traffic_spike on {traffic_spike(devices)}"
            if choice == "spike":
            print(f"\n[DISCOVERY tick={tick}]")

            print("ARP  sample:", list(arp.items())[:2])
            print("LLDP sample:", lldp[:2])
            print("SNMP sample:", [
            print(f"\n⚠️  [INJECT] {choice.upper()}")
                {s["device_id"]: list(s["oids"].items())[:2]} for s in snmp[:2]
            ])
            choice = random.choices(ANOMALY_CHOICES, weights=ANOMALY_WEIGHTS)[0]

        # Anomaly Injection 
        if time.time() >= next_anomaly_time:
                    f"→ {row['explanation']}"

