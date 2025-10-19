# app.py — Sentinel Beta v2.1
# ---------------------------------------
# - Typewriter "SENTINEL" header (intel aesthetic)
# - Visible red input caret
# - Conversational per-agent threads
# - All 5 agents wired (strata → dealhawk → neo → cipher → proforma)
# - OCR-safe PDF/DOCX parsing

import io, os, time, subprocess
from datetime import datetime
import streamlit as st

# ---------- OPTIONAL PARSERS ----------
try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

from docx import Document

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@600&display=swap');

:root {
  --bg:#111418; --surface:#171A1F; --card:#1E232B;
  --text:#F5F5F5; --muted:#9BA1A9; --accent:#E63946;
  --border:#2C313A;
}
html,body,[class*="css"]{
  background:var(--bg)!important; color:var(--text)!important;
  font-family:'Source Code Pro',monospace;
}
.block-container{padding-top:1rem; padding-bottom:7rem;}
hr{border:0; height:1px; background:var(--border);}
.stTextArea textarea {
  background:var(--surface);
  color:var(--text);
  border:1px solid var(--border);
  border-radius:8px;
  height:80px;
  caret-color: var(--text); /* visible caret fix */
}
.stButton>button {
  background:var(--accent);
  color:#fff;
  border:0;
  border-radius:8px;
  height:38px;
  font-weight:600;
}
.stButton>button:hover {
  filter:brightness(1.15);
}

/* Animated SENTINEL header */
.typewriter {
  font-weight:600;
  font-size:46px;
  color:var(--accent);
  overflow:hidden;
  border-right:.15em solid var(--accent);
  white-space:nowrap;
  margin:0 auto;
  letter-spacing:.12em;
  animation:typing 2.5s steps(20,end), blink-caret .75s step-end infinite;
}
@keyframes typing { from{width:0} to{width:100%} }
@keyframes blink-caret { from,to{border-color:transparent} 50%{border-color:var(--accent);} }
.s-subtext {
  text-align:center; color:var(--muted); font-size:13px; margin-top:4px;
  letter-spacing:1px;
}

/* Chat */
.chat-wrap{background:var(--card); border:1px solid var(--border);
  border-radius:12px; padding:16px 18px; height:65vh; overflow-y:auto;}
.chat-bubble{background:rgba(30,35,43,.95); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px; padding:12px 14px;
  margin:10px 0; line-height:1.55; animation:fadeIn .3s ease;}
.chat-bubble.error{border-left-color:#ff6b6b;}
.meta{color:var(--muted); font-size:11px; margin-top:4px;}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}

.static-footer{position:fixed;left:0;right:0;bottom:0;
  background:var(--surface);border-top:2px solid var(--accent);
  box-shadow:0 -3px 12px rgba(0,0,0,.4);z-index:9999;}
.footer-inner{max-width:1100px;margin:0 auto;padding:10px 16px;
  display:flex;gap:10px;align-items:flex-end;}
.footer-left{flex:1;}
.footer-right{width:260px;display:flex;flex-direction:column;gap:8px;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<div style='text-align:center; margin-top:10px;'>
  <div class='typewriter'>SENTINEL</div>
  <div class='s-subtext'>Autonomous Intelligence for Private Markets</div>
</div>
<hr/>
""", unsafe_allow_html=True)

# ---------- STATE ----------
if "threads" not in st.session_state:
    st.session_state["threads"] = {}
if "context" not in st.session_state:
    st.session_state["context"] = ""
if "last_agent" not in st.session_state:
    st.session_state["last_agent"] = "strata"
if "is_running" not in st.session_state:
    st.session_state["is_running"] = False
if "prompt" not in st.session_state:
    st.session_state["prompt"] = ""

AGENTS = {
    "strata": "Research & intelligence for energy/decarbonization.",
    "dealhawk": "Deal sourcing for profitable private companies.",
    "neo": "Financial modeling and scenario analysis.",
    "cipher": "Governance, PII scrub, policy checks.",
    "proforma": "Formatting and exports for IC memos."
}
for a in AGENTS:
    st.session_state["threads"].setdefault(a, [])

# ---------- SIDEBAR ----------
st.sidebar.markdown("### ⚙️ Orchestrator")
agent = st.sidebar.selectbox("Choose agent", list(AGENTS.keys()),
                             index=list(AGENTS.keys()).index(st.session_state["last_agent"]))
st.session_state["last_agent"] = agent
st.sidebar.caption(AGENTS[agent])
st.sidebar.markdown("---")

files = st.sidebar.file_uploader("📎 Upload files (PDF/DOCX)",
                                 type=["pdf", "docx"], accept_multiple_files=True)

def _pdf_text(b: bytes) -> str:
    text = ""
    if pdfplumber:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages:
                    text += p.extract_text() or ""
        except Exception:
            pass
    if not text.strip() and OCR_AVAILABLE:
        try:
            imgs = convert_from_bytes(b, dpi=200)
            text = "\n".join(pytesseract.image_to_string(i) for i in imgs)
        except Exception:
            pass
    return text.strip()

def _docx_text(b: bytes) -> str:
    try:
        doc = Document(io.BytesIO(b))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

if files:
    texts = []
    for f in files[:3]:
        data = f.getvalue()
        n = f.name.lower()
        parsed = _pdf_text(data) if n.endswith(".pdf") else _docx_text(data)
        if parsed:
            texts.append(parsed)
    st.session_state["context"] = ("\n\n".join(texts)).strip()[:10000]

if st.session_state["context"]:
    with st.sidebar.expander("🗂 Preview extracted text", expanded=False):
        st.text_area("Context (trimmed)", st.session_state["context"][:3000], height=200)

if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# ---------- CHAT DISPLAY ----------
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
thread = st.session_state["threads"][agent]
if thread:
    for item in thread[-15:]:
        css_extra = " error" if item.get("error") else ""
        st.markdown(
            f"""<div class="chat-bubble{css_extra}">
                <b>{item['agent'].upper()}</b><br>{item['response'].replace(chr(10),'<br>')}
                <div class="meta">⏱ {item['time']}</div></div>""",
            unsafe_allow_html=True)
else:
    st.info("Upload files (optional) and start chatting with the active agent below.")
st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<div style='height:120px;'></div>", unsafe_allow_html=True)

# ---------- RUNNER ----------
def _compose(user_q: str) -> str:
    ctx = st.session_state.get("context", "").strip()
    return f"Context:\n{ctx}\n\nUser Query:\n{user_q}" if ctx else user_q

def run_agent(agent_key: str, user_q: str):
    st.session_state["is_running"] = True
    q = _compose(user_q)
    output, is_error = "", False
    with st.spinner(f"{agent_key.upper()} is thinking..."):
        try:
            res = subprocess.run(
                ["python", "sentinal_orchestrator.py", agent_key, q],
                capture_output=True, text=True, check=False, timeout=60
            )
            output = (res.stdout or "").strip()
            if not output:
                err = (res.stderr or "").strip()
                if err:
                    output = f"⚠️ Agent error:\n{err}"
                    is_error = True
        except subprocess.TimeoutExpired:
            output = "⏱ Timeout after 60s."
            is_error = True
        except Exception as e:
            output = f"⚠️ {e}"
            is_error = True

    st.session_state["threads"][agent_key].append({
        "agent": agent_key, "query": user_q,
        "response": output, "time": datetime.now().strftime("%H:%M:%S"),
        "error": is_error
    })
    st.session_state["is_running"] = False
    st.rerun()

# ---------- FOOTER ----------
st.markdown("""
<div class="static-footer">
  <div class="footer-inner">
    <div class="footer-left"></div>
    <div class="footer-right"></div>
  </div>
</div>
""", unsafe_allow_html=True)

left = st.empty()
right = st.empty()

with left.container():
    st.session_state["prompt"] = st.text_area(
        "Type your prompt here:",
        value=st.session_state["prompt"],
        key="prompt_box",
        placeholder="Ask Sentinel...",
        height=80
    )

with right.container():
    send = st.button("💬 Ask Agent", use_container_width=True)

if send and st.session_state["prompt"].strip() and not st.session_state["is_running"]:
    run_agent(agent, st.session_state["prompt"].strip())
    st.session_state["prompt"] = ""
