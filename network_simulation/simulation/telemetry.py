import random
import time
import pandas as pd
import os

from network_simulation.simulation.anomalies import APPROVED_MACS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILE     = os.path.join(DATA_DIR, "network_data.csv")

# Real SNMP OID for interface input octets (IF-MIB)
SNMP_OID_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"

COLUMNS = [
    "timestamp", "device_id", "mac", "type", "connected_to",
    "traffic", "packet_rate", "signal", "status",
    "mac_changed",
    "flap_count",
    "snmp_oid",
    "snmp_value",
    "syslog_msg",
]

# NEW: CSV RESET CONTROL
START_TIME = time.time()
RESET_INTERVAL = 180  # 3 minutes


def _syslog(device_id, status, traffic, mac_changed):
    ts   = time.strftime("%b %d %H:%M:%S")
    host = device_id.replace("_", "-")

    if mac_changed:
        return f"{ts} {host} kernel: [WARN] MAC address change detected"
    if status == "offline":
        return f"{ts} {host} networkd: [ERR] Interface eth0 link down"
    if traffic > 200:
        return f"{ts} {host} iotd: [WARN] High traffic {traffic} pkts/s"

    return f"{ts} {host} iotd: [INFO] Device normal"


def generate_telemetry(devices, connections):
    global START_TIME

    data = []

    for d in devices:
        base_traffic = d.get("base_traffic", random.randint(10, 50))
        status       = d.get("status", "active")

        # STATEFUL TRAFFIC
        last_traffic = d.get("last_traffic", base_traffic)
        traffic = last_traffic + random.randint(-5, 5)

        # TIME-BASED PATTERN
        hour = int(time.time() / 5) % 24
        if 9 <= hour <= 18:
            traffic *= 1.3
        else:
            traffic *= 0.7

        # DEVICE TYPE BEHAVIOR
        if d["type"] == "camera":
            traffic *= 1.2
        elif d["type"] == "sensor":
            traffic *= 0.5
        elif d["type"] == "phone":
            traffic *= 0.9

        # Apply anomaly override
        traffic = d.get("traffic_override", traffic)
        traffic = max(1, int(traffic))

        # STATEFUL SIGNAL
        last_signal = d.get("last_signal", d.get("base_signal", 80))
        signal = last_signal + random.randint(-2, 2)

        # AP LOAD IMPACT
        ap = connections.get(d["device_id"])
        ap_load = sum(1 for v in connections.values() if v == ap)

        if ap_load > 8:
            signal -= 10

        signal = d.get("signal_override", signal)
        signal = max(0, min(100, int(signal)))

        # PACKET RATE
        packet_rate = d.get("packet_override", random.randint(20, 100))

        # SAVE STATE
        d["last_traffic"] = traffic
        d["last_signal"] = signal

        # MAC detection
        mac_changed = 0 if d["mac"] in APPROVED_MACS else 1

        flap_count = d.get("flap_count", 0)

        # SNMP simulation
        snmp_value = traffic * 1024

        row = {
            "timestamp": int(time.time()),
            "device_id": d["device_id"],
            "mac": str(d["mac"]),
            "type": str(d.get("type", "unknown")),
            "connected_to": str(connections.get(d["device_id"], "unknown")),

            # FORCE NUMERIC TYPES
            "traffic": int(traffic),
            "packet_rate": int(packet_rate),
            "signal": int(signal),

            "status": str(status),

            "mac_changed": int(mac_changed),
            "flap_count": int(flap_count),

            "snmp_oid": str(SNMP_OID_IN_OCTETS),
            "snmp_value": int(snmp_value),
            "syslog_msg": str(_syslog(d["device_id"], status, traffic, mac_changed)),
        }

        data.append(row)

        print(
            f"{d['device_id']} → traffic:{traffic} "
            f"pkts:{packet_rate} sig:{signal} "
            f"status:{status} mac_chg:{mac_changed} flap:{flap_count}"
        )

    # CREATE DATAFRAME
    df = pd.DataFrame(data, columns=COLUMNS)

    # Ensure directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    current_time = time.time()

    # RESET CSV EVERY 3 MINUTES (SAFE)
    if current_time - START_TIME > RESET_INTERVAL:
        print("\n[INFO] Resetting CSV file (3 min refresh)...\n")
        df.to_csv(FILE, index=False)
        START_TIME = current_time

    else:
        # SAFE CSV WRITING (HEADER + AUTO FIX)
        if not os.path.exists(FILE):
            df.to_csv(FILE, index=False)
        else:
            try:
                existing = pd.read_csv(FILE, nrows=0)

                if list(existing.columns) != COLUMNS:
                    print("[INFO] Fixing CSV header mismatch...")
                    df.to_csv(FILE, index=False)
                else:
                    df.to_csv(FILE, mode='a', header=False, index=False)

            except Exception:
                print("[WARNING] CSV corrupted. Recreating file...")
                df.to_csv(FILE, index=False)

    return df