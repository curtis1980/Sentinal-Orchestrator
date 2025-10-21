# ---------- Sentinel v3.3.5 — Final UI Alignment Build ----------
# Target: black-matte espionage console layout from reference image
# Includes: fade intro, centered alignment, consistent colors, 3-button row

import time, subprocess, streamlit as st
from datetime import datetime

st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
:root, html, body, [class*="stAppViewContainer"], [class*="stMain"] {
    background-color:#0B0C0F !important;
    color:#E6E6E6 !important;
    font-family:'Courier New',monospace !important;
}
hr {border-top:1px solid #2C313A !important;}
[data-testid="stSidebar"] {background-color:#0B0C0F !important;}
.stMarkdown, label, span, p {color:#D9D9D9 !important;}

/* Header */
h1,h2,h3,h4,h5 {
    color:#E63946 !important;
    text-align:center !important;
    letter-spacing:.08em;
    font-weight:700 !important;
}

/* Chat area */
.chat-box {
    background:#12161E;
    border:1px solid #1C232C;
    border-radius:8px;
    padding:16px 18px;
    height:260px;
    overflow-y:auto;
}

/* Buttons */
.stButton>button {
    background:#E63946 !important;
    color:#fff !important;
    border:none !important;
    border-radius:6px !important;
    font-weight:600 !important;
    height:38px !important;
    box-shadow:0 0 6px rgba(230,57,70,0.25);
    transition:all .2s ease-in-out;
}
.stButton>button:hover {
    background:#FF465A !important;
    box-shadow:0 0 14px rgba(255,70,90,0.45);
}

/* Inputs */
textarea, input, select, [data-baseweb="input"], [data-baseweb="textarea"] {
    background:#1E232B !important;
    color:#F8F8F8 !important;
    border:1px solid #2C313A !important;
    border-radius:6px !important;
}
.stSelectbox div[role="combobox"] {
    background:#1E232B !important;
    color:#E63946 !important;
}

/* Alignment */
.centered {text-align:center;}
</style>
""", unsafe_allow_html=True)

# ---------- INTRO ----------
if not st.session_state.get("entry_done", False):
    st.markdown("""
    <style>
    @keyframes fadeOut {0%{opacity:1;}90%{opacity:0;}100%{opacity:0;visibility:hidden;}}
    #boot-seq {animation:fadeOut 1.6s ease-out 3.2s forwards;}
    </style>
    <div id="boot-seq" style="
        height:100vh;display:flex;flex-direction:column;
        justify-content:center;align-items:center;
        text-align:center;
        background:radial-gradient(circle at 50% 20%, #11131a 0%, #090a0c 80%);
        font-family:'Courier New',monospace;">
        <div style="font-size:42px;color:#E63946;letter-spacing:.10em;
                    font-weight:800;margin-bottom:12px;">SENTINEL</div>
        <div style="color:#A8B2BD;font-size:14px;margin-bottom:22px;">
            AUTHENTICATING SESSION…
        </div>
        <div style="margin-top:10px;color:#9AA6B1;font-size:13px;
                    text-align:left;line-height:1.7;">
            🛰 INITIALIZING NODES…<br>
            <span style="color:#48FFF7;">✅ STRATA NODE ONLINE</span><br>
            <span style="color:#48FFF7;">✅ DEALHAWK NODE ONLINE</span><br>
            <span style="color:#48FFF7;">✅ NEO NODE ONLINE</span><br>
            <span style="color:#48FFF7;">✅ PFNG NODE ONLINE</span><br>
            <span style="color:#48FFF7;">✅ CIPHER SECURE CHANNEL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(4.8)
    st.session_state["entry_done"] = True
    st.rerun()

# ---------- HEADER ----------
st.markdown("""
<div class="centered">
  <h2 style="margin-bottom:2px;">SENTINEL</h2>
  <div style="color:#A0A6AD;font-size:14px;">Autonomous Agents for Asymmetric Advantage</div>
</div>
<hr style="margin-top:6px;margin-bottom:18px;">
""", unsafe_allow_html=True)

# ---------- AGENT SELECTION ----------
col1, col2, col3 = st.columns([1,2,1])
with col2:
    agent = st.selectbox("Choose agent", ["strata","dealhawk","neo","proforma","cipher"])
st.caption("Research & intelligence for energy/decarbonization.")

# ---------- CHAT / RESPONSE WINDOW ----------
st.markdown('<div class="chat-box">No messages yet.</div>', unsafe_allow_html=True)

# ---------- PROMPT BOX ----------
st.text_area("Type your prompt:", placeholder=f"Ask {agent.capitalize()}…", height=90)

# ---------- BUTTON ROW ----------
bcol1, bcol2, bcol3 = st.columns([1.2,1,1])
with bcol1:
    st.button("🔁 Reset Session", use_container_width=True)
with bcol2:
    st.button("💬 Ask Agent", use_container_width=True)
with bcol3:
    st.button("➡ Send to DEALHAWK", use_container_width=True)
