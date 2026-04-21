import networkx as nx
import random
import json
import os
from networkx.readwrite import json_graph


def create_topology(devices):
    """
    Campus-like topology:
      switch_1 ── switch_2
      switch_1 ── ap_1, ap_2
      switch_2 ── ap_3
      ap_*     ── IoT devices (random assignment)
    """
    G = nx.Graph()
    connections = {}

    switches      = ["switch_1", "switch_2"]
    access_points = ["ap_1", "ap_2", "ap_3"]

    for sw in switches:
        G.add_node(sw, type="switch")
    for ap in access_points:
        G.add_node(ap, type="access_point")

    G.add_edge("switch_1", "switch_2")
    G.add_edge("switch_1", "ap_1")
    G.add_edge("switch_1", "ap_2")
    G.add_edge("switch_2", "ap_3")

    for d in devices:
        ap = random.choice(access_points)
        G.add_node(d["device_id"], type=d["type"])
        G.add_edge(d["device_id"], ap)
        connections[d["device_id"]] = ap

    return G, connections


def export_topology(G):
    """Export NetworkX graph to JSON for dashboard consumption."""
    BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(BASE_DIR, "data", "topology.json")

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    data = json_graph.node_link_data(G)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[INFO] Topology exported → {file_path}")


def print_topology(G):
    print("\n--- Network Topology ---")
    for edge in G.edges():
        print(f"{edge[0]} ↔ {edge[1]}")
