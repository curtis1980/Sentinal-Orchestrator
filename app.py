# app.py — Sentinel v1.8 (fixed footer, Ctrl+Enter, error containment)
# -------------------------------------------------------------------
# UX:
# - Fixed footer: input (left) + buttons (right, stacked)
# - Scrollable chat window (last 10)
# - ACTIVE AGENT indicator stays in sync with sidebar select
# - Ctrl + Enter triggers "Ask Agent"
#
# Resilience:
# - Subprocess errors/timeouts captured into chat (no second pane)
# - OCR libs optional (won’t crash if missing)

import io, time, subprocess, os
from datetime import datetime
import streamlit as st

# Optional parsers (safe imports)
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

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Sentinel", layout="wide")

# -------------------- THEME / CSS --------------------
st.markdown("""
<style>
:root {
  --bg:#121212; --surface:#171A1F; --card:#1C2129;
  --text:#F5F5F5; --muted:#B8BEC6; --accent:#E63946; --border:#2B3038;
}
html,body,[class*="css"]{ background:var(--bg)!important; color:var(--text)!important;
  font-family:Inter,system-ui,sans-serif; }
.block-container{ padding-top:2rem; padding-bottom:9.5rem; } /* leave space for fixed footer */

.s-header{ text-align:center; margin:0 0 8px 0; }
.s-title{ font-size:44px; letter-spacing:2px; font-weight:900; }
.s-underline{ width:160px; height:4px; margin:8px auto 6px auto; border-radius:3px;
  background:linear-gradient(90deg,var(--accent),#e77d84); }
.s-status{ text-align:center; color:var(--muted); font-size:13px; margin-bottom:8px; }
.pulse{ display:inline-block; width:10px; height:10px; border-radius:50%; background:var(--accent); margin-left:8px;
  animation:pulse 2s infinite; }
@keyframes pulse{ 0%{opacity:.6} 50%{opacity:1} 100%{opacity:.6} }

.chat-wrap{ background:var(--card); border:1px solid var(--border); border-radius:12px;
  padding:14px 16px; height:68vh; overflow-y:auto; scroll-behavior:smooth; }
.chat-bubble{ background:rgba(28,33,41,.92); border:1px solid var(--border); border-left:4px solid var(--accent);
  border-radius:12px; padding:12px 14px; margin:10px 0; line-height:1.55; color:var(--text); animation:fadeIn .2s ease-in; }
.chat-bubble.error{ border-left-color:#ff6b6b; background:rgba(38,18,18,.92); }
@keyframes fadeIn{ from{opacity:0; transform:translateY(4px);} to{opacity:1; transform:translateY(0);} }
.meta{ color:var(--muted); font-size:12px; margin-top:6px; }
hr{ border:0; height:1px; background:var(--border); }

.static-footer{ position:fixed; left:0; right:0; bottom:0; background:var(--bg);
  border-top:2px solid var(--accent); box-shadow:0 -4px 16px rgba(0,0,0,.45); z-index:9999; }
.footer-inner{ max-width:1200px; margin:0 auto; padding:12px 18px; display:flex; gap:14px; align-items:stretch; }
.footer-left{ flex:1; }
.footer-right{ width:320px; display:flex; flex-direction:column; gap:10px; }

.stTextArea textarea{ background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:8px; height:80px; }
.stButton>button{ background:var(--surface); border:1px solid var(--border); color:var(--text);
  border-radius:8px; height:38px; }
.stButton>button:hover{ border-color:var(--accent); box-shadow:0 0 0 2px rgba(230,57,70,.28); }
</style>
""", unsafe_allow_html=True)

# -------------------- STATE --------------------
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

def _on_agent_change():
    st.session_state["last_agent"] = st.session_state["agent_select"]
    _recompute_next()

# -------------------- HEADER --------------------
st.markdown("""
<div class="s-header">
  <div class="s-title">SENTINEL</div>
  <div class="s-underline"></div>
</div>
""", unsafe_allow_html=True)
st.markdown(
    f"""<div class="s-status">
            ACTIVE AGENT: <b>{st.session_state['last_agent'].upper()}</b><span class="pulse"></span>
        </div>""",
    unsafe_allow_html=True
)
st.markdown("<hr/>", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
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
files = st.sidebar.file_uploader("Up to 3 files • 10 MB each", type=["pdf", "docx"], accept_multiple_files=True)

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
        n = f.name.lower()
        parsed = _pdf_text(data) if n.endswith(".pdf") else _docx_text(data)
        if parsed:
            texts.append(parsed)
    st.session_state["context"] = ("\n\n".join(texts)).strip()[:10000]

if st.session_state.get("context"):
    with st.sidebar.expander("🗂 Preview extracted text", expanded=False):
        st.text_area("Context (trimmed)", st.session_state["context"][:3000], height=200)

st.sidebar.markdown("---")
if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# -------------------- CHAT (scrollable) --------------------
st.markdown('<div id="chat" class="chat-wrap">', unsafe_allow_html=True)
if st.session_state["history"]:
    for item in st.session_state["history"][-10:]:
        css_extra = " error" if item.get("error") else ""
        st.markdown(
            f"""<div class="chat-bubble{css_extra}">
                    <b>{item['agent'].upper()}</b><br>
                    {item['response'].replace(chr(10), '<br>')}
                    <div class="meta">⏱ {item['time']}</div>
                </div>""",
            unsafe_allow_html=True
        )
else:
    st.info("Upload files (optional) and type a prompt below to get started.")
st.markdown('</div>', unsafe_allow_html=True)

# Keep enough spacing so chat never hides behind the fixed footer
st.markdown("<div style='height:120px;'></div>", unsafe_allow_html=True)

# -------------------- RUNNER --------------------
def _compose(user_q: str) -> str:
    ctx = st.session_state.get("context", "").strip()
    return f"Context:\n{ctx}\n\nUser Query:\n{user_q}" if ctx else user_q

def run_agent(agent_key: str, user_q: str):
    if st.session_state["is_running"]:
        return
    st.session_state["is_running"] = True
    q = _compose(user_q)

    output = ""
    is_error = False
    with st.spinner(f"Running {agent_key.upper()}..."):
        for attempt in range(3):
            try:
                res = subprocess.run(
                    ["python", "sentinal_orchestrator.py", agent_key, q],
                    capture_output=True, text=True, check=False, timeout=60
                )
                # Prefer stdout; if empty, show stderr (trim)
                output = (res.stdout or "").strip()
                if not output:
                    err = (res.stderr or "").strip()
                    if err:
                        output = f"⚠️ Agent error:\n{err}"
                        is_error = True
                break
            except subprocess.TimeoutExpired:
                if attempt == 2:
                    output = "⏱️ Timeout after 60s (3 attempts)."
                    is_error = True
                else:
                    time.sleep(2 ** attempt)
            except Exception as e:
                output = f"⚠️ Agent execution error: {e}"
                is_error = True
                break

    st.session_state["history"].append({
        "agent": agent_key, "query": user_q,
        "response": output, "time": datetime.now().strftime("%H:%M:%S"),
        "error": is_error
    })
    # Recompute next (in case selection changed)
    _recompute_next()
    st.session_state["is_running"] = False

# -------------------- FIXED FOOTER --------------------
st.markdown(
    """
<div class="static-footer">
  <div class="footer-inner">
    <div class="footer-left">
      <!-- Text area rendered by Streamlit -->
    </div>
    <div class="footer-right">
      <!-- Buttons rendered by Streamlit -->
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Render Streamlit widgets into the footer columns
footer_left = st.empty()
footer_right = st.empty()

with footer_left.container():
    user_q = st.text_area("Type your prompt here:", value=st.session_state.get("prompt", ""),
                          placeholder="Ask Sentinel…", height=80, key="prompt")

with footer_right.container():
    ask = st.button("💬 Ask Agent", use_container_width=True, key="ask_btn")
    nxt = st.session_state.get("next_agent")
    send_next = st.button(f"➡ Send to {nxt.upper()}" if nxt else "Next", use_container_width=True, key="next_btn")

# Ctrl + Enter → trigger Ask Agent (client-side; no extra deps)
st.markdown("""
<script>
(function(){
  const root = window.parent.document;
  root.addEventListener('keydown', function(e){
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const btns = Array.from(root.querySelectorAll('button'));
      const ask = btns.find(b => b.innerText.trim().toLowerCase().includes('ask agent'));
      if (ask) ask.click();
      e.preventDefault();
    }
  }, false);
})();
</script>
""", unsafe_allow_html=True)

# Handle actions
if ask and user_q.strip():
    run_agent(st.session_state["last_agent"], user_q.strip())
elif send_next and user_q.strip() and nxt:
    run_agent(nxt, user_q.strip())
