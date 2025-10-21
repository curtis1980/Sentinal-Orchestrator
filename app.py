# ---------- SENTINEL v3.5.1 — Final Stable Console UI ----------
# Features:
# - Verified typewriter boot intro + fade
# - Terminal/ Courier typography across the app
# - Global dark theme (no white flash; enforced on all containers)
# - Centered compact agent select, blue-gray chat pane
# - Prompt label + helper, aligned button row

import streamlit as st
import time
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="SENTINEL", layout="wide")

# ---------- GLOBAL THEME (enforced) ----------
st.markdown("""
<style>
/* Hard-lock dark bg on all core wrappers to avoid white areas or flashes */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], 
[data-testid="stToolbar"], [data-testid="stSidebar"], .stApp, .main, .block-container {
  background-color:#0D0F12 !important;
  color:#F8F8F8 !important;
  font-family:'Courier New', monospace !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] { background:transparent !important; }
hr { border:0; border-top:1px solid #2C313A; }

/* Normalize markdown text color */
.stMarkdown, .stText, .stCaption, .st-emotion-cache p, label, span {
  color:#D9D9D9 !important; font-family:'Courier New', monospace !important;
}

/* Buttons (red) */
.stButton>button {
  background:#E63946 !important; color:#fff !important; border:none !important;
  border-radius:6px !important; font-weight:600 !important; height:38px !important;
  box-shadow:0 0 8px rgba(230,57,70,.28); transition:all .2s ease-in-out;
}
.stButton>button:hover{ background:#FF465A !important; box-shadow:0 0 14px rgba(255,70,90,.45); }

/* Inputs / textarea */
textarea, input, [data-baseweb="textarea"], [data-baseweb="input"]{
  background:#1E232B !important; color:#F8F8F8 !important;
  border:1px solid #2C313A !important; border-radius:6px !important;
}

/* Selectbox (compact, red border, Courier) */
div[data-baseweb="select"] > div{
  background:#1E232B !important; border:1px solid #E63946 !important; border-radius:6px !important;
}
div[data-baseweb="select"] div, div[data-baseweb="select"] svg{
  color:#E63946 !important; font-family:'Courier New', monospace !important;
}

/* Info/alert restyle (keeps subtle blue strip look) */
[data-testid="stNotification"], .stAlert {
  background:#111720 !important; border:1px solid #1C232C !important; color:#D9E4F0 !important;
}

/* Chat container */
.chat-pane{
  background:#1E232B; border:1px solid #1C232C; border-radius:8px;
  padding:16px 18px; height:50vh; overflow-y:auto;
}

/* Header animations */
@keyframes typingHeader{from{width:0}to{width:100%}}
@keyframes caretHeader{0%,100%{border-color:transparent}50%{border-color:#E63946}}
@keyframes fadeInSub{from{opacity:0}to{opacity:1}}

.header-type{
  font-family:'Courier New', monospace; color:#E63946; font-weight:800;
  font-size:42px; letter-spacing:.10em; border-right:2px solid #E63946;
  white-space:nowrap; overflow:hidden; width:0;
  animation:typingHeader 2.4s steps(22,end) .2s forwards, caretHeader 1s step-end infinite;
}
.header-sub{
  font-family:'Courier New', monospace; color:#A8B2BD; font-size:15px;
  letter-spacing:.06em; margin-top:8px; opacity:0; animation:fadeInSub 1.2s ease 2.4s forwards;
}

/* Prompt label + helper */
.prompt-label{ color:#A8B2BD !important; font-size:13px !important; letter-spacing:.05em !important; }
.prompt-helper{ color:#73818C !important; font-size:12px !important; letter-spacing:.04em !important; }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
if "entry_done" not in st.session_state:
    st.session_state["entry_done"] = False
if "threads" not in st.session_state:
    st.session_state["threads"] = {}
if "prompt" not in st.session_state:
    st.session_state["prompt"] = ""

# ---------- BOOT INTRO (typewriter + fade) ----------
if not st.session_state["entry_done"]:
    st.markdown("""
    <style>
    @keyframes fadeOut {0%{opacity:1;}95%{opacity:0;}100%{opacity:0;display:none}}
    @keyframes typing {from{width:0}to{width:100%}}
    @keyframes caret {0%,100%{border-color:transparent}50%{border-color:#E63946}}
    </style>

    <div style="height:90vh;display:flex;flex-direction:column;justify-content:center;
         align-items:center;text-align:center;font-family:'Courier New',monospace;
         animation:fadeOut 1.5s ease-out 3.4s forwards;">
      <div style="color:#E63946;font-size:42px;letter-spacing:.10em;font-weight:800;margin-bottom:12px;
                  border-right:2px solid #E63946;width:0;overflow:hidden;white-space:nowrap;
                  animation:typing 2.6s steps(24,end) .3s forwards, caret 1s step-end infinite;">
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
  <div class="header-type">SENTINEL</div>
  <div class="header-sub">Autonomous Agents for Asymmetric Advantage</div>
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

# center the selector
s1, s2, s3 = st.columns([1,2,1])
with s2:
    agent = st.selectbox("Choose agent", agent_keys, index=0, key="agent_select")
st.caption(f"⚙ {AGENTS[agent]}")

# ---------- CHAT WINDOW ----------
thread = st.session_state["threads"].get(agent, [])
if thread:
    st.markdown('<div class="chat-pane">', unsafe_allow_html=True)
    for msg in thread[-10:]:
        st.markdown(
            f"<div style='border-left:3px solid #E63946;padding:8px 10px;margin:6px 0;"
            f"color:#F8F8F8'>"
            f"<b>{msg['agent'].upper()}</b><br>{msg['response']}"
            f"<div style='color:#9AA6B1;font-size:11px;margin-top:3px;'>⏱ {msg['time']}</div>"
            f"</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No messages yet.")

# ---------- PROMPT + HELPER ----------
st.markdown('<div class="prompt-label">Type your prompt:</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="prompt-helper">Tip: ask {agent.capitalize()} with context — include scope, region, metrics, and time frame for best precision.</div>',
    unsafe_allow_html=True
)
user_prompt = st.text_area("", placeholder=f"Ask {agent.capitalize()}…",
                           height=90, label_visibility="collapsed", key="prompt_box")

# ---------- BUTTON ROW ----------
c1, c2, c3 = st.columns([4,2,2])
with c1:
    if st.button("🔁 Reset Session", use_container_width=True):
        st.session_state.clear(); st.rerun()
with c2:
    st.button("💬 Ask Agent", use_container_width=True)
with c3:
    st.button("➡ Send to Next", use_container_width=True)
