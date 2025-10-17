# app.py
import streamlit as st
import subprocess
import time
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="Sentinal Orchestrator", layout="centered")
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
            padding: 1rem 2rem;
        }
        .title-bar {
            background: linear-gradient(90deg, #0d6efd, #6610f2);
            color: white;
            padding: 1.2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 1.2rem;
        }
        .agent-card {
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 0.8rem;
            margin-top: 0.5rem;
        }
        .chat-bubble {
            padding: 12px;
            border-radius: 10px;
            color: white;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title-bar'><h2>🤖 Sentinal Orchestrator</h2><p>Multi-agent AI for Energy & Private Equity Intelligence</p></div>", unsafe_allow_html=True)

# --- Agent Data ---
AGENTS = {
    "strata": {
        "color": "#4CAF50",
        "desc": "Research and intelligence agent for energy and decarbonization ecosystems."
    },
    "dealhawk": {
        "color": "#FF9800",
        "desc": "Deal sourcing agent for identifying late-stage, profitable private companies in energy transition."
    },
    "neo": {
        "color": "#2196F3",
        "desc": "Analytical agent that builds financial models, pro formas, and scenario simulations."
    },
    "cipher": {
        "color": "#9C27B0",
        "desc": "Security and coordination agent managing communication between other agents."
    },
    "proforma": {
        "color": "#795548",
        "desc": "Automates and validates private equity financial assumptions and model inputs."
    }
}
AGENT_SEQUENCE = list(AGENTS.keys())

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []
if "last_agent" not in st.session_state:
    st.session_state.last_agent = None
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "next_agent" not in st.session_state:
    st.session_state.next_agent = None

# --- Select Agent ---
agent = st.selectbox("🧩 Choose an agent:", AGENT_SEQUENCE)
st.markdown(f"<div class='agent-card'><b>{agent.upper()}</b>: {AGENTS[agent]['desc']}</div>", unsafe_allow_html=True)

query = st.text_area("💬 Enter your query:", placeholder="Ask your agent something...")

# --- Run Helper ---
def run_agent(agent, query):
    """Run a specific agent with subprocess call"""
    start = time.time()
    with st.spinner(f"Running {agent.upper()}..."):
        try:
            result = subprocess.run(
                ["python", "sentinal_orchestrator.py", agent, query],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout.strip()
            duration = round(time.time() - start, 2)
            st.markdown(
                f"<div class='chat-bubble' style='background-color:{AGENTS[agent]['color']};'><b>{agent.upper()} says:</b><br><br>{output.replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.history.append({
                "agent": agent,
                "query": query,
                "response": output,
                "time": timestamp
            })
            st.session_state.last_agent = agent
            st.session_state.last_response = output
            idx = AGENT_SEQUENCE.index(agent)
            st.session_state.next_agent = AGENT_SEQUENCE[idx + 1] if idx + 1 < len(AGENT_SEQUENCE) else None
        except subprocess.CalledProcessError as e:
            st.error(f"⚠️ Agent Error: {e.stderr or e.stdout or 'Unknown issue'}")

# --- Run Button ---
if st.button("🚀 Run Agent"):
    if not query.strip():
        st.warning("Please enter a query before running.")
    else:
        run_agent(agent, query)

# --- Follow-up + Next Agent ---
if st.session_state.last_agent and st.session_state.last_response:

