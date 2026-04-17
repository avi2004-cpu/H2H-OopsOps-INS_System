def simulate_arp(devices, connections):
    """
    Simulate ARP table: MAC → Device → Connection
    """
    arp_table = {}

    for d in devices:
        arp_table[d["mac"]] = {
            "device_id": d["device_id"],
            "connected_to": connections[d["device_id"]]
        }

    return arp_table


def simulate_lldp(connections):
    """
    Simulate LLDP neighbor discovery
    """
    neighbors = []

    for device, parent in connections.items():
        neighbors.append({
            "device": device,
            "neighbor": parent
        })

    return neighbors
