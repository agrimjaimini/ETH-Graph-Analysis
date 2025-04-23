import networkx as nx
from typing import List, Dict

def build_graph(transactions: List[Dict]) -> nx.DiGraph:
    """
    Construct a directed graph from a list of transactions.
    Nodes: addresses; Edges: aggregated by count and total value.
    """
    G = nx.DiGraph()
    for tx in transactions:
        sender = tx['from']
        receiver = tx['to'] or 'contract_creation'
        value = tx['value']
        if G.has_edge(sender, receiver):
            G[sender][receiver]['value'] += value
            G[sender][receiver]['count'] += 1
        else:
            G.add_edge(sender, receiver, value=value, count=1)
    return G