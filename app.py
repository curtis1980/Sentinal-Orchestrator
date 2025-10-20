# app.py — Sentinel v3.1.7 (Unified Chat Layout)
# -----------------------------------------------------------
# Fixes ghost text area bug, unifies chat + input area, 
# aligns Ask/Send buttons, brightens agent guide, fixes Send→Next logic.

import io, os, json, time, subprocess, re
from datetime import datetime
import streamlit as st

# ---------- Optional parsers ----------
try: import pdfplumber
except Exception: pdfplumber = None
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False
try: from docx import Document
except Exception: Document = None

# ---------- Page Config ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
:root {
  --bg:#121212; --surface:#171A1F; --card:#1E232B;
  --text:#F8F8F8; --muted:#A0A6AD; --accent:#E63946; --border:#2C313A;
}

/* Hide Streamlit chrome */
[data-testid="stHeader"], [data-testid="stToolbar"], header, body > header {
  display:none !important;
}
html, body {margin:0!important; padding:0!important; overflow-x:hidden!important;}
[data-testid="stAppViewContainer"], html, body {
  background-color:var(--bg)!important;
  background-image:radial-gradient(#00000022 1px,transparent 1px),
                   linear-gradient(180deg,#0f0f0f 0%, #171717 100%);
  background-size:18px 18px,100% 100%;
  color:var(--text)!important;
  font-family:'Courier New', monospace;
}

/* Content */
.content-inner {
  max-width:1100px;
  margin:0 auto;
  padding:0 1.2rem 4rem;
}

/* Header */
.header-container{text-align:center;margin-top:10px;margin-bottom:8px;}
.typewriter-title {
  display:inline-block;overflow:hidden;white-space:nowrap;
  color:var(--accent);font-weight:700;font-size:46px;letter-spacing:.08em;
  animation:typingTitle 4.5s steps(40,end) forwards;
}
.typewriter-tagline {
  opacity:0;display:block;white-space:nowrap;color:var(--muted);
  font-size:14px;letter-spacing:.06em;margin-top:6px;
  animation:fadeInTag 1.6s ease forwards;animation-delay:4.7s;
}
@keyframes typingTitle {from{width:0} to{width:100%}}
@keyframes fadeInTag {from{opacity:0} to{opacity:1}}

/* Agent selector */
.agent-select {max-width:360px;}
.version-label {color:var(--muted);font-size:12px;text-align:right;}

/* Chat */
.chat-container {
  background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:16px 18px;height:60vh;
  overflow-y:auto;margin:12px 0;
}
.chat-bubble {
  background:rgba(32,37,44,.95);border:1px solid var(--border);
  border-left:4px solid var(--accent);border-radius:10px;
  padding:12px 14px;margin:10px 0;line-height:1.55;color:var(--text)!important;
  animation:fadeIn .3s ease;
}
.chat-bubble.error-bubble{border-left:4px solid #FFB703;background:#2a1c1c;}
.meta{color:var(--muted);font-size:11px;margin-top:4px;}
.placeholder{color:var(--muted);font-style:italic;text-align:center;margin-top:22vh;}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}

/* Input */
.stTextArea textarea {
  background:var(--surface);color:var(--text);
  border:1px solid var(--border);border-radius:8px;height:92px;
  caret-color:var(--text);transition:all .2s ease;
}
.stTextArea textarea:hover {border-color:#8B0000;box-shadow:0 0 8px #8B000033;}
.buttons-row {display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px;}
.buttons-row .stButton>button {
  background:var(--accent);color:#fff;border:0;border-radius:8px;
  height:40px;font-weight:600;transition:all .15s ease;
}
.buttons-row .stButton>button:hover {filter:brightness(1.12);transform:translateY(-1px);}
.buttons-row .stButton>button:disabled {opacity:.6;cursor:not-allowed;transform:none;}

/* Overview styling */
.agent-guide h3 {color:#fff;}
.agent-guide strong {color:#fff;}
.agent-guide p {color:#CFCFCF;line-height:1.5;}
.agent-guide li {color:#CFCFCF;}
.agent-guide .emoji {font-size:18px;margin-right:6px;}

/* Status */
.status-chip {position:fixed;top:10px;right:14px;background:#1f242b;
  border:1px solid var(--border);color:#fff;padding:6px 10px;border-radius:999px;
  font-size:12px;box-shadow:0 2px 10px rgba(0,0,0,.25);z-index:10000;}
.status-dot {width:8px;height:8px;display:inline-block;border-radius:50%;
  background:var(--accent);margin-right:6px;animation:pulse 1.2s ease-in-out infinite;}
@keyframes pulse {0%,100%{opacity:.4}50%{opacity:1}}
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
defaults = {
  "threads":{}, "context":"", "last_agent":"strata", "next_agent":"dealhawk",
  "is_running":False, "active_agent":None, "prompt":""
}
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
  cur = st.session_state.get("last_agent","strata")
  try:
      i = AGENT_SEQUENCE.index(cur)
      st.session_state["next_agent"] = AGENT_SEQUENCE[i+1] if i+1 < len(AGENT_SEQUENCE) else None
  except ValueError:
      st.session_state["next_agent"] = None

# ---------- Helpers ----------
def _compose(user_q:str)->str:
  ctx=(st.session_state.get("context") or "").strip()
  prior=st.session_state["threads"][agent][-5:]
  mem="\n".join(f"{m['agent'].upper()}: {m['response'][:400]}" for m in prior)
  base=user_q
  if ctx: base=f"Context:\n{ctx}\n\n{base}"
  if mem: base=f"Recent Discussion:\n{mem}\n\n{base}"
  return base

def _extract_summary(resp:str,fallback_len:int=1600)->str:
  if not resp: return ""
  try:
      js=resp.rfind("{")
      if js!=-1:
          parsed=json.loads(resp[js:])
          s=parsed.get("summary","")
          if isinstance(s,str) and s.strip(): return s.strip()[:fallback_len]
  except: pass
  m=re.search(r'(?i)(?:\\*\\*summary\\*\\*:|^#*\\s*summary\\s*:?)\\s*(.+?)(?:\\n\\s*\\n|$)',resp,re.S|re.M)
  if m: return m.group(1).strip()[:fallback_len]
  clean=re.sub(r'<[^>]+>','',resp).strip()
  return clean[:fallback_len]

def _cap(t:str,limit:int=8000)->str: return t if len(t)<=limit else t[:limit-20]+" …[truncated]"

# ---------- Main Layout ----------
st.markdown("<div class='content-inner'>", unsafe_allow_html=True)

# Top control bar
col1, col2 = st.columns([4,1])
with col1:
    agent = st.selectbox("Choose agent", AGENT_SEQUENCE, index=AGENT_SEQUENCE.index(st.session_state["last_agent"]),
                         key="agent_select", label_visibility="visible")
    st.session_state["last_agent"]=agent
    _recompute_next()
    st.caption(AGENTS[agent])
with col2:
    st.markdown("<div class='version-label'>v3.1.7</div>", unsafe_allow_html=True)

# ---------- Chat Container ----------
chat_box = st.container()
with chat_box:
    thread = st.session_state["threads"][agent]
    if thread:
        st.markdown('<div class="chat-container" id="chatwrap">', unsafe_allow_html=True)
        for m in thread[-18:]:
            klass = "chat-bubble error-bubble" if m.get("error") else "chat-bubble"
            st.markdown(f"""
            <div class="{klass}">
              <b>{m['agent'].upper()}</b><br>{m['response'].replace(chr(10),'<br>')}
              <div class="meta">⏱ {m['time']}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="chat-container"><div class="placeholder">No messages yet.</div></div>', unsafe_allow_html=True)

# ---------- Input Section ----------
st.session_state["prompt"] = st.text_area(
    "Type your prompt:", value=st.session_state.get("prompt",""), key="prompt_box",
    placeholder=f"Ask {agent.capitalize()}…", height=92
)

colA, colB = st.columns(2)
with colA:
    ask_btn = st.button("💬 Ask Agent", use_container_width=True, disabled=st.session_state.get("is_running",False))
with colB:
    nxt = st.session_state.get("next_agent")
    send_btn = st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next",
                         use_container_width=True,
                         disabled=(nxt is None or st.session_state.get("is_running",False)))

# ---------- Agent Runner ----------
def run_agent(agent_key:str, user_q:str):
    if not user_q.strip() or st.session_state.get("is_running"): return
    st.session_state["is_running"]=True
    st.session_state["active_agent"]=agent_key
    st.toast(f"🛰 Accessing {agent_key.upper()}...", icon="🔴")

    composed=_cap(_compose(user_q),8000)
    attempts,output,is_error=0,"",False
    while attempts<2:
        attempts+=1
        try:
            res=subprocess.run(["python","sentinal_orchestrator.py",agent_key,composed],
                               capture_output=True,text=True,timeout=120)
            output=(res.stdout or res.stderr or "").strip()
            if output: break
        except Exception as e:
            output=f"⚠️ Execution error: {e}"; is_error=True
        time.sleep(0.6)
    st.session_state["threads"][agent_key].append({
        "agent":agent_key,"query":user_q,"response":output or "⚠️ No output received.",
        "time":datetime.now().strftime("%H:%M:%S"),"error":is_error or (not bool(output))
    })
    st.session_state["is_running"]=False
    st.session_state["active_agent"]=None
    st.rerun()

# ---------- Button Logic ----------
user_q = (st.session_state.get("prompt") or "").strip()
if ask_btn:
    run_agent(agent,user_q)
    st.session_state["prompt"]=""
elif send_btn and nxt:
    if st.session_state["threads"][agent]:
        last=st.session_state["threads"][agent][-1]["response"]
        summary=_extract_summary(last)
        st.session_state["last_agent"]=nxt
        _recompute_next()
        run_agent(nxt, summary or last[:1600])
    else:
        st.warning("No output to pass forward from the current agent.")

# ---------- Context Upload ----------
with st.expander("📎 Attach Context (PDF/DOCX)", expanded=False):
    uploads = st.file_uploader("Upload files", type=["pdf","docx"], accept_multiple_files=True)
    def _pdf_text(b): 
        txt=""; 
        if pdfplumber:
            try:
                with pdfplumber.open(io.BytesIO(b)) as pdf:
                    for p in pdf.pages: txt+=(p.extract_text() or "")+"\\n"
            except: pass
        if not txt.strip() and OCR_AVAILABLE:
            try:
                imgs=convert_from_bytes(b,dpi=200)
                txt="\\n".join(pytesseract.image_to_string(i) for i in imgs)
            except: pass
        return txt.strip()
    def _docx_text(b):
        if not Document: return ""
        try:
            doc=Document(io.BytesIO(b))
            return "\\n".join(p.text for p in doc.paragraphs)
        except: return ""
    if uploads:
        chunks=[]
        for f in uploads[:3]:
            data=f.getvalue()
            txt=_pdf_text(data) if f.name.lower().endswith(".pdf") else _docx_text(data)
            if txt: chunks.append(txt)
        st.session_state["context"]=("\\n\\n".join(chunks))[:10000]
        st.success("Context attached successfully.")

# ---------- Agent Guide ----------
with st.expander("🧠 Sentinel Agent Overview — Roles & Prompting Guide", expanded=False):
    st.markdown("""
<div class="agent-guide">
<b>SENTINEL</b> coordinates autonomous agents for private-market intelligence and decision analysis across energy transition & industrials.

### 🧭 <span class="emoji">🧭</span> <strong>STRATA — Market Mapping</strong>
<p>“Map emerging U.S. midstream decarbonization subsectors.”</p>

### 🦅 <span class="emoji">🦅</span> <strong>DEALHAWK — Deal Sourcing</strong>
<p>“Find five late-stage private grid-modernization firms in Texas.”</p>

### 🧮 <span class="emoji">🧮</span> <strong>NEO — Financial Modeling</strong>
<p>“Translate Strata’s findings into a base-case P&L for 2025–2030.”</p>

### ⚖️ <span class="emoji">⚖️</span> <strong>PRO FORMA NON GRATA (PFNG)</strong>
<p>“Run PFNG on Neo’s summary; assign RIS and counterfactuals.”</p>

### 🔐 <span class="emoji">🔐</span> <strong>CIPHER — IC Assembly</strong>
<p>“/profile ArcLight Energy Systems Ltd.”</p>
</div>
""", unsafe_allow_html=True)

# ---------- Auto-scroll ----------
st.markdown("""
<script>
const el=window.parent.document.querySelector('#chatwrap');
if(el){el.scrollTo({top:el.scrollHeight, behavior:'smooth'});}
</script>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
