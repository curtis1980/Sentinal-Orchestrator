# ---------- SENTINEL v4.0 — Intro Fix + Backend Integration ----------
import streamlit as st
import time, subprocess, json
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="SENTINEL", layout="wide")

# ---------- GLOBAL THEME ----------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stSidebar"], .stApp, .main, .block-container {
  background-color:#0D0F12 !important;
  color:#F8F8F8 !important;
  font-family:'Courier New', monospace !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] { background:transparent !important; }
hr { border:0; border-top:1px solid #2C313A; }

div[data-baseweb="select"] > div{
  background:#16191D !important;
  border:1px solid #E6394622 !important;
  border-radius:6px !important;
}
div[data-baseweb="select"] div, div[data-baseweb="select"] svg{
  color:#E63946 !important;
  font-family:'Courier New', monospace !important;
}

.stButton>button {
  background:#E63946 !important; color:#fff !important; border:none !important;
  border-radius:6px !important; font-weight:600 !important; height:38px !important;
  box-shadow:0 0 8px rgba(230,57,70,.28); transition:all .2s ease-in-out;
}
.stButton>button:hover{ background:#FF465A !important; box-shadow:0 0 14px rgba(255,70,90,.45); }

textarea, input, [data-baseweb="textarea"], [data-baseweb="input"]{
  background:#1E232B !important; color:#F8F8F8 !important;
  border:1px solid #2C313A !important; border-radius:6px !important;
}

[data-testid="stNotification"], .stAlert {
  background:#111720 !important; border:1px solid #1C232C !important; color:#D9E4F0 !important;
}
.chat-pane{
  background:#1E232B; border:1px solid #1C232C; border-radius:8px;
  padding:16px 18px; height:50vh; overflow-y:auto;
}

@keyframes typingIntro {
  from { width: 0ch; }
  to { width: 10ch; }
}
@keyframes blinkIntro {
  0%, 50% { border-color:#E63946; }
  51%, 100% { border-color:transparent; }
}
@keyframes fadeOutIntro {
  0% {opacity:1;}
  90% {opacity:1;}
  100% {opacity:0;display:none;}
}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "entry_done" not in st.session_state:
    st.session_state["entry_done"] = False
if "threads" not in st.session_state:
    st.session_state["threads"] = {}
if "prompt" not in st.session_state:
    st.session_state["prompt"] = ""

# ---------- CINEMATIC INTRO ----------
if not st.session_state["entry_done"]:
    st.markdown("""
    <div style="height:90vh;display:flex;flex-direction:column;justify-content:center;
                align-items:center;text-align:center;font-family:'Courier New',monospace;
                animation:fadeOutIntro 1.2s ease-out 4.2s forwards;">
        <div style="color:#E63946;font-size:42px;letter-spacing:.10em;font-weight:800;
                    margin-bottom:12px;display:inline-block;overflow:hidden;white-space:nowrap;
                    border-right:3px solid #E63946;
                    animation:typingIntro 2.6s steps(9,end), blinkIntro 0.8s step-end 3;
                    animation-fill-mode:forwards;">
            SENTINEL
        </div>
        <div style="color:#A8B2BD;font-size:14px;letter-spacing:.08em;margin:10px 0 22px;">
            AUTHENTICATING SESSION…
        </div>
        <div style="margin-top:8px;color:#9AA6B1;font-size:13px;text-align:left;line-height:1.6;">
            🛰 INITIALIZING NODES…<br>
            <span style="color:#48FF7F;">✅ STRATA NODE ONLINE</span><br>
            <span style="color:#48FF7F;">✅ DEALHAWK NODE ONLINE</span><br>
            <span style="color:#48FF7F;">✅ NEO NODE ONLINE</span><br>
            <span style="color:#48FF7F;">✅ PFNG NODE ONLINE</span><br>
            <span style="color:#48FF7F;">✅ CIPHER SECURE CHANNEL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(4.8)
    st.session_state["entry_done"] = True
    st.rerun()

# ---------- HEADER ----------
st.markdown("""
<div style="text-align:center;margin-top:8px;">
  <div style="color:#E63946;font-size:42px;letter-spacing:.10em;font-weight:800;">SENTINEL</div>
  <div style="font-family:'Courier New', monospace;color:#A8B2BD;font-size:15px;letter-spacing:.06em;">
      Autonomous Agents for Asymmetric Advantage
  </div>
</div>
<hr style="margin:14px 0 20px;">
""", unsafe_allow_html=True)

# ---------- AGENT SELECTOR ----------
AGENTS = {
    "strata": "Research & intelligence for energy/decarbonization.",
    "dealhawk": "Deal sourcing for profitable private companies.",
    "neo": "Financial modeling and scenario analysis.",
    "proforma": "Critical review and risk calibration (PFNG).",
    "cipher": "IC assembly and governance validation."
}
agent_keys = list(AGENTS.keys())

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    agent = st.selectbox("Choose agent", agent_keys, index=0, key="agent_select")
st.caption(f"⚙ {AGENTS[agent]}")

# ---------- CHAT DISPLAY ----------
thread = st.session_state["threads"].get(agent, [])
if thread:
    st.markdown('<div class="chat-pane">', unsafe_allow_html=True)
    for msg in thread[-10:]:
        st.markdown(
            f"<div style='border-left:3px solid #E63946;padding:8px 10px;margin:6px 0;color:#F8F8F8;'>"
            f"<b>{msg['agent'].upper()}</b><br>{msg['response']}"
            f"<div style='color:#9AA6B1;font-size:11px;margin-top:3px;'>⏱ {msg['time']}</div>"
            f"</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No messages yet.")

# ---------- PROMPT ----------
st.markdown('<div style="color:#A8B2BD;font-size:13px;">Type your prompt:</div>', unsafe_allow_html=True)
st.markdown(f'<div style="color:#73818C;font-size:12px;">Tip: ask {agent.capitalize()} with context (scope, region, metrics, time frame).</div>', unsafe_allow_html=True)
user_prompt = st.text_area("", placeholder=f"Ask {agent.capitalize()}…", height=90, label_visibility="collapsed", key="prompt_box")

# ---------- BACKEND CONNECTOR ----------
AGENT_CHAIN = {
    "strata": "dealhawk",
    "dealhawk": "neo",
    "neo": "proforma",
    "proforma": "cipher",
    "cipher": None,
}

def run_agent_subprocess(agent_key: str, query: str):
    try:
        result = subprocess.run(
            ["python", "sentinal_orchestrator.py", agent_key, query],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return f"❌ Agent {agent_key} error: {result.stderr or result.stdout}"
        data = json.loads(result.stdout)
        if "error" in data:
            return f"⚠️ {data['error']}"
        return data.get("output", str(data))
    except subprocess.TimeoutExpired:
        return f"⏱️ {agent_key.upper()} timed out."
    except Exception as e:
        return f"💥 Exception running {agent_key}: {e}"

def store_response(agent_key: str, response: str):
    now = datetime.now().strftime("%H:%M:%S")
    msg = {"agent": agent_key, "response": response, "time": now}
    st.session_state["threads"].setdefault(agent_key, []).append(msg)

# ---------- BUTTONS ----------
col1, col2, col3 = st.columns([4, 2, 2])
with col1:
    if st.button("🔁 Reset Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()
with col2:
    if st.button("💬 Ask Agent", use_container_width=True):
        query = st.session_state.get("prompt_box", "").strip()
        if not query:
            st.warning("Enter a prompt first.")
        else:
            with st.spinner(f"⚙️ ACCESSING {agent.upper()} NODE..."):
                output = run_agent_subprocess(agent, query)
            store_response(agent, output)
            st.success("✅ RESPONSE RECEIVED")
            st.rerun()
with col3:
    if st.button("➡ Send to Next", use_container_width=True):
        next_agent = AGENT_CHAIN.get(agent)
        if not next_agent:
            st.info("No next agent in chain.")
        else:
            last_thread = st.session_state["threads"].get(agent, [])
            if not last_thread:
                st.warning("No prior output to send.")
            else:
                prev_out = last_thread[-1]["response"][:2000]
                with st.spinner(f"➡ Forwarding to {next_agent.upper()}..."):
                    result = run_agent_subprocess(next_agent, prev_out)
                store_response(next_agent, result)
                st.success(f"✅ {next_agent.upper()} RESPONSE RECEIVED")
                st.rerun()
