# app.py
import streamlit as st
import subprocess
import time
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="Sentinal Orchestrator", layout="centered")
# (HTML, styling, etc.)

# --- Agent Data ---
AGENTS = {
    # your agent dictionary here
}

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []
if "last_agent" not in st.session_state:
    st.session_state.last_agent = None
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "next_agent" not in st.session_state:
    st.session_state.next_agent = None

# --- Run Helper Function ---
def run_agent(agent, query):
    # (your subprocess logic here)
    pass

# --- Main App Body ---
agent = st.selectbox("🧩 Choose an agent:", list(AGENTS.keys()))
query = st.text_area("💬 Enter your query:")
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

