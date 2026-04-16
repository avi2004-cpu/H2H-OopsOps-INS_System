from network_simulation.simulation.devices import generate_devices
from network_simulation.simulation.topology import create_topology
from network_simulation.simulation.telemetry import generate_telemetry
from network_simulation.simulation.anomalies import traffic_spike, rogue_device, device_offline
import time
import random

devices = generate_devices(10)
topology, connections = create_topology(devices)

counter = 0

while True:
    generate_telemetry(devices, connections)

    # Inject anomaly every 10 cycles
    if counter % 10 == 0:
        choice = random.choice(["spike", "rogue", "offline"])

        if choice == "spike":
            traffic_spike(devices)
        elif choice == "rogue":
            rogue_device(devices, connections)
        elif choice == "offline":
            device_offline(devices)

    counter += 1
    time.sleep(2)
