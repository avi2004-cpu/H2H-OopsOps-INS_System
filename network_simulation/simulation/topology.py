import networkx as nx
import random
import json
import os
from networkx.readwrite import json_graph


def create_topology(devices):
    """
    Create a campus-like network topology:
    - 2 switches
    - 3 access points
    - IoT devices connected to APs
    """

    G = nx.Graph()
    connections = {}

    # Add core network devices
    switches = ["switch_1", "switch_2"]
    access_points = ["ap_1", "ap_2", "ap_3"]

    # Add switches
    for sw in switches:
        G.add_node(sw, type="switch")

    # Add APs
    for ap in access_points:
        G.add_node(ap, type="access_point")

    # Connect switches together
    G.add_edge("switch_1", "switch_2")

    # Connect APs to switches
    G.add_edge("switch_1", "ap_1")
    G.add_edge("switch_1", "ap_2")
    G.add_edge("switch_2", "ap_3")

    # Connect devices to APs (balanced/random)
    for d in devices:
        ap = random.choice(access_points)
        G.add_node(d["device_id"], type=d["type"])
        G.add_edge(d["device_id"], ap)

        connections[d["device_id"]] = ap

    return G, connections


def export_topology(G):
    """
    Export graph to JSON for frontend visualization
    """

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(BASE_DIR, "data", "topology.json")

    data = json_graph.node_link_data(G)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[INFO] Topology exported to {file_path}")


def print_topology(G):
    """
    Debug function to print connections
    """
    print("\n--- Network Topology ---")
    for edge in G.edges():
        print(f"{edge[0]} ↔ {edge[1]}")
