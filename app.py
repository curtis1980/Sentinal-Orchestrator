# app.py
import streamlit as st
import subprocess
import time
from datetime import datetime

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

# --- Page Setup ---
st.set_page_config(page_title="Sentinal Orchestrator", layout="centered")
st.title("🤖 Sentinal Orchestrator")
st.caption("Multi-agent AI for Energy & Private Equity Intelligence")

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []
if "last_agent" not in st.session_state:
    st.session_state.last_agent = None
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "next_agent" not in st.session_state:
    st.session_state.next_agent = None

# --- Helper Function ---
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
            st.success(f"✅ Completed in {duration}s")
            st.markdown(f"**{agent.upper()} says:**\n\n{output}")
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

# --- Main App UI ---
agent = st.selectbox("🧩 Choose an agent:", AGENT_SEQUENCE)
st.markdown(f"**Description:** {AGENTS[agent]['desc']}")
query = st.text_area("💬 Enter your query:", placeholder="Ask your agent something...")

if st.button("🚀 Run Agent"):
    if query.strip():
        run_agent(agent, query)
    else:
        st.warning("Please enter a query before running.")

# --- Follow-up + Next Agent ---
if st.session_state.last_agent and st.session_state.last_response:
    st.markdown("### 🔁 Last Interaction")
    st.write(f"**Agent:** {st.session_state.last_agent.upper()}")
    st.write(f"**Response:** {st.session_state.last_response}")

    if st.session_state.next_agent:
        st.markdown("---")
        st.markdown(f"**Next Recommended Agent:** `{st.session_state.next_agent.upper()}`")
        follow_up = st.text_input("🔍 Follow-up query (optional):")
        if st.button(f"Continue with {st.session_state.next_agent.upper()}"):
            if follow_up.strip():
                run_agent(st.session_state.next_agent, follow_up)
            else:
                st.warning("Please enter a follow-up query before continuing.")
