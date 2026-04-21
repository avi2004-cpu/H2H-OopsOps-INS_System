import random

DEVICE_TYPES = ["sensor", "camera", "thermostat", "smart_light", "phone"]


def generate_mac(index):
    """Generate a deterministic-prefix MAC so we can build a whitelist."""
    return f"AA:BB:CC:{index:02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}"


def generate_devices(n=15):
    devices = []
    for i in range(n):
        device_type = random.choice(DEVICE_TYPES)
        mac = generate_mac(i)
        device = {
            "device_id":    f"device_{i}",
            "mac":          mac,
            "original_mac": mac,          # kept for MAC-change detection
            "type":         device_type,
            "status":       "active",
            "base_traffic": get_base_traffic(device_type),
            "base_signal":  random.randint(60, 100),
            "flap_count":   0,            # incremented by apply_flap_state
        }
        devices.append(device)
    return devices


def get_base_traffic(device_type):
    return {
        "camera":      random.randint(40, 80),
        "sensor":      random.randint(5, 20),
        "thermostat":  random.randint(10, 25),
        "smart_light": random.randint(5, 15),
        "phone":       random.randint(20, 50),
    }.get(device_type, random.randint(10, 30))


def reset_device(device):
    device["status"] = "active"
    device.pop("traffic_override", None)
    device.pop("signal_override", None)
    device.pop("packet_override", None)


def print_devices(devices):
    print("\n--- Device List ---")
    for d in devices:
        print(f"{d['device_id']} | {d['type']} | {d['mac']} | {d['status']}")
