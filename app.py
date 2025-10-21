# ---------- SENTINEL v3.5 — Final Stable UI Build ----------
# Includes: typewriter intro + unified Courier console UI

import streamlit as st
import time
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="SENTINEL", layout="wide")

st.markdown("""
<style>
body {
  background-color:#0D0F12 !important;
  color:#F8F8F8 !important;
  font-family:'Courier New', monospace !important;
}
hr { border:0; border-top:1px solid #2C313A; }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION SETUP ----------
if "entry_done" not in st.session_state:
    st.session_state["entry_done"] = False
if "threads" not in st.session_state:
    st.session_state["threads"] = {}
if "prompt" not in st.session_state:
    st.session_state["prompt"] = ""

# ---------- INTRO (Typewriter Boot Sequence) ----------
if not st.session_state["entry_done"]:
    st.markdown("""
    <style>
    @keyframes fadeOut {0%{opacity:1;}95%{opacity:0;}100%{opacity:0;display:none;}}
    @keyframes typing {from{width:0;}to{width:100%;}}
    @keyframes caret {0%,100%{border-color:transparent;}50%{border-color:#E63946;}}
    body {background:#0D0F12;}
    </style>

    <div style="height:90vh;display:flex;flex-direction:column;justify-content:center;
        align-items:center;text-align:center;font-family:'Courier New',monospace;
        animation:fadeOut 1.5s ease-out 3.4s forwards;">

        <div style="color:#E63946;font-size:42px;letter-spacing:.1em;font-weight:800;
                    margin-bottom:12px;border-right:2px solid #E63946;width:0;
                    overflow:hidden;white-space:nowrap;
                    animation:typing 2.6s steps(24,end) .3s forwards,
                               caret 1s step-end infinite;">
            SENTINEL
        </div>

        <div style="color:#A8B2BD;font-size:14px;letter-spacing:.08em;
                    margin:10px 0 22px;">AUTHENTICATING SESSION…</div>

        <div style="margin-top:8px;color:#9AA6B1;font-size:13px;
                    text-align:left;line-height:1.6;">
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
<style>
@keyframes typingHeader {from{width:0;}to{width:100%;}}
@keyframes caretHeader {0%,100%{border-color:transparent;}50%{border-color:#E63946;}}
@keyframes fadeInSub {from{opacity:0;}to{opacity:1;}}

.header-type {
  font-family:'Courier New', monospace;
  color:#E63946;
  font-weight:800;
  font-size:42px;
  letter-spacing:.1em;
  border-right:2px solid #E63946;
  white-space:nowrap;
  overflow:hidden;
  width:0;
  animation:typingHeader 2.4s steps(22,end) .2s forwards,
             caretHeader 1s step-end infinite;
}

.header-sub {
  font-family:'Courier New', monospace;
  color:#A8B2BD;
  font-size:15px;
  letter-spacing:.06em;
  margin-top:8px;
  opacity:0;
  animation:fadeInSub 1.2s ease 2.4s forwards;
}
</style>

<div style="text-align:center;margin-top:8px;">
  <div class="header-type">SENTINEL</div>
  <div class="header-sub">Autonomous Agents for Asymmetric Advantage</div>
</div>
<hr style="margin:14px 0 20px;border:0;border-top:1px solid #2C313A;">
""", unsafe_allow_html=True)

# ---------- AGENT SELECTOR ----------
AGENTS = {
    "strata": "Research & intelligence for energy/decarbonization.",
    "dealhawk": "Deal sourcing for profitable private companies.",
    "neo": "Financial modeling and scenario analysis.",
    "proforma": "Critical review and risk calibration (PFNG).",
    "cipher": "IC assembly and governance validation."
}
AGENT_KEYS = list(AGENTS.keys())

st.markdown("""
<style>
div[data-baseweb="select"] div,
label, .stCaption, div[data-testid="stMarkdownContainer"] p {
  font-family:'Courier New', monospace !important;
  color:#A8B2BD !important;
  letter-spacing:.05em !important;
}
div[data-baseweb="select"] > div {
  background:#1E232B !important;
  border:1px solid #E63946 !important;
  border-radius:6px !important;
}
div[data-baseweb="select"] svg { color:#E63946 !important; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,2,1])
with col2:
    agent = st.selectbox("Choose agent", AGENT_KEYS, index=0)
st.caption(f"⚙ {AGENTS[agent]}")

# ---------- CHAT WINDOW ----------
thread = st.session_state["threads"].get(agent, [])
if thread:
    st.markdown("<div style='background:#1E232B;border-radius:8px;"
                "padding:16px 18px;height:50vh;overflow-y:auto;'>",
                unsafe_allow_html=True)
    for msg in thread[-10:]:
        st.markdown(
            f"<div style='border-left:3px solid #E63946;padding:8px 10px;margin:6px 0;"
            f"color:#F8F8F8;font-family:Courier New,monospace;'>"
            f"<b>{msg['agent'].upper()}</b><br>{msg['response']}"
            f"<div style='color:#9AA6B1;font-size:11px;margin-top:3px;'>⏱ {msg['time']}</div></div>",
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No messages yet.")

# ---------- PROMPT AREA ----------
st.markdown("""
<style>
.prompt-label {
  font-family:'Courier New',monospace !important;
  color:#A8B2BD !important;
  font-size:13px !important;
  letter-spacing:.05em !important;
  margin-top:12px !important;
}
.prompt-helper {
  font-family:'Courier New',monospace !important;
  color:#73818C !important;
  font-size:12px !important;
  letter-spacing:.04em !important;
  margin-bottom:6px !important;
}
textarea, [data-baseweb="textarea"] {
  font-family:'Courier New',monospace !important;
  background:#1E232B !important;
  color:#F8F8F8 !important;
  border:1px solid #2C313A !important;
  border-radius:6px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="prompt-label">Type your prompt:</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="prompt-helper">Tip: ask {agent.capitalize()} with context — include scope, region, metrics, and time frame for best precision.</div>',
    unsafe_allow_html=True
)
user_prompt = st.text_area("", placeholder=f"Ask {agent.capitalize()}…", height=90, label_visibility="collapsed")

# ---------- BUTTONS ----------
colA, colB, colC = st.columns([4,2,2])
with colA:
    if st.button("🔁 Reset Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()
with colB:
    st.button("💬 Ask Agent", use_container_width=True)
with colC:
    st.button(f"➡ Send to Next", use_container_width=True)
