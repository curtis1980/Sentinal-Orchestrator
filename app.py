# app.py — Sentinel v3.0
# -----------------------------------------------------------
# Adds: synchronized tagline animation, static footer,
# horizontal "processing" bar, and restored prompting guide.

import io, os, sys, json, time, subprocess
from datetime import datetime
import streamlit as st

try: import pdfplumber
except: pdfplumber=None
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE=True
except: OCR_AVAILABLE=False
try: from docx import Document
except: Document=None

st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
:root {
  --bg:#121212; --surface:#171A1F; --card:#1E232B;
  --text:#F8F8F8; --muted:#A0A6AD; --accent:#E63946; --border:#2C313A;
}

/* Remove Streamlit top bar */
[data-testid="stHeader"], header, body > header {display:none!important;}
[data-testid="stToolbar"] {display:none!important;}
html, body {margin:0!important; padding:0!important; overflow-x:hidden!important;}

/* Base background */
[data-testid="stAppViewContainer"], html, body {
  background-color: var(--bg)!important;
  background-image:
    radial-gradient(#00000022 1px, transparent 1px),
    linear-gradient(180deg, #0f0f0f 0%, #171717 100%);
  background-size: 18px 18px, 100% 100%;
  color:var(--text)!important;
  font-family:'Courier New', monospace;
}

.block-container {padding-top:0.25rem; padding-bottom:6rem; margin-top:-20px;}

/* Header */
.header-container {
  text-align:center;
  margin-top:10px;
  margin-bottom:8px;
  font-family:'Courier New', monospace;
}
.typewriter-title {
  display:inline-block; overflow:hidden; white-space:nowrap;
  color:var(--accent); font-weight:700; font-size:46px; letter-spacing:.08em;
  animation:typingTitle 2.4s steps(30,end) forwards;
}
.typewriter-tagline {
  opacity:0; display:block; white-space:nowrap;
  color:var(--muted); font-size:14px; letter-spacing:.06em;
  margin-top:6px; animation:fadeInTag 1.6s ease forwards;
  animation-delay:2.5s;
}
@keyframes typingTitle {from{width:0} to{width:100%}}
@keyframes fadeInTag {from{opacity:0} to{opacity:1}}

/* Textarea hover */
.stTextArea textarea {
  background:var(--surface); color:var(--text);
  border:1px solid var(--border); border-radius:8px; height:80px;
  caret-color:var(--text); transition:all .2s ease;
}
.stTextArea textarea:hover {
  border-color:#8B0000; box-shadow:0 0 8px #8B000033;
}

/* Buttons */
.stButton>button {
  background:var(--accent); color:#fff; border:0; border-radius:8px;
  height:38px; font-weight:600; transition:all 0.15s ease;
}
.stButton>button:hover {filter:brightness(1.12); transform:translateY(-1px);}

/* Chat area */
.chat-wrap {background:var(--card); border:1px solid var(--border);
  border-radius:12px; padding:16px 18px; height:64vh; overflow-y:auto;}
.chat-wrap:empty{display:none!important;}
.chat-bubble{background:rgba(32,37,44,.95); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px; padding:12px 14px;
  margin:10px 0; line-height:1.55; color:var(--text)!important; animation:fadeIn .3s ease;}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}

/* Static footer */
.static-footer {
  position:fixed; bottom:0; left:0; right:0;
  background:var(--surface); border-top:2px solid var(--accent);
  box-shadow:0 -3px 12px rgba(0,0,0,.4); z-index:9999;
}
.footer-inner {
  max-width:1100px; margin:0 auto; padding:10px 16px;
  display:flex; flex-direction:row; align-items:flex-end; gap:10px;
}

/* Progress bar */
.progress-bar {
  position:absolute; top:0; left:0; height:3px;
  background:var(--accent); width:0; animation:scan 2s linear infinite;
}
@keyframes scan {
  0%{left:-50%; width:50%;}
  50%{left:25%; width:50%;}
  100%{left:100%; width:0;}
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class="header-container">
  <div class="typewriter-title">SENTINEL</div>
  <div class="typewriter-tagline">Autonomous Agents for Asymmetric Advantage</div>
</div>
<hr/>
""", unsafe_allow_html=True)

# ---------- Session State ----------
defaults = {"threads":{}, "context":"", "last_agent":"strata", "is_running":False, "prompt":"", "next_agent":"dealhawk"}
for k,v in defaults.items(): st.session_state.setdefault(k,v)

AGENTS = {
  "strata":"Research & intelligence for energy/decarbonization.",
  "dealhawk":"Deal sourcing for profitable private companies.",
  "neo":"Financial modeling and scenario analysis.",
  "proforma":"Critical review and risk calibration (PFNG).",
  "cipher":"IC assembly and governance validation."
}
AGENT_SEQUENCE = list(AGENTS.keys())
for a in AGENTS: st.session_state["threads"].setdefault(a,[])

def _recompute_next():
  curr = st.session_state["last_agent"]
  try: i = AGENT_SEQUENCE.index(curr)
  except: i=0
  st.session_state["next_agent"] = AGENT_SEQUENCE[i+1] if i+1 < len(AGENT_SEQUENCE) else None

# ---------- Sidebar ----------
st.sidebar.markdown("### ⚙️ Orchestrator")
agent = st.sidebar.selectbox("Choose agent", AGENT_SEQUENCE, index=AGENT_SEQUENCE.index(st.session_state["last_agent"]))
st.session_state["last_agent"]=agent
_recompute_next()
st.sidebar.caption(AGENTS[agent])
files = st.sidebar.file_uploader("📎 Upload files (PDF/DOCX)", type=["pdf","docx"], accept_multiple_files=True)

def _pdf_text(b):
    if not pdfplumber: return ""
    try:
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except: return ""

def _docx_text(b):
    if not Document: return ""
    try:
        doc=Document(io.BytesIO(b)); return "\n".join(p.text for p in doc.paragraphs)
    except: return ""

if files:
    t=[]
    for f in files:
        data=f.getvalue()
        txt=_pdf_text(data) if f.name.endswith(".pdf") else _docx_text(data)
        if txt:t.append(txt)
    st.session_state["context"]=("\n\n".join(t))[:10000]

if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    st.session_state.clear(); st.rerun()

# ---------- Helper ----------
def _compose(user_q:str)->str:
    ctx=st.session_state.get("context","").strip()
    prior=st.session_state["threads"][agent][-5:]
    mem="\n".join(f"{m['agent'].upper()}: {m['response'][:400]}" for m in prior)
    base=user_q
    if ctx: base=f"Context:\n{ctx}\n\n{base}"
    if mem: base=f"Recent Discussion:\n{mem}\n\n{base}"
    return base

# ---------- Agent Call ----------
def run_agent(agent_key, query):
    if st.session_state.get("is_running"): return
    st.session_state["is_running"]=True
    composed=_compose(query)
    output=""; is_error=False
    st.toast(f"🛰 Accessing {agent_key.upper()}...", icon="🔴")

    try:
        res=subprocess.run(["python","sentinal_orchestrator.py",agent_key,composed],
                           capture_output=True,text=True,timeout=90)
        output=(res.stdout or res.stderr or "").strip()
    except Exception as e:
        output=f"⚠️ Error: {e}"; is_error=True

    st.session_state["threads"][agent_key].append({
        "agent":agent_key,"query":query,"response":output,
        "time":datetime.now().strftime("%H:%M:%S"),"error":is_error})
    st.session_state["is_running"]=False
    st.rerun()

# ---------- Chat Area ----------
thread=st.session_state["threads"][agent]
if thread:
    st.markdown('<div class="chat-wrap">',unsafe_allow_html=True)
    for m in thread[-12:]:
        st.markdown(f"""
        <div class="chat-bubble">
        <b>{m['agent'].upper()}</b><br>{m['response'].replace(chr(10),'<br>')}
        <div class="meta">⏱ {m['time']}</div>
        </div>""",unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
st.markdown("<div style='height:36px'></div>",unsafe_allow_html=True)

# ---------- Static Footer ----------
st.markdown("<div class='static-footer'><div class='progress-bar' id='prog'></div><div class='footer-inner'>",unsafe_allow_html=True)
col1,col2,col3=st.columns([5,2,2])
with col1:
    st.session_state["prompt"]=st.text_area("Type your prompt:", value=st.session_state["prompt"], key="prompt_box", placeholder=f"Ask {agent.capitalize()}…", height=80)
with col2:
    ask_btn=st.button("💬 Ask Agent", use_container_width=True)
with col3:
    nxt=st.session_state["next_agent"]
    send_btn=st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next", use_container_width=True, disabled=(nxt is None))
st.markdown("</div></div>",unsafe_allow_html=True)

if st.session_state["is_running"]:
    st.markdown("<script>document.getElementById('prog').style.width='100%';</script>",unsafe_allow_html=True)
else:
    st.markdown("<script>document.getElementById('prog').style.width='0';</script>",unsafe_allow_html=True)

user_q=(st.session_state["prompt"] or "").strip()
if ask_btn and user_q: run_agent(agent,user_q)
elif send_btn and nxt:
    if st.session_state["threads"][agent]:
        last=st.session_state["threads"][agent][-1]["response"]
        run_agent(nxt,last)
    else: st.warning("No prior output to send.")

# ---------- Overview ----------
with st.expander("🧠 Sentinel Agent Overview — Roles & Prompting Guide", expanded=False):
    st.markdown("""
**SENTINEL** coordinates autonomous agents for private-market intelligence and decision analysis across energy transition & industrials.  
Each agent can be refined with iterative questioning before hand-off.

### 🛰 **STRATA** — Market Mapping  
- *Purpose:* Identify key sub-themes, technologies, and companies.  
- *Try:* “Map emerging U.S. midstream decarbonization subsectors.”  

### 🦅 **DEALHAWK** — Deal Sourcing  
- *Purpose:* Source and profile private, profitable companies.  
- *Try:* “Find five late-stage private grid-modernization firms in Texas.”  

### 🧮 **NEO** — Financial Modeling  
- *Purpose:* Turn insights into model assumptions and pro formas.  
- *Try:* “Translate Strata’s findings into a base case P&L for 2025–2030.”  

### ⚖️ **PRO FORMA NON GRATA (PFNG)** — Critical Review  
- *Purpose:* Stress-test assumptions, assign risk scores.  
- *Try:* “Challenge the model: what are three counterfactual risk cases?”  

### 🔐 **CIPHER** — IC Compilation  
- *Purpose:* Build IC memo and governance alignment.  
- *Try:* “Assemble a structured IC summary based on Neo’s and PFNG’s outputs.”  
""")
