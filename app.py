# app.py — Sentinel v3.1 (Chain-Stable)
# -----------------------------------------------------------
# Fixes Send→Next handoff (summary + size cap), adds status chip,
# retry on agent calls, and keeps the espionage UI intact.

import io, os, sys, json, time, subprocess, re
from datetime import datetime
import streamlit as st

# ---------- Optional parsers ----------
try: import pdfplumber
except Exception: pdfplumber=None
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE=True
except Exception: OCR_AVAILABLE=False
try: from docx import Document
except Exception: Document=None

# ---------- Page config ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
:root { --bg:#121212; --surface:#171A1F; --card:#1E232B;
  --text:#F8F8F8; --muted:#A0A6AD; --accent:#E63946; --border:#2C313A; }

/* Remove Streamlit chrome */
[data-testid="stHeader"], header, body > header, [data-testid="stToolbar"]{display:none!important;}
html, body {margin:0!important; padding:0!important; overflow-x:hidden!important;}

/* Background */
[data-testid="stAppViewContainer"], html, body{
  background-color:var(--bg)!important;
  background-image: radial-gradient(#00000022 1px, transparent 1px), linear-gradient(180deg,#0f0f0f 0%, #171717 100%);
  background-size:18px 18px, 100% 100%;
  color:var(--text)!important; font-family:'Courier New', monospace;
}
.block-container{padding-top:0.25rem; padding-bottom:6rem; margin-top:-20px;}

/* Sidebar */
[data-testid="stSidebar"]{background-color:#15181c; border-right:1px solid var(--border); padding:1rem 1rem 1.25rem;}
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label{color:var(--accent)!important; font-weight:600;}

/* Upload */
[data-testid="stFileUploader"] label, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] p{color:#e6e6e6!important; font-weight:500;}
[data-testid="stFileUploader"] svg{color:var(--accent)!important; opacity:.9;}
[data-testid="stFileUploaderFileName"]{color:#f5f5f5!important; font-weight:600;}
[data-testid="stFileUploaderFileDetails"]{color:#d0d0d0!important;}

/* Inputs */
.stTextArea textarea{background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:8px; height:80px; caret-color:var(--text); transition:all .2s;}
.stTextArea textarea:hover{border-color:#8B0000; box-shadow:0 0 8px #8B000033;}
.stButton>button{background:var(--accent); color:#fff; border:0; border-radius:8px; height:38px; font-weight:600; transition:all .15s;}
.stButton>button:hover{filter:brightness(1.12); transform:translateY(-1px);}
.stButton>button:disabled{opacity:.6; cursor:not-allowed; transform:none;}

/* Chat */
.chat-wrap{background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px 18px; height:64vh; overflow-y:auto;}
.chat-wrap:empty{display:none!important;}
.chat-bubble{background:rgba(32,37,44,.95); border:1px solid var(--border); border-left:4px solid var(--accent); border-radius:10px; padding:12px 14px; margin:10px 0; line-height:1.55; color:var(--text)!important; animation:fadeIn .3s ease;}
.meta{color:var(--muted); font-size:11px; margin-top:4px;}
@keyframes fadeIn{from{opacity:0; transform:translateY(4px);} to{opacity:1; transform:translateY(0);}}

/* Header */
.header-container{text-align:center; margin-top:10px; margin-bottom:8px; font-family:'Courier New', monospace;}
.typewriter-title{display:inline-block; overflow:hidden; white-space:nowrap; color:var(--accent); font-weight:700; font-size:46px; letter-spacing:.08em; animation:typingTitle 2.4s steps(30,end) forwards;}
.typewriter-tagline{opacity:0; display:block; white-space:nowrap; color:var(--muted); font-size:14px; letter-spacing:.06em; margin-top:6px; animation:fadeInTag 1.6s ease forwards; animation-delay:2.5s;}
@keyframes typingTitle{from{width:0} to{width:100%}}
@keyframes fadeInTag{from{opacity:0} to{opacity:1}}

/* Static footer */
.static-footer{position:fixed; bottom:0; left:0; right:0; background:var(--surface); border-top:2px solid var(--accent); box-shadow:0 -3px 12px rgba(0,0,0,.4); z-index:9999;}
.footer-inner{max-width:1100px; margin:0 auto; padding:10px 16px; display:flex; gap:10px; align-items:flex-end;}
/* Progress bar */
.progress-bar{position:absolute; top:0; left:0; height:3px; background:var(--accent); width:0; animation:scan 2s linear infinite;}
@keyframes scan{0%{left:-50%; width:50%;} 50%{left:25%; width:50%;} 100%{left:100%; width:0;}}

/* Status chip */
.status-chip{position:fixed; top:10px; right:14px; background:#1f242b; border:1px solid var(--border); color:#fff; padding:6px 10px; border-radius:999px; font-size:12px; box-shadow:0 2px 10px rgba(0,0,0,.25); z-index:10000;}
.status-dot{width:8px; height:8px; display:inline-block; border-radius:50%; background:var(--accent); margin-right:6px; animation:pulse 1.2s ease-in-out infinite;}
@keyframes pulse{0%,100%{opacity:.4} 50%{opacity:1}}
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

# ---------- Session ----------
defaults = {
    "threads":{}, "context":"", "last_agent":"strata",
    "is_running":False, "prompt":"", "next_agent":"dealhawk",
    "active_agent":None
}
for k,v in defaults.items(): st.session_state.setdefault(k,v)

AGENTS = {
  "strata":"Research & intelligence for energy/decarbonization.",
  "dealhawk":"Deal sourcing for profitable private companies.",
  "neo":"Financial modeling and scenario analysis.",
  "proforma":"Critical review and risk calibration (PFNG).",
  "cipher":"IC assembly and governance validation."
}
AGENT_SEQUENCE = ["strata","dealhawk","neo","proforma","cipher"]
for a in AGENTS: st.session_state["threads"].setdefault(a,[])

def _recompute_next():
    cur = st.session_state.get("last_agent","strata")
    try:
        i = AGENT_SEQUENCE.index(cur)
        st.session_state["next_agent"] = AGENT_SEQUENCE[i+1] if i+1 < len(AGENT_SEQUENCE) else None
    except ValueError:
        st.session_state["next_agent"] = None

# ---------- Sidebar ----------
st.sidebar.markdown("### ⚙️ Orchestrator")
agent = st.sidebar.selectbox("Choose agent", AGENT_SEQUENCE, index=AGENT_SEQUENCE.index(st.session_state["last_agent"]))
st.session_state["last_agent"] = agent
_recompute_next()
st.sidebar.caption(AGENTS[agent])
files = st.sidebar.file_uploader("📎 Upload files (PDF/DOCX)", type=["pdf","docx"], accept_multiple_files=True)

# ---------- Parsers ----------
def _pdf_text(b:bytes)->str:
    t=""
    if pdfplumber:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages: t += (p.extract_text() or "") + "\n"
        except Exception: pass
    if not t.strip() and OCR_AVAILABLE:
        try:
            imgs = convert_from_bytes(b, dpi=200)
            t = "\n".join(pytesseract.image_to_string(i) for i in imgs)
        except Exception: pass
    return t.strip()

def _docx_text(b:bytes)->str:
    if not Document: return ""
    try:
        doc = Document(io.BytesIO(b))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception: return ""

if files:
    chunks=[]
    for f in files[:3]:
        data = f.getvalue()
        txt = _pdf_text(data) if f.name.lower().endswith(".pdf") else _docx_text(data)
        if txt: chunks.append(txt)
    st.session_state["context"] = ("\n\n".join(chunks))[:10000]

if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    st.session_state.clear(); st.rerun()

# ---------- Helpers ----------
def _compose(user_q:str)->str:
    """Builds the prompt with context + last few assistant messages."""
    ctx = st.session_state.get("context","").strip()
    prior = st.session_state["threads"][agent][-5:]
    mem = "\n".join(f"{m['agent'].upper()}: {m['response'][:400]}" for m in prior)
    base = user_q
    if ctx: base = f"Context:\n{ctx}\n\n{base}"
    if mem: base = f"Recent Discussion:\n{mem}\n\n{base}"
    return base

def _extract_summary(resp:str, fallback_len:int=1600)->str:
    """Robust handoff: try JSON.summary → 'summary:' block → first N chars."""
    if not resp: return ""
    # Try JSON at end
    try:
        json_start = resp.rfind("{")
        if json_start != -1:
            parsed = json.loads(resp[json_start:])
            s = parsed.get("summary","")
            if isinstance(s,str) and s.strip(): return s.strip()
    except Exception:
        pass
    # Try markdown **Summary:** or heading
    m = re.search(r'(?i)(?:\*\*summary\*\*:|^#*\s*summary\s*:?)\s*(.+?)(?:\n\s*\n|$)', resp, re.S|re.M)
    if m: 
        s = m.group(1).strip()
        return s[:fallback_len]
    # Fallback: strip html-ish tags, take first N chars
    clean = re.sub(r'<[^>]+>','',resp).strip()
    return clean[:fallback_len]

def _cap(text:str, limit:int=8000)->str:
    """Cap payload to keep subprocess args safe on all OS."""
    if len(text) <= limit: return text
    return text[:limit-20] + " …[truncated]"

# ---------- Agent Runner ----------
def run_agent(agent_key: str, user_q: str):
    if st.session_state.get("is_running"): return
    if not agent_key or not user_q.strip(): return

    st.session_state["is_running"] = True
    st.session_state["active_agent"] = agent_key
    q = _compose(user_q)
    q = _cap(q, 8000)  # keep arg size safe

    # simple retry-once for transient errors
    attempts = 0
    output = ""; is_error = False
    while attempts < 2:
        attempts += 1
        try:
            res = subprocess.run(
                ["python","sentinal_orchestrator.py", agent_key, q],
                capture_output=True, text=True, check=False, timeout=120
            )
            output = (res.stdout or "").strip()
            errout = (res.stderr or "").strip()
            if not output and errout:
                output = errout
            if output: break
        except Exception as e:
            output = f"⚠️ Execution error: {e}"
            is_error = True
        time.sleep(0.6)  # backoff for retry

    # ensure threads map exists
    if "threads" not in st.session_state: st.session_state["threads"] = {}
    if agent_key not in st.session_state["threads"]: st.session_state["threads"][agent_key] = []

    st.session_state["threads"][agent_key].append({
        "agent": agent_key, "query": user_q, "response": output or "⚠️ No output received.",
        "time": datetime.now().strftime("%H:%M:%S"), "error": is_error or (not bool(output))
    })

    st.session_state["is_running"] = False
    st.session_state["active_agent"] = None
    st.rerun()

# ---------- Status Chip ----------
if st.session_state.get("is_running") and st.session_state.get("active_agent"):
    st.markdown(
        f"""<div class="status-chip"><span class="status-dot"></span>
        🛰 Accessing <b>{st.session_state['active_agent'].upper()}</b>…</div>""",
        unsafe_allow_html=True
    )

# ---------- Chat ----------
thread = st.session_state["threads"][agent]
if thread:
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for item in thread[-15:]:
        cleaned = item["response"]
        st.markdown(f"""
        <div class="chat-bubble">
            <b>{item['agent'].upper()}</b><br>{cleaned.replace(chr(10), '<br>')}
            <div class="meta">⏱ {item['time']}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)

# ---------- Static Footer (input + buttons) ----------
st.markdown("<div class='static-footer'><div class='progress-bar' id='prog'></div><div class='footer-inner'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([5,2,2])
with col1:
    st.session_state["prompt"] = st.text_area(
        "Type your prompt:", value=st.session_state["prompt"], key="prompt_box",
        placeholder=f"Ask {agent.capitalize()}…", height=80
    )
with col2:
    ask_btn = st.button("💬 Ask Agent", use_container_width=True, disabled=st.session_state["is_running"])
with col3:
    nxt = st.session_state.get("next_agent")
    send_btn = st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next", use_container_width=True,
                         disabled=(nxt is None or st.session_state["is_running"]))
st.markdown("</div></div>", unsafe_allow_html=True)

# progress bar toggle
if st.session_state["is_running"]:
    st.markdown("<script>document.getElementById('prog').style.width='100%';</script>", unsafe_allow_html=True)
else:
    st.markdown("<script>document.getElementById('prog').style.width='0';</script>", unsafe_allow_html=True)

# ---------- Actions ----------
user_q = (st.session_state["prompt"] or "").strip()
if ask_btn:
    if user_q:
        run_agent(agent, user_q); st.session_state["prompt"] = ""
    else:
        st.warning("Type a question first.")
elif send_btn and nxt:
    if st.session_state["threads"][agent]:
        last_resp = st.session_state["threads"][agent][-1]["response"]
        summary = _extract_summary(last_resp, fallback_len=1600)
        run_agent(nxt, summary or last_resp[:1600])
    else:
        st.warning("No output to pass forward from the current agent.")

# ---------- Overview (prompting guide) ----------
with st.expander("🧠 Sentinel Agent Overview — Roles & Prompting Guide", expanded=False):
    st.markdown("""
**SENTINEL** coordinates autonomous agents for private-market intelligence and decision analysis in energy transition & industrials.  
Iterate with each agent before handoff for cleaner context.

### 🧭 STRATA — Market Mapping  
**Best prompts**
- “Map the North American grid modernization ecosystem.”  
- “Break down the energy storage value chain by technology and stage.”  
**Output**: Markdown hierarchy + **Next Steps for Sourcing** (keywords, filters, sources).

### 🦅 DEALHAWK — Deal Sourcing  
**Best prompts**
- “Using the above filters, find 8–10 Canadian private companies in grid analytics.”  
- “Identify founder-led businesses in industrial electrification with EBITDA > 0.”  
**Output**: company table + **Top 3 to Advance**.

### 🧮 NEO — Financial Modeling  
**Best prompts**
- “Build a base vs. bull case for a battery recycling roll-up.”  
- “Estimate normalized EBITDA for a controls integrator.”  
**Output**: concise modeling narrative with drivers and scenarios.

### 📊 PRO FORMA NON GRATA (PFNG) — Critical Review  
**Best prompts**
- “Run PFNG on Neo’s summary; assign RIS and list counterfactuals.”  
- “Audit assumptions and identify where the numbers disagree with the story.”  
**Output**: **Critical Review Memo** with RIS and counterfactuals.

### 🔐 CIPHER — Orchestrator & IC Assembly  
**Modes**: `/strata`, `/dealhawk`, `/screen`, `/profile`  
**Best prompts**
- “/dealhawk using the above filters”  
- “/profile ArcLight Energy Systems Ltd”  
**Output**: Markdown-only reports with cited URLs + **Suggested Next Command**.
""")
