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


# ── Config ─────────────────────────────────────────
ANOMALY_CHOICES = ["spike", "mac", "ap_offline", "device_offline", "rogue", "flap", "ddos"]
ANOMALY_WEIGHTS = [15, 10, 10, 10, 5, 5, 8]


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
# 🔥 CORE SIMULATION ENGINE (USED BY API)
# ════════════════════════════════════════════════════════
def run_simulation():
    # reset CSV
    if os.path.exists(DATA_FILE):
        open(DATA_FILE, "w").close()

    devices = generate_devices(15)
    G, connections = create_topology(devices)
    export_topology(G)

    register_approved_macs(devices)

    detector = AnomalyDetector(contamination=0.1)

    # baseline
    baseline_frames = []
    for _ in range(8):
        df = generate_telemetry(devices, connections)
        baseline_frames.append(df)
        time.sleep(0.2)

    baseline_df = pd.concat(baseline_frames, ignore_index=True)
    detector.train(baseline_df)

    next_anomaly_time = time.time() + random.randint(45, 60)

    tick = 0
    anomaly_count = 0
    last_anomaly = "none"

    while True:
        tick += 1

        apply_flap_state(tick)
        apply_active_attacks(devices)

        # roaming
        if random.random() < 0.05:
            dev = random.choice(devices)
            new_ap = random.choice(["ap_1", "ap_2", "ap_3"])
            connections[dev["device_id"]] = new_ap

        df = generate_telemetry(devices, connections)

        results = detector.predict(df)

        write_status(tick, last_anomaly, anomaly_count, len(devices))

        # anomaly injection
        if time.time() >= next_anomaly_time:
            choice = random.choices(ANOMALY_CHOICES, weights=ANOMALY_WEIGHTS)[0]

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
            next_anomaly_time = time.time() + random.randint(45, 60)

        yield df   # KEY FOR API

        time.sleep(1.2)


# ════════════════════════════════════════════════════════
# LOCAL RUN (CLI)
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("[INFO] Starting simulation locally...\n")

    try:
        for df in run_simulation():
            print(df.tail(1))

    except KeyboardInterrupt:
        print("\nSimulation stopped cleanly.")