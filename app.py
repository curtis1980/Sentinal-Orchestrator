# app.py  — Sentinel Beta v1.0
import streamlit as st
import subprocess
import time
from datetime import datetime

# =========================================================
# Sentinel Header & Theme
# =========================================================
st.set_page_config(page_title="Sentinel", layout="centered")

st.markdown("""
<div style="
    text-align:center;
    background-color:#0a0a0a;
    padding:50px 0 30px 0;
    border-bottom:3px solid #e63946;
">
    <h1 style="color:#f2f2f2;font-size:46px;font-weight:800;letter-spacing:2px;margin-bottom:10px;">
        SENTINEL
    </h1>
    <h4 style="color:#e63946;font-weight:600;letter-spacing:1.5px;margin-top:0;">
        AUTONOMOUS AGENTS FOR ASYMMETRIC ADVANTAGE
    </h4>
</div>
""", unsafe_allow_html=True)

# =========================================================
# Custom CSS (dark theme, red accent, muted agent tones)
# =========================================================
st.markdown("""
<style>
body, .main, .block-container {
    background-color:#0a0a0a !important;
    color:#f2f2f2 !important;
    font-family:'Inter',sans-serif;
}

/* Scrollable chat area */
.chat-container {
    height:65vh;
    overflow-y:auto;
    background-color:#111;
    border:1px solid #1f1f1f;
    border-radius:8px;
    padding:16px;
}

/* Input bar */
.input-area {
    position:sticky;
    bottom:0;
    background-color:#0a0a0a;
    border-top:1px solid #222;
    padding:12px;
}

/* Agent message bubbles */
.bubble {padding:14px 16px;border-radius:10px;margin:10px 0;color:#fff;
         line-height:1.4em;transition:all 0.2s ease;box-shadow:0 1px 3px rgba(0,0,0,0.4);}
.bubble:hover {transform:scale(1.01);}
.bubble.strata {background:#123524;}
.bubble.dealhawk {background:#3a2f0b;}
.bubble.neo {background:#102941;}
.bubble.cipher {background:#2d1b4a;}
.bubble.proforma {background:#2e1d1f;}

/* Buttons */
button[data-baseweb="button"] {
    background-color:#e63946 !important;
    color:white !important;
    border:none !important;
    font-weight:600;
    border-radius:6px;
}
button[data-baseweb="button"]:hover {background-color:#ff4d5a !important;}

/* Text area */
textarea {
    background-color:#111 !important;
    color:#fff !important;
    border:1px solid #333 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# Agent Registry
# =========================================================
AGENTS = {
    "strata": {"color":"#123524","desc":"Research and intelligence agent for energy and decarbonization ecosystems."},
    "dealhawk": {"color":"#3a2f0b","desc":"Deal sourcing agent identifying late-stage, profitable private companies in energy transition."},
    "neo": {"color":"#102941","desc":"Analytical agent that builds financial models, pro formas, and scenario simulations."},
    "cipher": {"color":"#2d1b4a","desc":"Security and coordination agent managing communication between other agents."},
    "proforma": {"color":"#2e1d1f","desc":"Automates and validates private-equity financial assumptions and model inputs."}
}
AGENT_SEQUENCE = list(AGENTS.keys())

# =========================================================
# Session State
# =========================================================
st.session_state.setdefault("history", [])
st.session_state.setdefault("last_agent", None)
st.session_state.setdefault("last_response", None)
st.session_state.setdefault("next_agent", None)
st.session_state.setdefault("is_running", False)

# =========================================================
# Core Agent Runner
# =========================================================
def run_agent(agent, query):
    if st.session_state.is_running:
        return
    st.session_state.is_running = True
    start = time.time()

    with st.spinner(f"Running {agent.upper()}..."):
        try:
            result = subprocess.run(
                ["python", "sentinal_orchestrator.py", agent, query],
                capture_output=True, text=True, check=True
            )
            # clean duplicate lines
            output = "\n".join([ln for ln in result.stdout.splitlines() if ln.strip()])
            duration = round(time.time() - start, 2)

            st.markdown(
                f"<div class='bubble {agent}'><b>{agent.upper()}:</b><br>{output.replace(chr(10), '<br>')}"
                f"<br><small>⏱ {duration}s</small></div>", unsafe_allow_html=True
            )

            st.session_state.history.append({
                "agent": agent, "query": query,
                "response": output,
                "time": datetime.now().strftime("%H:%M:%S")
            })
            st.session_state.last_agent = agent
            st.session_state.last_response = output
            idx = AGENT_SEQUENCE.index(agent)
            st.session_state.next_agent = AGENT_SEQUENCE[idx+1] if idx+1 < len(AGENT_SEQUENCE) else None

        except subprocess.CalledProcessError as e:
            st.error(f"⚠ Agent Error: {e.stderr or e.stdout or 'Unknown issue'}")
        finally:
            st.session_state.is_running = False

# =========================================================
# Main UI
# =========================================================
st.markdown("### 💬 Conversation")
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for h in st.session_state.history[-10:]:
    st.markdown(
        f"<div class='bubble {h['agent']}'><b>{h['agent'].upper()}:</b><br>{h['response'].replace(chr(10), '<br>')}</div>",
        unsafe_allow_html=True
    )
st.markdown("</div>", unsafe_allow_html=True)

# Input area (static)
st.markdown("<div class='input-area'>", unsafe_allow_html=True)
agent = st.selectbox("Choose an agent:", AGENT_SEQUENCE)
query = st.text_area("Type your prompt here:", key="user_query", placeholder="Ask your agent something...")

cols = st.columns([1,1])
if cols[0].button("💬 Ask Same Agent", use_container_width=True):
    if query.strip(): run_agent(agent, query)
    else: st.warning("Please enter a query first.")
if cols[1].button(f"➡ Send to {st.session_state.get('next_agent','NEXT').upper()}", use_container_width=True):
    if query.strip():
        next_agent = st.session_state.get("next_agent") or agent
        run_agent(next_agent, query)
    else:
        st.warning("Please enter a query first.")
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# Reset / New Session
# =========================================================
st.markdown("<hr>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("🔁 Start New Search", use_container_width=True):
        with st.spinner("🧠 Clearing session and resetting Sentinel..."):
            time.sleep(1)
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.success("✅ Ready for a fresh search!")
            time.sleep(0.8)
            st.experimental_rerun()
