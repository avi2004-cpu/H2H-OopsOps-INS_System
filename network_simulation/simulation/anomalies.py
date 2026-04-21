import random
import time

# Shared state
# Populated by main.py after devices are generated.
# Used by rogue detection to know which MACs are "approved".
APPROVED_MACS: set = set()

# Tracks devices currently in a flap cycle {device_id: remaining_flap_ticks}
_flap_state: dict = {}


def register_approved_macs(devices):
    """Call once at startup with the clean device list."""
    APPROVED_MACS.clear()
    APPROVED_MACS.update(d["mac"] for d in devices)


# Anomaly 1: Traffic Flood 
def traffic_spike(devices):
    device = random.choice(devices)
    device["traffic_override"] = random.randint(600, 900)
    device["packet_override"]  = random.randint(250, 350)
    device["signal_override"]  = 95
    print(f"[ANOMALY] Traffic spike injected on {device['device_id']}")
    return device["device_id"]


# Anomaly 2: MAC Spoofing 
def mac_spoof(devices):
    """
    Changes a device MAC to one NOT in APPROVED_MACS so the
    whitelist-based detector can catch it.
    """
    device = random.choice(devices)
    device["original_mac"] = device["mac"]
    # Generate a clearly foreign MAC
    fake_mac = "FA:KE:{:02X}:{:02X}:{:02X}:{:02X}".format(
        random.randint(0, 255), random.randint(0, 255),
        random.randint(0, 255), random.randint(0, 255)
    )
    device["mac"] = fake_mac
    print(f"[ANOMALY] MAC spoof on {device['device_id']} → {fake_mac}")
    return device["device_id"]


# Anomaly 3: AP Offline (takes down all connected devices)
def ap_offline(devices, connections):
    """
    Takes a whole AP offline — every device on that AP goes offline
    simultaneously, simulating a real AP failure.
    """
    ap = random.choice(["ap_1", "ap_2", "ap_3"])
    affected = [d for d in devices if connections.get(d["device_id"]) == ap]

    for device in affected:
        device["status"]           = "offline"
        device["traffic_override"] = 0
        device["packet_override"]  = 0
        device["signal_override"]  = 0

    print(f"[ANOMALY] AP offline: {ap} — {len(affected)} devices went down: "
          f"{[d['device_id'] for d in affected]}")
    return ap


# Anomaly 4: Single Device Offline
def device_offline(devices):
    device = random.choice(devices)
    device["status"]           = "offline"
    device["traffic_override"] = 0
    device["packet_override"]  = 0
    device["signal_override"]  = 0
    print(f"[ANOMALY] Device offline: {device['device_id']}")
    return device["device_id"]


# Anomaly 5: Rogue Device Injection
def rogue_device(devices, connections):
    """
    Injects a device with a MAC that is NOT in APPROVED_MACS.
    Detection relies on the MAC whitelist, not the device_id name.
    """
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
    }
    devices.append(new_device)
    ap = random.choice(["ap_1", "ap_2", "ap_3"])
    connections[new_device["device_id"]] = ap
    print(f"[ANOMALY] Rogue device {new_device['device_id']} "
          f"(MAC {rogue_mac}) joined {ap}")
    return new_device["device_id"]


# Anomaly 6: Link Flapping
def start_link_flap(devices):
    """
    Marks a random device to flap online/offline for the next N ticks.
    Call apply_flap_state() every telemetry cycle to apply the effect.
    """
    device = random.choice(devices)
    _flap_state[device["device_id"]] = {"device": device, "ticks": 8}
    print(f"[ANOMALY] Link flapping started on {device['device_id']}")
    return device["device_id"]


def apply_flap_state(tick_counter):
    """
    Call this every tick. Alternates status of flapping devices.
    Returns True if any device is still flapping.
    """
    done = []
    for dev_id, state in _flap_state.items():
        device = state["device"]
        remaining = state["ticks"]

        if remaining <= 0:
            device["status"] = "active"   # restore on exit
            done.append(dev_id)
            print(f"[FLAP END] {dev_id} stabilised")
        else:
            # Alternate every tick
            device["status"] = "offline" if (tick_counter % 2 == 0) else "active"
            device["traffic_override"] = 0 if device["status"] == "offline" else None
            if device["traffic_override"] is None:
                device.pop("traffic_override", None)
            _flap_state[dev_id]["ticks"] -= 1

    for dev_id in done:
        del _flap_state[dev_id]

    return len(_flap_state) > 0
