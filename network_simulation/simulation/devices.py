import random

device_types = ["sensor", "camera", "phone"]

def generate_devices(n=10):
    devices = []
    for i in range(n):
        devices.append({
            "device_id": f"device_{i}",
            "mac": f"AA:BB:CC:{i:02}",
            "type": random.choice(device_types),
            "status": "active"
        })
    return devices
