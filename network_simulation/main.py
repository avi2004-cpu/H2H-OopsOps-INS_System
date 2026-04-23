import os
import sys
import json
import time
import random
import pandas as pd

# ── Path setup ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, ROOT)

# Use ONE consistent path
DATA_FILE = os.path.join(ROOT, "network_simulation", "data", "network_data.csv")
STATUS_FILE = os.path.join(ROOT, "network_simulation", "data", "sim_status.json")

# ── Imports ────────────────────────────────────────────────
from network_simulation.simulation.devices import generate_devices
from network_simulation.simulation.topology import create_topology, export_topology
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
    ddos_attack,
    apply_active_attacks
)
from network_simulation.simulation.discovery import (
    simulate_arp,
    simulate_lldp,
    simulate_snmp_walk,
)
from ml_model.model import AnomalyDetector


# ── Anomaly config ─────────────────────────────────────────
ANOMALY_CHOICES = ["spike", "mac", "ap_offline", "device_offline", "rogue", "flap", "ddos"]
ANOMALY_WEIGHTS = [15, 10, 10, 10, 5, 5, 8]   # tuned (less aggressive)


# ── Status writer ──────────────────────────────────────────
def write_status(tick, last_anomaly, anomaly_count, device_count):
    payload = {
        "tick": tick,
        "timestamp": int(time.time()),
        "last_anomaly": last_anomaly,
        "anomaly_count": anomaly_count,
        "device_count": device_count,
        "alive": True,
    }
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(payload, f, indent=2)


# ════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════

# RESET CSV ON EVERY RUN (SAFE)
if os.path.exists(DATA_FILE):
    print("[INFO] Clearing old CSV data...")
    open(DATA_FILE, "w").close()

print("[INFO] New simulation session started\n")

devices = generate_devices(15)
G, connections = create_topology(devices)
export_topology(G)

register_approved_macs(devices)

detector = AnomalyDetector(contamination=0.1)

print("Real-Time Network Simulation + ML Running...\n")


# ════════════════════════════════════════════════════════
# BASELINE TRAINING
# ════════════════════════════════════════════════════════

print("[INFO] Collecting baseline data...")
baseline_frames = []

for _ in range(10):
    df = generate_telemetry(devices, connections)
    baseline_frames.append(df)
    time.sleep(0.2)

baseline_df = pd.concat(baseline_frames, ignore_index=True)
detector.train(baseline_df)

print("[INFO] Model trained ✓\n")


# ════════════════════════════════════════════════════════
# REAL-TIME LOOP
# ════════════════════════════════════════════════════════

next_anomaly_time = time.time() + random.randint(45, 60)

tick = 0
anomaly_count = 0
last_anomaly = "none"

try:
    while True:
        tick += 1

        # ── Apply ongoing states ─────────────────────
        apply_flap_state(tick)
        apply_active_attacks(devices)

        # ── Device roaming (realism) ────────────────
        if random.random() < 0.05:
            dev = random.choice(devices)
            new_ap = random.choice(["ap_1", "ap_2", "ap_3"])
            connections[dev["device_id"]] = new_ap
            print(f"[MOVE] {dev['device_id']} → {new_ap}")

        # ── Telemetry ───────────────────────────────
        df = generate_telemetry(devices, connections)

        # ── ML Detection ────────────────────────────
        results = detector.predict(df)
        anomalies = results[results["is_anomaly"]]

        for _, row in anomalies.iterrows():
            print(
                f"[ML ALERT] [{row['severity'].upper()}] "
                f"{row['anomaly_type']} on {row['device_id']} "
                f"→ {row['explanation']}"
            )

        # ── Dashboard status ────────────────────────
        write_status(tick, last_anomaly, anomaly_count, len(devices))

        # ── Discovery simulation ────────────────────
        arp = simulate_arp(devices, connections)
        lldp = simulate_lldp(connections)
        snmp = simulate_snmp_walk(devices, connections)

        if tick % 5 == 0:
            print(f"\n[DISCOVERY tick={tick}]")
            print("ARP  sample:", list(arp.items())[:2])
            print("LLDP sample:", lldp[:2])
            print("SNMP sample:", [
                {s["device_id"]: list(s["oids"].items())[:2]} for s in snmp[:2]
            ])

        # ── Anomaly injection ───────────────────────
        if time.time() >= next_anomaly_time:
            choice = random.choices(ANOMALY_CHOICES, weights=ANOMALY_WEIGHTS)[0]
            print(f"\n[INJECT] {choice.upper()}")

            if choice == "spike":
                dev = traffic_spike(devices)
                last_anomaly = f"traffic_spike on {dev}"

            elif choice == "mac":
                dev = mac_spoof(devices)
                last_anomaly = f"mac_spoof on {dev}"

            elif choice == "ap_offline":
                ap = ap_offline(devices, connections)
                last_anomaly = f"ap_offline: {ap}"

            elif choice == "device_offline":
                dev = device_offline(devices)
                last_anomaly = f"device_offline: {dev}"

            elif choice == "rogue":
                dev = rogue_device(devices, connections)
                last_anomaly = f"rogue_device: {dev}"

            elif choice == "flap":
                dev = start_link_flap(devices)
                last_anomaly = f"link_flap on {dev}"

            elif choice == "ddos":
                victims = ddos_attack(devices)
                last_anomaly = f"ddos on {victims}"

            anomaly_count += 1

            # slower injection
            next_anomaly_time = time.time() + random.randint(45, 60)

        time.sleep(1.2)   # slightly slower for dashboard readability

except KeyboardInterrupt:
    print("\nSimulation stopped cleanly.")