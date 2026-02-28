# dashboard.py
import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import time

# ------------------------------
# CONFIG
# ------------------------------
RISK_DECAY = 0.6
ALPHA = 0.5  # velocity weight
BETA = 0.3   # network exposure weight
GAMMA = 0.2  # high value transaction weight
RISK_THRESHOLDS = {
    "medium": 4,
    "high": 7
}
DATA_FILE = "data/synthetic_transactions.csv"  # path to your dataset

# ------------------------------
# LOAD DATA
# ------------------------------
df = pd.read_csv(DATA_FILE)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# ------------------------------
# STREAMLIT SETUP
# ------------------------------
st.set_page_config(page_title="💧 RIPPLE Prototype", layout="wide")
st.title("💧 RIPPLE - Fraud Network Visualization")

# Session state to store graph and processed index
if "graph" not in st.session_state:
    st.session_state.graph = nx.DiGraph()
if "processed_index" not in st.session_state:
    st.session_state.processed_index = 0

# ------------------------------
# RISK FUNCTIONS
# ------------------------------
def compute_risk(G, node):
    """Compute risk for a node based on simple formula."""
    base_risk = G.nodes[node].get("risk", 0)
    # velocity: number of outgoing tx in last 10 minutes
    now = pd.Timestamp.now()
    velocity_score = sum(
        1 for _, _, d in G.out_edges(node, data=True)
        if now - pd.Timestamp(d["timestamp"]) < pd.Timedelta(minutes=10)
    )
    # network exposure: number of successors
    network_exposure = len(list(G.successors(node)))
    # high value transactions
    high_value_tx = sum(d["amount"] > 3000 for _, _, d in G.out_edges(node, data=True))
    risk_new = base_risk + ALPHA*velocity_score + BETA*network_exposure + GAMMA*high_value_tx
    return min(risk_new, 10)

def propagate_risk(G):
    """Propagate risk to connected nodes with decay factor."""
    for node in G.nodes:
        risk = compute_risk(G, node)
        G.nodes[node]["risk"] = risk

    for node in G.nodes:
        risk = G.nodes[node]["risk"]
        for neighbor in G.successors(node):
            G.nodes[neighbor]["risk"] += risk * RISK_DECAY
            G.nodes[neighbor]["risk"] = min(G.nodes[neighbor]["risk"], 10)
    return G

# ------------------------------
# PROCESS NEXT TRANSACTION
# ------------------------------
def process_next_tx():
    if st.session_state.processed_index >= len(df):
        return False
    tx = df.iloc[st.session_state.processed_index]
    f, t = tx["from_account"], tx["to_account"]
    G = st.session_state.graph
    # add nodes if not exist
    if f not in G:
        G.add_node(f, risk=0)
    if t not in G:
        G.add_node(t, risk=0)
    # add edge
    G.add_edge(f, t, amount=tx["amount"], channel=tx["channel"], timestamp=tx["timestamp"])
    st.session_state.graph = propagate_risk(G)
    st.session_state.processed_index += 1
    return True

# ------------------------------
# SIMULATE LIVE STREAM
# ------------------------------
st.subheader("Simulated Transaction Streaming")
placeholder = st.empty()

if st.button("Process Next Transaction"):
    process_next_tx()

if st.checkbox("Auto-stream Transactions"):
    with placeholder.container():
        for _ in range(5):  # process 5 transactions per iteration
            has_next = process_next_tx()
            if not has_next:
                st.info("All transactions processed!")
                break
            st.write(f"Processed transaction #{st.session_state.processed_index}")
            time.sleep(0.5)

# ------------------------------
# DISPLAY GRAPH
# ------------------------------
st.subheader("Transaction Graph")
G = st.session_state.graph
nt = Network(height="600px", width="100%", notebook=False, directed=True)
for node, data in G.nodes(data=True):
    risk = data.get("risk",0)
    color = "green" if risk < RISK_THRESHOLDS["medium"] else "yellow" if risk < RISK_THRESHOLDS["high"] else "red"
    nt.add_node(node, label=f"{node}\nRisk:{round(risk,1)}", color=color, title=f"Risk:{round(risk,1)}")

for f, t, d in G.edges(data=True):
    nt.add_edge(f, t, title=f"{d['channel']} ${d['amount']}")

nt.show_buttons(filter_=['physics'])
nt.save_graph("network.html")
st.components.v1.html(open("network.html",'r').read(), height=600)

# ------------------------------
# DISPLAY RISK TABLE & PREVENTIVE ACTIONS
# ------------------------------
st.subheader("Account Risk Levels & Preventive Actions")
risk_data = [(n, round(d["risk"],2)) for n,d in G.nodes(data=True)]
st.table(risk_data)

st.subheader("Preventive Actions")
for node, data in G.nodes(data=True):
    risk = data.get("risk",0)
    if risk >= RISK_THRESHOLDS["high"]:
        st.write(f"🚨 Account {node} flagged! Action: Temporary Freeze + OTP verification")
    elif risk >= RISK_THRESHOLDS["medium"]:
        st.write(f"⚠️ Account {node} medium risk. Action: Step-up authentication")