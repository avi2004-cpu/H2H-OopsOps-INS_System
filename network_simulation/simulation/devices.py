import random

DEVICE_TYPES = ["sensor", "camera", "thermostat", "smart_light", "phone"]


def generate_mac(index):
    """Generate a deterministic-prefix MAC so we can build a whitelist."""
    return f"AA:BB:CC:{index:02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}"


def get_base_traffic(device_type):
    return {
        "camera":      random.randint(40, 80),
        "sensor":      random.randint(5, 20),
        "thermostat":  random.randint(10, 25),
        "smart_light": random.randint(5, 15),
        "phone":       random.randint(20, 50),
    }.get(device_type, random.randint(10, 30))


def generate_devices(n=15):
    devices = []

    for i in range(n):
        device_type = random.choice(DEVICE_TYPES)
        mac = generate_mac(i)

        base_traffic = get_base_traffic(device_type)
        base_signal  = random.randint(60, 100)

        device = {
            "device_id":    f"device_{i}",
            "mac":          mac,
            "original_mac": mac,
            "type":         device_type,
            "status":       "active",

            # Base characteristics
            "base_traffic": base_traffic,
            "base_signal":  base_signal,

            # Existing
            "flap_count":   0,

            # NEW STATE (VERY IMPORTANT)
            "last_traffic": base_traffic,
            "last_signal":  base_signal,

            # OPTIONAL (future anomaly evolution)
            "attack_stage": 0,
        }

        devices.append(device)

    return devices


def reset_device(device):
    """Restore device to normal state after anomaly."""
    device["status"] = "active"

    device.pop("traffic_override", None)
    device.pop("signal_override", None)
    device.pop("packet_override", None)

    # Reset state safely
    device["last_traffic"] = device.get("base_traffic", 20)
    device["last_signal"]  = device.get("base_signal", 80)

    device["attack_stage"] = 0


def print_devices(devices):
    print("\n--- Device List ---")
    for d in devices:
        print(
            f"{d['device_id']} | {d['type']} | "
            f"{d['mac']} | {d['status']} | "
            f"T:{d.get('last_traffic')} S:{d.get('last_signal')}"
        )