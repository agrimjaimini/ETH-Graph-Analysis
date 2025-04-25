from pyvis.network import Network
import networkx as nx
import community as community_louvain
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from fetch_data import get_balances_etherscan

load_dotenv()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")



def visualize_graph(G: nx.Graph, df: pd.DataFrame, rpc_url: str, output_html: str = 'graph.html', min_edge_value: float = 0.25) -> None:
    """
    Render an interactive HTML graph of G using Pyvis.
    Node size is scaled by ETH balance from Etherscan.
    Nodes are colored by Louvain cluster, with anomalies highlighted in red and glowing.
    """
    anomalies = pd.read_csv('data/anomalies.csv')

    # Filter graph edges by value ===
    edges_to_keep = [(u, v) for u, v, d in G.edges(data=True) if d.get('value', 0) >= float(min_edge_value)]
    G_filtered = G.edge_subgraph(edges_to_keep).copy()

    addresses = list(G_filtered.nodes())
    print(f"Fetching {len(addresses)} wallet balances from Etherscan...")
    balances = get_balances_etherscan(addresses, ETHERSCAN_API_KEY)

    # Node Resizing
    values = np.array(list(balances.values()))
    min_size, max_size = 50, 500

    # Apply log scaling
    values = np.log1p(values)  # log(1 + x) to handle zero balances safely

    if values.max() != values.min():
        scaled = ((values - values.min()) / (values.max() - values.min())) * (max_size - min_size) + min_size
    else:
        scaled = np.full_like(values, (min_size + max_size) / 2)

    wallet_sizes = dict(zip(balances.keys(), scaled))

    # Cluster detection 
    partition = community_louvain.best_partition(G_filtered.to_undirected())
    unique_clusters = set(partition.values())

    excluded_color = "#ff5c57"
    color_map = cm.get_cmap('tab20', len(unique_clusters) + 1)
    cluster_colors = {}
    i = 0
    for c in unique_clusters:
        color = mcolors.rgb2hex(color_map(i))
        while color.lower() == excluded_color.lower():
            i += 1
            color = mcolors.rgb2hex(color_map(i))
        cluster_colors[c] = color
        i += 1

    # Build Pyvis network
    net = Network(height='750px', width='100%', directed=True, notebook=True, cdn_resources='in_line')

    for node in G_filtered.nodes():
        match = anomalies[anomalies['node'] == node]
        node_lc = node.lower()
        size = wallet_sizes.get(node_lc, 15)
        balance = balances.get(node_lc, 0)
        title = f"{node}\nBalance: {balance:.4f} ETH"

        if not match.empty and match['anomaly'].values[0] == True:
            net.add_node(
                node,
                label=node[:6],
                title=title,
                color="#ff5c57",
                size=size + 10,
                borderWidth=3,
                shadow=True
            )
        else:
            cluster = partition.get(node, 0)  
            color = cluster_colors.get(cluster, "#cccccc")  
            net.add_node(
                node,
                label=node[:6],
                title=title,
                size=size,
                color=color  
            )

    for u, v, data in G_filtered.edges(data=True):
        value = data.get('value', 0)
        title = f"Value: {value:.2f} ETH\\nCount: {data.get('count', 1)}"
        net.add_edge(u, v, value=value, title=title)

    # Layout Physics
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "stabilization": {
          "iterations": 100,
          "updateInterval": 50
        },
        "solver": "forceAtlas2Based"
      }
    }
    """)

    net.write_html(output_html, open_browser=False, notebook=True)
