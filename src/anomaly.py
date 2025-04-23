import pandas as pd
from sklearn.ensemble import IsolationForest
import networkx as nx

def detect_anomalies(G: nx.DiGraph, contamination: float = 0.01) -> pd.DataFrame:
    """
    Compute node-level features and detect anomalies using Isolation Forest.
    Returns a DataFrame with columns: node, in_degree, out_degree, total_value_in,
    total_value_out, anomaly_score, anomaly (bool).
    """
    records = []
    for n in G.nodes():
        in_edges = G.in_edges(n, data=True)
        out_edges = G.out_edges(n, data=True)
        records.append({
            'node': n,
            'in_degree': G.in_degree(n, weight='count'),
            'out_degree': G.out_degree(n, weight='count'),
            'total_value_in': sum(d['value'] for _, _, d in in_edges),
            'total_value_out': sum(d['value'] for _, _, d in out_edges)
        })
    df = pd.DataFrame(records)
    features = df[['in_degree', 'out_degree', 'total_value_in', 'total_value_out']]
    iso = IsolationForest(contamination=contamination)
    df['anomaly_score'] = iso.fit_predict(features)
    df['anomaly'] = df['anomaly_score'] == -1
    return df