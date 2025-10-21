# SENTINEL Console v4.2 (Demo-Stable)
import streamlit as st, sys, subprocess, json, time
from datetime import datetime

st.set_page_config(page_title="SENTINEL", layout="wide")

# --- Back-compat shim: Streamlit removed experimental_rerun in newer versions ---
if not hasattr(st, "experimental_rerun"):
    st.experimental_rerun = st.rerun  # maps to stable API

# --- Style (kept minimal) ---
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#0D0F12; color:#F8F8F8; }
.stButton>button { background:#E63946; color:#fff; border:none; border-radius:6px; }
.chat{background:#1E232B;border:1px solid #1C232C;border-radius:8px;padding:12px;max-height:48vh;overflow:auto;}
</style>
""", unsafe_allow_html=True)

# --- State ---
state = st.session_state
state.setdefault("phase", "console")   # intro removed for stability
state.setdefault("threads", {})

# --- Header ---
st.markdown("""
<div style="text-align:center;margin-top:6px;">
  <div style="color:#E63946;font-size:38px;font-weight:800;">SENTINEL</div>
  <div style="color:#A8B2BD;">Autonomous Agents for Asymmetric Advantage</div>
</div>
<hr>
""", unsafe_allow_html=True)

# --- Agents & Chain ---
AGENTS = {
    "strata": "Research & intelligence",
    "dealhawk": "Deal sourcing",
    "neo": "Financial modeling",
    "proforma": "Stress test / diligence",
    "cipher": "Governance / IC"
}
CHAIN = {"strata":"dealhawk","dealhawk":"neo","neo":"proforma","proforma":"cipher","cipher":None}

# --- Selector ---
c1,c2,c3 = st.columns([1,2,1])
with c2:
    agent = st.selectbox("Choose agent", list(AGENTS.keys()), index=0, key="agent_select")
st.caption(f"⚙ {AGENTS[agent]}")

# --- Chat panel ---
thread = state.threads.get(agent, [])
if thread:
    st.markdown('<div class="chat">', unsafe_allow_html=True)
    for m in thread[-12:]:
        st.markdown(
            f"<div style='border-left:3px solid #E63946;padding:6px 8px;margin:6px 0;'>"
            f"<b>{m['agent'].upper()}</b><br>{m['response']}"
            f"<div style='color:#9AA6B1;font-size:11px;'>⏱ {m['time']}</div>"
            f"</div>", unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No messages yet.")

# --- Prompt ---
prompt = st.text_area("Prompt", placeholder=f"Ask {agent.capitalize()}…", height=90, key="prompt_box")

# --- Orchestrator call ---
def call_orchestrator(agent_key: str, query: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "sentinal_orchestrator.py", agent_key, query],
            capture_output=True, text=True, timeout=30
        )
        # show stderr to help debugging but keep UX safe
        if result.returncode != 0:
            return f"❌ {result.stderr or result.stdout}"
        data = json.loads(result.stdout)
        # Single agent returns a dict; fullchain returns {final, chain}
        if "final" in data:
            return data["final"]["summary"]
        if "summary" in data:
            return data["summary"]
        return str(data)
    except subprocess.TimeoutExpired:
        return f"⏱️ {agent_key.upper()} timed out."
    except Exception as e:
        return f"💥 {type(e).__name__}: {e}"

def store(agent_key: str, text: str):
    state.threads.setdefault(agent_key, []).append({
        "agent": agent_key,
        "response": text,
        "time": datetime.now().strftime("%H:%M:%S")
    })

# --- Controls ---
b1,b2,b3 = st.columns([4,2,2])
with b1:
    if st.button("🔁 Reset Session", use_container_width=True):
        state.threads = {}
        state.prompt_box = ""
with b2:
    if st.button("💬 Ask Agent", use_container_width=True):
        q = (state.get("prompt_box") or "").strip()
        if not q:
            st.warning("Enter a prompt.")
        else:
            with st.spinner(f"⚙️ ACCESSING {agent.upper()} NODE..."):
                out = call_orchestrator(agent, q)
            store(agent, out)
            st.success("✅ RESPONSE RECEIVED")
with b3:
    if st.button("➡ Send to Next", use_container_width=True):
        nxt = CHAIN.get(agent)
        if not nxt:
            st.info("No next agent in chain.")
        else:
            last = state.threads.get(agent, [])
            if not last:
                st.warning("No prior output to forward.")
            else:
                payload = last[-1]["response"][:2000]
                with st.spinner(f"➡ Forwarding to {nxt.upper()}..."):
                    out = call_orchestrator(nxt, payload)
                store(nxt, out)
                st.success(f"✅ {nxt.upper()} RESPONSE RECEIVED")
