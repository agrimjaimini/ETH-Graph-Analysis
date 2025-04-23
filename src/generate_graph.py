import os
import json
from fetch_data import fetch_transactions, get_current_block
from graph_builder import build_graph
from anomaly import detect_anomalies
from visualize import visualize_graph
import pandas as pd


from dotenv import load_dotenv
load_dotenv()   


def generate_graph(start_block : int, edge_value=.25):
    START_BLOCK = start_block
    API_KEY = os.getenv('ETHERSCAN_API_KEY')
    RPC_URL = os.getenv('RPC_URL_KEY')
    END_BLOCK = int(get_current_block(API_KEY))


    # 1) Fetch
    txs = fetch_transactions(START_BLOCK, END_BLOCK, API_KEY)
    df = pd.DataFrame(txs)  
    os.makedirs('data', exist_ok=True)
    with open('data/txs.json', 'w') as f:
        json.dump(txs, f)

    # 2) Build graph
    G = build_graph(txs)

    # 3) Detect anomalies
    df_anom = detect_anomalies(G)
    df_anom.to_csv('data/anomalies.csv', index=False)

    # 4) Visualize
    visualize_graph(G, df, RPC_URL, output_html='src/static/graph.html', min_edge_value=edge_value)  

