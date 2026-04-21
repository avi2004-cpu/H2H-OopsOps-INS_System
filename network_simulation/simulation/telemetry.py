import random
import time
import pandas as pd
import os

from anomalies import APPROVED_MACS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILE     = os.path.join(DATA_DIR, "network_data.csv")

# Real SNMP OID for interface input octets (IF-MIB)
SNMP_OID_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10"

COLUMNS = [
    "timestamp", "device_id", "mac", "type", "connected_to",
    "traffic", "packet_rate", "signal", "status",
    "mac_changed",   # 1 if MAC differs from approved baseline
    "flap_count",    # number of times device has flapped this session
    "snmp_oid",      # simulated SNMP OID label
    "snmp_value",    # simulated OID value (in octets)
    "syslog_msg",    # simulated syslog entry
]


def _syslog(device_id, status, traffic, mac_changed):
    """Generate a realistic syslog-format message."""
    ts   = time.strftime("%b %d %H:%M:%S")
    host = device_id.replace("_", "-")
    if mac_changed:
        return f"{ts} {host} kernel: [WARN] MAC address change detected"
    if status == "offline":
        return f"{ts} {host} networkd: [ERR] Interface eth0 link down"
    if traffic > 200:
        return f"{ts} {host} iotd: [WARN] Unusually high traffic {traffic} pkts/s"
    return f"{ts} {host} iotd: [INFO] Device reporting normally"


def generate_telemetry(devices, connections):
    data = []

    for d in devices:
        base_traffic = d.get("base_traffic", random.randint(10, 50))
        traffic      = d.get("traffic_override", base_traffic + random.randint(-5, 10))
        signal       = d.get("signal_override",  random.randint(60, 100))
        packet_rate  = d.get("packet_override",  random.randint(20, 100))
        status       = d.get("status", "active")

        # MAC change detection — compares live MAC against approved whitelist
        mac_changed  = 0 if d["mac"] in APPROVED_MACS else 1

        # Flap count — incremented externally by apply_flap_state()
        flap_count   = d.get("flap_count", 0)

        # Simulated SNMP value
        snmp_value   = max(1, traffic) * 1024   # bytes approximation

        row = {
            "timestamp":    int(time.time()),
            "device_id":    d["device_id"],
            "mac":          d["mac"],
            "type":         d.get("type", "unknown"),
            "connected_to": connections.get(d["device_id"], "unknown"),
            "traffic":      max(1, traffic),
            "packet_rate":  packet_rate,
            "signal":       signal,
            "status":       status,
            "mac_changed":  mac_changed,
            "flap_count":   flap_count,
            "snmp_oid":     SNMP_OID_IN_OCTETS,
            "snmp_value":   snmp_value,
            "syslog_msg":   _syslog(d["device_id"], status, traffic, mac_changed),
        }
        data.append(row)

        print(
            f"{d['device_id']} → traffic:{row['traffic']} "
            f"pkts:{packet_rate} sig:{signal} "
            f"status:{status} mac_chg:{mac_changed} flap:{flap_count}"
        )

    return df

