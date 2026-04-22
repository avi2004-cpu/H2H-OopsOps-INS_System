import random
from network_simulation.simulation.anomalies import APPROVED_MACS


# ARP Simulation 
def simulate_arp(devices, connections):
    """
    Simulate ARP table: MAC → device → connection.
    Also flags MACs not in the approved whitelist (rogue / spoof detection).
    """
    arp_table = {}

    for d in devices:
        mac = d["mac"]
        is_rogue = mac not in APPROVED_MACS

        arp_table[mac] = {
            "device_id":    d["device_id"],
            "connected_to": connections.get(d["device_id"], "unknown"),
            "is_rogue_mac": is_rogue,
        }

        if is_rogue:
            print(f"[ARP ALERT] Unknown MAC {mac} on {d['device_id']} — "
                  f"not in approved list!")

    return arp_table


#LLDP Simulation 
def simulate_lldp(connections):
    """
    Simulate LLDP neighbor discovery.
    Returns list of {device, neighbor} pairs as a switch would report.
    """
    neighbors = []
    for device, parent in connections.items():
        neighbors.append({
            "device":       device,
            "neighbor":     parent,
            "port_id":      f"eth{random.randint(0, 3)}",
            "ttl":          120,
        })
    return neighbors


#  Simulated SNMP Walk 
# Real OIDs from IF-MIB (RFC 2863) — used here as labels for realism
SNMP_OIDS = {
    "ifInOctets":    "1.3.6.1.2.1.2.2.1.10",
    "ifOutOctets":   "1.3.6.1.2.1.2.2.1.16",
    "ifInErrors":    "1.3.6.1.2.1.2.2.1.14",
    "ifOperStatus":  "1.3.6.1.2.1.2.2.1.8",   # 1=up, 2=down
}


def simulate_snmp_walk(devices, connections):
    """
    Simulate an SNMP walk returning OID → value per device.
    Mirrors what pysnmp would return from a real switch.
    """
    results = []
    for d in devices:
        status_val = 1 if d.get("status", "active") == "active" else 2
        traffic    = d.get("traffic_override", d.get("base_traffic", 20))

        results.append({
            "device_id":   d["device_id"],
            "connected_to": connections.get(d["device_id"], "unknown"),
            "oids": {
                SNMP_OIDS["ifInOctets"]:   traffic * 1024,
                SNMP_OIDS["ifOutOctets"]:  int(traffic * 0.6 * 1024),
                SNMP_OIDS["ifInErrors"]:   random.randint(0, 5),
                SNMP_OIDS["ifOperStatus"]: status_val,
            }
        })
    return results
