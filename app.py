# app.py — Sentinel v2.9 (Render Stable Build)
# --------------------------------------------
# Longbow Capital | Sentinel Platform
# Autonomous Agents for Asymmetric Advantage
#
# ✅ Stable dark UI (dot-grid background)
# ✅ Typewriter header (Courier New)
# ✅ Correct chain order (Strata → Dealhawk → Neo → Pro Forma → Cipher)
# ✅ Guarded subprocess call (prevents startup crash)
# ✅ Render-ready (no flashing grey screen)
# ✅ Health-safe minimal boot output
# ✅ PDF/DOCX parsing and iterative agent chat

import io, os, sys, json, time, subprocess
from datetime import datetime
import streamlit as st

# --- Sentinel startup diagnostics ---
def log(msg):
    print(f"[Sentinel Boot] {msg}", flush=True)

log("Initializing Sentinel app.py ...")

# ---------- Optional parsers ----------
try:
    import pdfplumber
    from pdf2image import convert_from_bytes
    import pytesseract
    from docx import Document
    OCR_AVAILABLE = True
    log("✅ All parsers loaded successfully.")
except Exception as e:
    OCR_AVAILABLE = False
    log(f"⚠️ Parser import warning: {e}")

# ---------- Page config ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
:root {
  --bg:#121212; --surface:#171A1F; --card:#1E232B;
  --text:#F8F8F8; --muted:#A0A6AD; --accent:#E63946; --border:#2C313A;
}
[data-testid="stAppViewContainer"], html, body {
  background-color: var(--bg)!important;
  background-image:
    radial-gradient(#00000022 1px, transparent 1px),
    linear-gradient(180deg, #0f0f0f 0%, #171717 100%);
  background-size: 18px 18px, 100% 100%;
  color:var(--text)!important;
  font-family:'Courier New', monospace;
}
.block-container{padding-top:0.25rem; padding-bottom:5.5rem; background-color:transparent!important;}
[data-testid="stSidebar"]{
  background-color:#15181c; border-right:1px solid var(--border);
  padding:1rem 1rem 1.25rem 1rem;
}
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label{
  color:var(--accent)!important; font-weight:600;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p{
  color:#e6e6e6!important; font-weight:500;
}
[data-testid="stFileUploader"] svg{
  color:var(--accent)!important; opacity:0.9;
}
[data-testid="stFileUploaderFileName"]{color:#f5f5f5!important; font-weight:600;}
[data-testid="stFileUploaderFileDetails"]{color:#d0d0d0!important;}
.stTextArea textarea{
  background:var(--surface); color:var(--text);
  border:1px solid var(--border); border-radius:8px; height:80px;
  caret-color: var(--text);
  transition: all 0.2s ease;
}
.stTextArea textarea:hover{
  border-color: #8B0000; box-shadow: 0 0 8px #8B000033;
}
.stButton>button{
  background:var(--accent); color:#fff; border:0; border-radius:8px;
  height:38px; font-weight:600;
}
.stButton>button:hover{ filter:brightness(1.12); }
.chat-wrap{
  background:var(--card); border:1px solid var(--border);
  border-radius:12px; padding:16px 18px; height:64vh; overflow-y:auto;
}
.chat-wrap:empty{display:none!important;}
.chat-bubble{
  background:rgba(32,37,44,.95); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px;
  padding:12px 14px; margin:10px 0; line-height:1.55;
  color:var(--text)!important; animation:fadeIn .3s ease;
}
.meta{color:var(--muted); font-size:11px; margin-top:4px;}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}
.static-footer{position:fixed; left:0; right:0; bottom:0;
  background:var(--surface); border-top:2px solid var(--accent);
  box-shadow:0 -3px 12px rgba(0,0,0,.4); z-index:9999;}
.footer-inner{max-width:1100px; margin:0 auto; padding:10px 16px;
  display:flex; gap:10px; align-items:flex-end;}
.footer-left{flex:1;} .footer-right{width:300px; display:flex; flex-direction:column; gap:8px;}
.header-container{text-align:center; margin-top:20px; margin-bottom:12px; font-family:'Courier New', monospace;}
.typewriter-title{display:inline-block; overflow:hidden; white-space:nowrap;
  border-right:.15em solid var(--accent); color:var(--accent);
  font-weight:700; font-size:46px; letter-spacing:.08em;
  animation:typingTitle 2.6s steps(30,end), blink-caret .75s step-end infinite;
  animation-fill-mode:forwards;}
.typewriter-tagline{display:block; overflow:hidden; white-space:nowrap;
  border-right:.15em solid var(--accent); color:var(--muted);
  font-size:14px; letter-spacing:.06em; margin-top:6px;
  animation:typingTag 3.4s steps(40,end) 2.8s, blink-caret .75s step-end infinite 2.8s;
  animation-fill-mode:forwards;}
@keyframes typingTitle{from{width:0}to{width:100%}}
@keyframes typingTag{from{width:0}to{width:100%}}
@keyframes blink-caret{from,to{border-color:transparent}50%{border-color:var(--accent);}}
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

# ---------- Session state ----------
defaults = {"threads":{}, "context":"", "last_agent":"strata", "is_running":False, "prompt":"", "next_agent":"dealhawk"}
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
    current = st.session_state.get("last_agent", "strata")
    try:
        idx = AGENT_SEQUENCE.index(current)
        st.session_state["next_agent"] = AGENT_SEQUENCE[idx + 1] if idx + 1 < len(AGENT_SEQUENCE) else None
    except ValueError:
        st.session_state["next_agent"] = None

# ---------- Sidebar ----------
st.sidebar.markdown("### ⚙️ Orchestrator")
agent = st.sidebar.selectbox("Choose agent", AGENT_SEQUENCE, index=AGENT_SEQUENCE.index(st.session_state["last_agent"]))
st.session_state["last_agent"] = agent
_recompute_next()
st.sidebar.caption(AGENTS[agent])
st.sidebar.markdown("---")
files = st.sidebar.file_uploader("📎 Upload files (PDF/DOCX)", type=["pdf","docx"], accept_multiple_files=True)

def _pdf_text(b):
    t=""
    if pdfplumber:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages: t+=(p.extract_text() or "")+"\n"
        except: pass
    if not t.strip() and OCR_AVAILABLE:
        try:
            imgs=convert_from_bytes(b,dpi=200)
            t="\n".join(pytesseract.image_to_string(i) for i in imgs)
        except: pass
    return t.strip()

def _docx_text(b):
    if not 'Document' in globals(): return ""
    try:
        doc=Document(io.BytesIO(b)); return "\n".join(p.text for p in doc.paragraphs)
    except: return ""

if files:
    texts=[]
    for f in files[:3]:
        data=f.getvalue()
        parsed=_pdf_text(data) if f.name.lower().endswith(".pdf") else _docx_text(data)
        if parsed:texts.append(parsed)
    st.session_state["context"]=("\n\n".join(texts))[:10000]

if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    st.session_state.clear(); st.rerun()

# ---------- Helper ----------
def _compose(user_q:str)->str:
    ctx=st.session_state.get("context","").strip()
    prior=st.session_state["threads"][agent][-10:]
    mem="\n".join(f"ASSISTANT: {m['response']}" for m in prior[-5:])
    base=user_q
    if ctx: base=f"Context:\n{ctx}\n\nUser Query:\n{base}"
    if mem: base=f"Conversation:\n{mem}\n\n{base}"
    return base

# ---------- Agent Runner ----------
def run_agent(agent_key: str, user_q: str):
    """Safely run the orchestrator subprocess."""
    if st.session_state.get("is_running"):
        return
    if not agent_key or not user_q.strip():
        print("[Sentinel] ⚠️ Skipping subprocess call — missing agent or query.")
        return

    st.session_state["is_running"] = True
    q = _compose(user_q)
    output = ""
    is_error = False

    st.toast(f"Routing to agent: {agent_key.upper()}...", icon="🛰️")
    print(f"[Sentinel] 🛰️ Running agent {agent_key} with query length {len(q)}")

    try:
        res = subprocess.run(
            ["python", "sentinal_orchestrator.py", agent_key, q],
            capture_output=True,
            text=True,
            check=False,
            timeout=90
        )
        output = (res.stdout or "").strip() or (res.stderr or "").strip()
    except Exception as e:
        output = f"⚠️ Execution error: {e}"
        is_error = True

    if "threads" not in st.session_state:
        st.session_state["threads"] = {}
    if agent_key not in st.session_state["threads"]:
        st.session_state["threads"][agent_key] = []
    st.session_state["threads"][agent_key].append({
        "agent": agent_key,
        "query": user_q,
        "response": output,
        "time": datetime.now().strftime("%H:%M:%S"),
        "error": is_error
    })
    st.session_state["is_running"] = False
    st.rerun()

# ---------- Chat Display ----------
thread = st.session_state["threads"][agent]
if thread:
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for item in thread[-15:]:
        css_extra = " error" if item.get("error") else ""
        cleaned = item["response"]
        st.markdown(f"""
        <div class="chat-bubble{css_extra}">
            <b>{item['agent'].upper()}</b><br>{cleaned.replace(chr(10), '<br>')}
            <div class="meta">⏱ {item['time']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("🛰️ Sentinel ready — choose an agent and enter a prompt below.")

# ---------- Footer ----------
st.markdown("""
<div class='static-footer'><div class='footer-inner'>
  <div class='footer-left'></div><div class='footer-right'></div>
</div></div>
""", unsafe_allow_html=True)

left,right=st.empty(),st.empty()
with left.container():
    st.session_state["prompt"]=st.text_area("Type your prompt here:",
        value=st.session_state["prompt"], key="prompt_box",
        placeholder=f"Ask {agent.capitalize()}…", height=80)
with right.container():
    ask_btn=st.button("💬 Ask Agent", use_container_width=True)
    nxt=st.session_state.get("next_agent")
    send_next_btn=st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next Agent",
                            use_container_width=True, disabled=(nxt is None))

user_q=(st.session_state["prompt"] or "").strip()
if ask_btn:
    if user_q:
        run_agent(agent, user_q); st.session_state["prompt"]=""
    else:
        st.warning("Type a question first.")
elif send_next_btn and nxt:
    if st.session_state["threads"][agent]:
        last_resp = st.session_state["threads"][agent][-1]["response"]
        summary = last_resp[:5000]
        time.sleep(0.4)
        run_agent(nxt, summary)
    else:
        st.warning("No output to pass forward from the current agent.")

log("✅ Sentinel app fully initialized.")
