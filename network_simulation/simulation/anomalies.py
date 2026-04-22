import random
import time

# ─────────────────────────────────────────────
# SHARED STATE
# ─────────────────────────────────────────────

APPROVED_MACS: set = set()

# Link flap state
_flap_state: dict = {}

# NEW: Persistent attack state
_active_attacks: dict = {}


# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

def register_approved_macs(devices):
    """Call once at startup with the clean device list."""
    APPROVED_MACS.clear()
    APPROVED_MACS.update(d["mac"] for d in devices)


# ─────────────────────────────────────────────
# ANOMALY 1: TRAFFIC SPIKE
# ─────────────────────────────────────────────

def traffic_spike(devices):
    device = random.choice(devices)
    device["traffic_override"] = random.randint(600, 900)
    device["packet_override"]  = random.randint(250, 350)
    device["signal_override"]  = 95
    print(f"[ANOMALY] Traffic spike injected on {device['device_id']}")
    return device["device_id"]


# ─────────────────────────────────────────────
# ANOMALY 2: MAC SPOOFING
# ─────────────────────────────────────────────

def mac_spoof(devices):
    device = random.choice(devices)
    device["original_mac"] = device["mac"]

    fake_mac = "FA:KE:{:02X}:{:02X}:{:02X}:{:02X}".format(
        random.randint(0, 255), random.randint(0, 255),
        random.randint(0, 255), random.randint(0, 255)
    )

    device["mac"] = fake_mac
    print(f"[ANOMALY] MAC spoof on {device['device_id']} → {fake_mac}")
    return device["device_id"]


# ─────────────────────────────────────────────
# ANOMALY 3: AP OFFLINE
# ─────────────────────────────────────────────

def ap_offline(devices, connections):
    ap = random.choice(["ap_1", "ap_2", "ap_3"])
    affected = [d for d in devices if connections.get(d["device_id"]) == ap]

    for device in affected:
        device["status"]           = "offline"
        device["traffic_override"] = 0
        device["packet_override"]  = 0
        device["signal_override"]  = 0

    print(f"[ANOMALY] AP offline: {ap} — {len(affected)} devices down")
    return ap


# ─────────────────────────────────────────────
# ANOMALY 4: DEVICE OFFLINE
# ─────────────────────────────────────────────

def device_offline(devices):
    device = random.choice(devices)
    device["status"]           = "offline"
    device["traffic_override"] = 0
    device["packet_override"]  = 0
    device["signal_override"]  = 0

    print(f"[ANOMALY] Device offline: {device['device_id']}")
    return device["device_id"]


# ─────────────────────────────────────────────
# ANOMALY 5: ROGUE DEVICE
# ─────────────────────────────────────────────

def rogue_device(devices, connections):
    rogue_mac = "RG:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(
        random.randint(0, 255), random.randint(0, 255),
        random.randint(0, 255), random.randint(0, 255),
        random.randint(0, 255)
    )

    new_device = {
        "device_id":    f"unknown_{random.randint(100, 999)}",
        "mac":          rogue_mac,
        "type":         "unknown",
        "status":       "active",
        "base_traffic": random.randint(30, 80),
        "base_signal":  random.randint(40, 70),
        "last_traffic": random.randint(30, 80),
        "last_signal":  random.randint(40, 70),
    }

    devices.append(new_device)

    ap = random.choice(["ap_1", "ap_2", "ap_3"])
    connections[new_device["device_id"]] = ap

    print(f"[ANOMALY] Rogue device {new_device['device_id']} joined {ap}")
    return new_device["device_id"]


# ─────────────────────────────────────────────
# ANOMALY 6: LINK FLAP
# ─────────────────────────────────────────────

def start_link_flap(devices):
    device = random.choice(devices)
    _flap_state[device["device_id"]] = {"device": device, "ticks": 8}

    print(f"[ANOMALY] Link flapping started on {device['device_id']}")
    return device["device_id"]


def apply_flap_state(tick_counter):
    done = []

    for dev_id, state in _flap_state.items():
        device = state["device"]
        remaining = state["ticks"]

        if remaining <= 0:
            device["status"] = "active"
            done.append(dev_id)
            print(f"[FLAP END] {dev_id} stabilised")
        else:
            device["status"] = "offline" if (tick_counter % 2 == 0) else "active"

            if device["status"] == "offline":
                device["traffic_override"] = 0
            else:
                device.pop("traffic_override", None)

            _flap_state[dev_id]["ticks"] -= 1

    for dev_id in done:
        del _flap_state[dev_id]

    return len(_flap_state) > 0


# ─────────────────────────────────────────────
# NEW: DDoS ATTACK (PERSISTENT)
# ─────────────────────────────────────────────

def ddos_attack(devices):
    victims = random.sample(devices, min(3, len(devices)))

    for d in victims:
        _active_attacks[d["device_id"]] = {
            "type": "ddos",
            "remaining": 6
        }

    print(f"[ANOMALY] DDoS attack started on {[d['device_id'] for d in victims]}")
    return [d["device_id"] for d in victims]


# ─────────────────────────────────────────────
# APPLY PERSISTENT ATTACKS
# ─────────────────────────────────────────────

def apply_active_attacks(devices):
    finished = []

    for dev_id, attack in _active_attacks.items():
        for d in devices:
            if d["device_id"] == dev_id:

                if attack["type"] == "ddos":
                    d["traffic_override"] = d.get("last_traffic", 50) * 3
                    d["packet_override"] = 200

                attack["remaining"] -= 1

                if attack["remaining"] <= 0:
                    finished.append(dev_id)

    for f in finished:
        print(f"[ATTACK END] {f} recovered")
        del _active_attacks[f]