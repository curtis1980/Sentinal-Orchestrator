# ---------- SENTINEL v3.5.3 — Typewriter & Caret Fix ----------
# Fixes:
# - True typewriter letter animation (no sliding text)
# - Caret disappears after typing completes
# - UI colors match cinematic terminal aesthetic

import streamlit as st
import time
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="SENTINEL", layout="wide")

# ---------- GLOBAL THEME ----------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], 
[data-testid="stToolbar"], [data-testid="stSidebar"], .stApp, .main, .block-container {
  background-color:#0D0F12 !important;
  color:#F8F8F8 !important;
  font-family:'Courier New', monospace !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] { background:transparent !important; }
hr { border:0; border-top:1px solid #2C313A; }

/* Dropdown harmonized gray tone */
div[data-baseweb="select"] > div{
  background:#16191D !important;
  border:1px solid #E6394622 !important;
  border-radius:6px !important;
}
div[data-baseweb="select"] div, div[data-baseweb="select"] svg{
  color:#E63946 !important;
  font-family:'Courier New', monospace !important;
}

/* Buttons (red aesthetic) */
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

/* Info + chat styling */
[data-testid="stNotification"], .stAlert {
  background:#111720 !important; border:1px solid #1C232C !important; color:#D9E4F0 !important;
}
.chat-pane{
  background:#1E232B; border:1px solid #1C232C; border-radius:8px;
  padding:16px 18px; height:50vh; overflow-y:auto;
}

/* --- Header animation (true typewriter, fixed cutoff) --- */
@keyframes typing {
  from { width: 0ch; }
  to { width: 10ch; }  /* allow full render of "SENTINEL" */
}
@keyframes blink {
  0%, 50% { border-color: #E63946; }
  51%, 100% { border-color: transparent; }
}
.header-type {
  display:inline-block;
  overflow:hidden;
  white-space:nowrap;
  color:#E63946;
  font-weight:800;
  font-size:42px;
  letter-spacing:.10em;
  border-right:3px solid #E63946;
  animation: typing 2.4s steps(9,end) forwards, blink 0.8s step-end 3;
  animation-fill-mode:forwards;
}

.header-sub {
  font-family:'Courier New', monospace;
  color:#A8B2BD;
  font-size:15px;
  letter-spacing:.06em;
  margin-top:8px;
  opacity:0;
  animation: fadeInSub 1.2s ease 2.4s forwards;
}
@keyframes fadeInSub { from {opacity:0;} to {opacity:1;} }

/* Prompt labels */
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

# ---------- INTRO (fade + typing, caret stops) ----------
if not st.session_state["entry_done"]:
    st.markdown("""
    <style>
    @keyframes fadeOut {0%{opacity:1;}95%{opacity:0;}100%{opacity:0;display:none}}
   @keyframes typingIntro {
  from { width: 0ch; }
  to { width: 10ch; } /* one extra character space */
}
    @keyframes blinkIntro {
      0%,50% { border-color:#E63946; }
      51%,100% { border-color:transparent; }
    }
    </style>

    <div style="height:90vh;display:flex;flex-direction:column;justify-content:center;
         align-items:center;text-align:center;font-family:'Courier New',monospace;
         animation:fadeOut 1.5s ease-out 3.4s forwards;">
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

c1, c2, c3 = st.columns([1,2,1])
with c2:
    agent = st.selectbox("Choose agent", agent_keys, index=0, key="agent_select")
st.caption(f"⚙ {AGENTS[agent]}")

# ---------- CHAT DISPLAY ----------
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

# ---------- PROMPT ----------
st.markdown('<div class="prompt-label">Type your prompt:</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="prompt-helper">Tip: ask {agent.capitalize()} with context — include scope, region, metrics, and time frame for best precision.</div>',
    unsafe_allow_html=True
)
user_prompt = st.text_area("", placeholder=f"Ask {agent.capitalize()}…", height=90, label_visibility="collapsed", key="prompt_box")

# ---------- BUTTONS ----------
col1, col2, col3 = st.columns([4,2,2])
with col1:
    if st.button("🔁 Reset Session", use_container_width=True):
        st.session_state.clear(); st.rerun()
with col2:
    st.button("💬 Ask Agent", use_container_width=True)
with col3:
    st.button("➡ Send to Next", use_container_width=True)

