# app.py – Sentinel v1.7
# ------------------------------------------
# Fixes:
# • Active Agent now stays in sync with sidebar select (immediate)
# • Next Agent recalculated correctly
# • Reset uses st.rerun() (no AttributeError)
# • Single scrollable chat, fixed footer, solid dark theme
# • Safe OCR fallback (optional libs)

import io, time, subprocess
from datetime import datetime
import streamlit as st

# Optional imports (safe)
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

# ---------- PAGE ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- THEME / CSS ----------
st.markdown("""
<style>
:root {
  --bg:#121212; --surface:#171A1F; --card:#1C2129;
  --text:#F5F5F5; --muted:#B8BEC6; --accent:#E63946; --border:#2B3038;
}
html,body,[class*="css"]{ background:var(--bg)!important; color:var(--text)!important;
  font-family:Inter,system-ui,sans-serif; }
.block-container{ padding-top:2rem; padding-bottom:9rem; }

.s-header{ text-align:center; margin:0 0 8px 0; }
.s-title{ font-size:44px; letter-spacing:2px; font-weight:900; }
.s-underline{ width:160px; height:4px; margin:8px auto 6px auto; border-radius:3px;
  background:linear-gradient(90deg,var(--accent),#e77d84); }
.s-status{ text-align:center; color:var(--muted); font-size:13px; }
.pulse{ display:inline-block; width:10px; height:10px; border-radius:50%;
  background:var(--accent); margin-left:8px; animation:pulse 2s infinite; }
@keyframes pulse{ 0%{opacity:.6} 50%{opacity:1} 100%{opacity:.6} }

.chat-wrap{ background:var(--card); border:1px solid var(--border);
  border-radius:12px; padding:14px 16px; height:68vh; overflow-y:auto; scroll-behavior:smooth; }
.chat-bubble{ background:rgba(28,33,41,.92); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:12px; padding:12px 14px;
  margin:10px 0; line-height:1.55; color:var(--text); animation:fadeIn .2s ease-in; }
@keyframes fadeIn{ from{opacity:0; transform:translateY(4px);} to{opacity:1; transform:translateY(0);} }
.meta{ color:var(--muted); font-size:12px; margin-top:6px; }

.static-footer{ position:fixed; left:0; right:0; bottom:0; background:var(--bg);
  border-top:2px solid var(--accent); box-shadow:0 -4px 16px rgba(0,0,0,.45);
  padding:10px 18px; z-index:9999; }
.footer-flex{ display:flex; align-items:center; gap:10px; }

.stTextArea textarea{ background:var(--surface); color:var(--text); border:1px solid var(--border); }
.stButton>button{ background:var(--surface); border:1px solid var(--border); color:var(--text);
  border-radius:8px; height:80px; }
.stButton>button:hover{ border-color:var(--accent); box-shadow:0 0 0 2px rgba(230,57,70,.28); }
hr{ border:0; height:1px; background:var(--border); }
</style>
""", unsafe_allow_html=True)

# ---------- STATE ----------
defaults = {
    "history": [], "context": "",
    "last_agent": "strata", "next_agent": "dealhawk",
    "is_running": False
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

AGENTS = {
    "strata": "Research & intelligence for energy/decarbonization.",
    "dealhawk": "Deal sourcing for profitable private companies.",
    "neo": "Financial modeling and scenario analysis.",
    "cipher": "Governance, PII scrub, policy checks.",
    "proforma": "Formatting and exports for IC memos."
}
AGENT_SEQUENCE = list(AGENTS.keys())

def _recompute_next():
    idx = AGENT_SEQUENCE.index(st.session_state["last_agent"])
    st.session_state["next_agent"] = (
        AGENT_SEQUENCE[idx + 1] if idx + 1 < len(AGENT_SEQUENCE) else None
    )

# Sidebar select → callback keeps app in sync
def _on_agent_change():
    st.session_state["last_agent"] = st.session_state["agent_select"]
    _recompute_next()

# ---------- HEADER ----------
st.markdown("""
<div class="s-header">
  <div class="s-title">SENTINEL</div>
  <div class="s-underline"></div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    f"""<div class="s-status">
            ACTIVE AGENT: <b>{st.session_state['last_agent'].upper()}</b>
            <span class="pulse"></span></div><hr/>""",
    unsafe_allow_html=True
)

# ---------- SIDEBAR ----------
st.sidebar.markdown("### ⚙️ Orchestrator")
st.sidebar.selectbox(
    "Choose agent",
    options=AGENT_SEQUENCE,
    index=AGENT_SEQUENCE.index(st.session_state["last_agent"]),
    key="agent_select",
    on_change=_on_agent_change,
    format_func=lambda x: x.upper()
)
st.sidebar.caption(AGENTS[st.session_state["last_agent"]])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📎 Upload files (PDF/DOCX)")
files = st.sidebar.file_uploader(
    "Up to 3 files • 10 MB each",
    type=["pdf", "docx"], accept_multiple_files=True
)

def _pdf_text(b: bytes) -> str:
    text = ""
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages:
                    text += p.extract_text() or ""
        except Exception:
            pass
    if not text.strip() and OCR_AVAILABLE:
        try:
            imgs = convert_from_bytes(b, dpi=200)
            text = "\n".join(pytesseract.image_to_string(img) for img in imgs)
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
        name = f.name.lower()
        if name.endswith(".pdf"):
            texts.append(_pdf_text(data))
        elif name.endswith(".docx"):
            texts.append(_docx_text(data))
    ctx = "\n\n".join(t for t in texts if t).strip()
    st.session_state["context"] = ctx[:10000]
if st.session_state.get("context"):
    with st.sidebar.expander("🗂 Preview extracted text", expanded=False):
        st.text_area("Context (trimmed)", st.session_state["context"][:3000], height=200)

st.sidebar.markdown("---")
if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()  # modern API

# ---------- CHAT ----------
st.markdown('<div id="chat" class="chat-wrap">', unsafe_allow_html=True)
if st.session_state["history"]:
    for item in st.session_state["history"][-10:]:
        st.markdown(
            f"""<div class="chat-bubble">
                    <b>{item['agent'].upper()}</b><br>
                    {item['response'].replace(chr(10), '<br>')}
                    <div class="meta">⏱ {item['time']}</div>
                </div>""",
            unsafe_allow_html=True
        )
else:
    st.info("Upload files (optional) and type a prompt below to get started.")
st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)  # keep chat clear of footer

# ---------- RUNNER ----------
def _compose(user_q: str) -> str:
    ctx = st.session_state.get("context", "").strip()
    return f"Context:\n{ctx}\n\nUser Query:\n{user_q}" if ctx else user_q

def run_agent(agent_key: str, user_q: str):
    if st.session_state["is_running"]:
        return
    st.session_state["is_running"] = True
    q = _compose(user_q)
    output = ""
    with st.spinner(f"Running {agent_key.upper()}..."):
        for attempt in range(3):
            try:
                res = subprocess.run(
                    ["python", "sentinal_orchestrator.py", agent_key, q],
                    capture_output=True, text=True, check=False, timeout=60
                )
                output = (res.stdout or "").strip()
                if not output:
                    output = res.stderr.strip() or "(no output)"
                break
            except subprocess.TimeoutExpired:
                if attempt == 2:
                    output = "⏱️ Timeout after 60s (3 attempts)."
                else:
                    time.sleep(2 ** attempt)
            except Exception as e:
                output = f"⚠️ Agent error: {e}"
                break
    st.session_state["history"].append({
        "agent": agent_key, "query": user_q,
        "response": output, "time": datetime.now().strftime("%H:%M:%S")
    })
    # recompute next after a run (in case user changed selection)
    _recompute_next()
    st.session_state["is_running"] = False

# ---------- FOOTER (fixed) ----------
st.markdown('<div class="static-footer"><div class="footer-flex">', unsafe_allow_html=True)
user_q = st.text_area("Type your prompt here:", placeholder="Ask Sentinel…", height=80, key="prompt")
colA, colB = st.columns([1, 1])
with colA:
    ask = st.button("💬 Ask Agent", use_container_width=True, key="ask")
with colB:
    next_key = st.session_state.get("next_agent")
    send_next = st.button(f"➡ Send to {next_key.upper()}" if next_key else "Next", use_container_width=True, key="next")
st.markdown('</div></div>', unsafe_allow_html=True)

if ask and user_q.strip():
    run_agent(st.session_state["last_agent"], user_q.strip())
elif send_next and user_q.strip() and next_key:
    run_agent(next_key, user_q.strip())
