import random

def traffic_spike(devices):
    device = random.choice(devices)
    device["traffic_override"] = 500
    device["signal_override"] = 95
    print(f"[ANOMALY] Traffic spike on {device['device_id']}")

def rogue_device(devices, connections):
    new_device = {
        "device_id": "rogue_1",
        "mac": "ZZ:YY:XX:99",
        "type": "unknown",
        "status": "active"
    }
    devices.append(new_device)
    connections[new_device["device_id"]] = "ap_1"
    print("[ANOMALY] Rogue device added")

def device_offline(devices):
    device = random.choice(devices)
    device["status"] = "offline"
    print(f"[ANOMALY] {device['device_id']} went offline")
