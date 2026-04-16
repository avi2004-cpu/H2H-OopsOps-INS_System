import random
import time
import pandas as pd
import os

#  Get absolute path to project (network_simulation folder)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

#  Construct path to CSV file safely
DATA_DIR = os.path.join(BASE_DIR, "data")
FILE = os.path.join(DATA_DIR, "network_data.csv")


def generate_telemetry(devices, connections):
    data = []

    for d in devices:
        #  Apply anomaly overrides if present
        traffic = d.get("traffic_override", random.randint(10, 50))
        signal = d.get("signal_override", random.randint(60, 100))

        row = {
            "timestamp": int(time.time()),
            "device_id": d["device_id"],
            "mac": d["mac"],
            "type": d["type"],
            "connected_to": connections.get(d["device_id"], "unknown"),
            "traffic": traffic,
            "signal": signal,
            "status": d.get("status", "active")
        }

        data.append(row)

        # Debug (optional)
        print(f"{d['device_id']} → traffic: {traffic}, signal: {signal}, status: {row['status']}")

        # Reset anomaly after one cycle
        if "traffic_override" in d:
            del d["traffic_override"]
        if "signal_override" in d:
            del d["signal_override"]

    df = pd.DataFrame(data)

    #  Ensure data folder exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    #  Write CSV safely
    if not os.path.exists(FILE):
        df.to_csv(FILE, index=False)
    else:
        df.to_csv(FILE, mode='a', header=False, index=False)
