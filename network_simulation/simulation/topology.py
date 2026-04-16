import networkx as nx

def create_topology(devices):
    G = nx.Graph()
    connections = {}

    # Core nodes
    G.add_node("switch_1")
    G.add_node("ap_1")
    G.add_node("ap_2")

    # Connections
    G.add_edge("switch_1", "ap_1")
    G.add_edge("switch_1", "ap_2")

    for d in devices:
        ap = "ap_1" if int(d["device_id"].split("_")[1]) % 2 == 0 else "ap_2"
        G.add_edge(d["device_id"], ap)
        connections[d["device_id"]] = ap

    return G, connections
