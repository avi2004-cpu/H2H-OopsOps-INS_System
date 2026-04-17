import random

# Expanded device types (more realistic IoT mix)
DEVICE_TYPES = ["sensor", "camera", "thermostat", "smart_light", "phone"]

def generate_mac(index):
    """Generate a pseudo MAC address"""
    return f"AA:BB:CC:{index:02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}"


def generate_devices(n=15):
    """
    Generate a list of simulated IoT devices
    """
    devices = []

    for i in range(n):
        device_type = random.choice(DEVICE_TYPES)

        device = {
            "device_id": f"device_{i}",
            "mac": generate_mac(i),
            "type": device_type,
            "status": "active",

            #  Optional realism fields (useful later)
            "base_traffic": get_base_traffic(device_type),
            "base_signal": random.randint(60, 100)
        }

        devices.append(device)

    return devices


def get_base_traffic(device_type):
    """
    Assign realistic traffic patterns per device type
    """
    if device_type == "camera":
        return random.randint(40, 80)   # high traffic
    elif device_type == "sensor":
        return random.randint(5, 20)    # low traffic
    elif device_type == "thermostat":
        return random.randint(10, 25)
    elif device_type == "smart_light":
        return random.randint(5, 15)
    elif device_type == "phone":
        return random.randint(20, 50)
    else:
        return random.randint(10, 30)


def reset_device(device):
    """
    Reset device to normal state after anomaly
    """
    device["status"] = "active"

    # Remove anomaly overrides if present
    device.pop("traffic_override", None)
    device.pop("signal_override", None)


def print_devices(devices):
    """
    Debug function to display devices
    """
    print("\n--- Device List ---")
    for d in devices:
        print(f"{d['device_id']} | {d['type']} | {d['mac']} | {d['status']}")
