import random
import time
import pandas as pd
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILE = os.path.join(DATA_DIR, "network_data.csv")


def generate_telemetry(devices, connections):
    data = []

    for d in devices:
        # Base realistic traffic
        base_traffic = d.get("base_traffic", random.randint(10, 50))

        # Apply anomaly overrides if present
        traffic = d.get("traffic_override", base_traffic + random.randint(-5, 10))
        signal = d.get("signal_override", random.randint(60, 100))
        packet_rate = d.get("packet_override", random.randint(20, 100))

        row = {
            "timestamp": int(time.time()),
            "device_id": d["device_id"],
            "mac": d["mac"],
            "type": d["type"],
            "connected_to": connections.get(d["device_id"], "unknown"),
            "traffic": max(1, traffic),  # avoid negative values
            "packet_rate": packet_rate,  # NEW FIELD
            "signal": signal,
            "status": d.get("status", "active")
        }

        data.append(row)

        # Debug output
        print(
            f"{d['device_id']} → traffic: {row['traffic']}, "
            f"packets: {packet_rate}, signal: {signal}, status: {row['status']}"
        )

        # Reset anomaly overrides after one cycle
        d.pop("traffic_override", None)
        d.pop("signal_override", None)
        d.pop("packet_override", None)

    # Define final schema (VERY IMPORTANT)
    columns = [
        "timestamp",
        "device_id",
        "mac",
        "type",
        "connected_to",
        "traffic",
        "packet_rate",
        "signal",
        "status"
    ]

    df = pd.DataFrame(data, columns=columns)

    # Ensure data folder exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Smart header handling
    if not os.path.exists(FILE):
        # Create new file with header
        df.to_csv(FILE, index=False)
    else:
        try:
            existing_df = pd.read_csv(FILE, nrows=0)

            if list(existing_df.columns) != columns:
                print("[INFO] Fixing CSV header...")
                df.to_csv(FILE, index=False)
            else:
                df.to_csv(FILE, mode='a', header=False, index=False)

        except Exception:
            # If file corrupted → recreate
            print("[WARNING] CSV corrupted. Recreating file...")
            df.to_csv(FILE, index=False)
