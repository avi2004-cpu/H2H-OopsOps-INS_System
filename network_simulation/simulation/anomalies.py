import random


# 6A: Traffic Flood Attack
def traffic_spike(devices):
    device = random.choice(devices)

    device["traffic_override"] = 800
    device["packet_override"] = 300   # affects packet_rate too
    device["signal_override"] = 95

    print(f"[ANOMALY] Traffic spike on {device['device_id']}")


# 6B: MAC Spoofing Attack
def mac_spoof(devices):
    device = random.choice(devices)

    # Store original MAC (optional for debugging)
    device["original_mac"] = device["mac"]

    device["mac"] = "FA:KE:MA:C0:00"

    print(f"[ANOMALY] MAC spoofing on {device['device_id']}")


# 6C: Device / AP Offline
def device_offline(devices):
    device = random.choice(devices)

    device["status"] = "offline"

    # Optional: simulate drop in traffic
    device["traffic_override"] = 0
    device["packet_override"] = 0
    device["signal_override"] = 0

    print(f"[ANOMALY] {device['device_id']} went offline")


# EXTRA (Already good): Rogue Device Injection
def rogue_device(devices, connections):
    new_device = {
        "device_id": f"rogue_{random.randint(1,100)}",
        "mac": "ZZ:YY:XX:99",
        "type": "unknown",
        "status": "active"
    }

    devices.append(new_device)

    # Attach rogue to random AP
    ap = random.choice(["ap_1", "ap_2", "ap_3"])
    connections[new_device["device_id"]] = ap

    print(f"[ANOMALY] Rogue device added → connected to {ap}")
