from network_simulation.simulation.devices import generate_devices
from network_simulation.simulation.topology import create_topology, export_topology
from network_simulation.simulation.telemetry import generate_telemetry
from network_simulation.simulation.anomalies import (
    traffic_spike,
    rogue_device,
    device_offline,
    mac_spoof
)
from network_simulation.simulation.discovery import simulate_arp, simulate_lldp

import time
import random

# Setup
devices = generate_devices(15)
G, connections = create_topology(devices)

# Export topology (for frontend)
export_topology(G)

print("\n🚀 Real-Time Network Simulation Running...\n")

# Random anomaly timer
next_anomaly_time = time.time() + random.randint(5, 15)

try:
    while True:
        # 1. Generate telemetry (continuous)
        generate_telemetry(devices, connections)

        # 2. Topology Discovery (ARP + LLDP)
        arp = simulate_arp(devices, connections)
        lldp = simulate_lldp(connections)

        # Print small sample (clean output)
        print("\n[DISCOVERY]")
        print("ARP Sample:", list(arp.items())[:2])
        print("LLDP Sample:", lldp[:2])

        # 3. Inject anomalies at random intervals
        current_time = time.time()

        if current_time >= next_anomaly_time:
            anomaly = random.choices(
                ["spike", "rogue", "offline", "mac"],
                weights=[40, 20, 20, 20]
            )[0]

            print("\n Injecting anomaly...")

            if anomaly == "spike":
                traffic_spike(devices)

            elif anomaly == "rogue":
                rogue_device(devices, connections)

            elif anomaly == "offline":
                device_offline(devices)

            elif anomaly == "mac":
                mac_spoof(devices)

            # Schedule next anomaly
            next_anomaly_time = current_time + random.randint(5, 15)

        # Loop delay (real-time feel)
        time.sleep(1)

except KeyboardInterrupt:
    print("\n Simulation stopped safely.")
