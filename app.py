# app.py — Sentinel v1.5 (Command Center UI)
# ------------------------------------------
# UX:
# - Solid matte background (#121212), Longbow red accent (#E63946)
# - Static header "SENTINEL" with animated underline shimmer
# - "ACTIVE AGENT: <name>  •  🔴" with subtle pulse
# - Scrollable chat container (last 10 messages), fade-in bubbles
# - Fixed footer: input + Ask Agent + Send to NEXT
#
# Functionality:
# - Multi-file upload (PDF/DOCX up to 3 × 10 MB)
# - PDF text → OCR fallback (pdf2image + pytesseract), safe if libs missing
# - Context injection (~10k chars), retries (3) + timeout (60s) for agent calls
# - Session reset

import io
import time
import subprocess
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
# Solid matte background + command-center polish
st.markdown("""
<style>
:root {
  --bg: #121212;
  --surface: #171A1F;
  --card: #1C2129;
  --text: #F5F5F5;
  --muted: #B8BEC6;
  --accent: #E63946;
  --border: #2B3038;
}

html, body, [class*="css"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}

.block-container { padding-top: 1.2rem; padding-bottom: 7.2rem; }

/* Header */
.s-header { text-align:center; margin-top:-4px; margin-bottom:12px; }
.s-title  { font-size: 44px; letter-spacing: 2px; font-weight: 900; }
.s-underline {
  width: 160px; height: 4px; margin: 8px auto 6px auto; border-radius: 3px;
  background: linear-gradient(90deg, rgba(230,57,70,0) 0%, var(--accent) 50%, rgba(230,57,70,0) 100%);
  background-size: 200% 100%;
  animation: shimmer 3.5s linear infinite;
  opacity: .9;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* Agent status line */
.s-status { text-align:center; color: var(--muted); font-size: 13px; }
.pulse {
  display:inline-block; width:10px; height:10px; border-radius:50%;
  background: var(--accent); margin-left:8px; box-shadow: 0 0 0 rgba(230,57,70, 0.7);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(230,57,70,0.5); }
  70% { box-shadow: 0 0 0 10px rgba(230,57,70,0); }
  100% { box-shadow: 0 0 0 0 rgba(230,57,70,0); }
}

/* Containers */
.chat-wrap {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  height: 68vh;            /* fixed height; scrolls inside */
  overflow-y: auto;
  scroll-behavior: smooth;
}

.chat-bubble {
  background: rgba(28,33,41, 0.92);
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  border-radius: 12px;
  padding: 12px 14px;
  margin: 10px 0;
  line-height: 1.55;
  color: var(--text);
  animation: fadeIn 240ms ease-in;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.meta { color: var(--muted); font-size: 12px; margin-top: 6px; }

.static-footer {
  position: fixed; left: 0; right: 0; bottom: 0;
  background: var(--bg);
  border-top: 2px solid var(--accent);
  box-shadow: 0 -6px 24px rgba(0,0,0,0.45);
  padding: 10px 16px;
  z-index: 9999;
}

/* Inputs/Buttons */
.stTextArea textarea {
  background: var(--surface); color: var(--text);
  border: 1px solid var(--border);
}
.stButton>button {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 8px;
}
.stButton>button:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(230,57,70,0.28);
}
hr { border: 0; height: 1px; background: var(--border); }
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE --------------------
defaults = {
    "history": [],            # list of {agent, query, response, time}
    "context": "",            # extracted file text
    "last_agent": "strata",   # current agent
    "next_agent": "dealhawk", # pointer to next
    "is_running": False
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------- HEADER --------------------
st.markdown("""
<div class="s-header">
  <div class="s-title">SENTINEL</div>
  <div class="s-underline"></div>
</div>
""", unsafe_allow_html=True)

# Active agent line with pulse
st.markdown(
    f"""<div class="s-status">
            ACTIVE AGENT: <b>{st.session_state['last_agent'].upper()}</b>
            <span class="pulse"></span>
        </div>
        <hr/>""",
    unsafe_allow_html=True
)

# -------------------- AGENTS --------------------
AGENTS = {
    "strata": "Research & intelligence for energy/decarbonization.",
    "dealhawk": "Deal sourcing for profitable private companies.",
    "neo": "Financial modeling and scenario analysis.",
    "cipher": "Governance, PII scrub, policy checks.",
    "proforma": "Formatting and exports for IC memos."
}
AGENT_SEQUENCE = list(AGENTS.keys())

# -------------------- SIDEBAR: Controls + Upload --------------------
st.sidebar.markdown("### ⚙️ Orchestrator")
agent_sel = st.sidebar.selectbox("Choose agent", options=AGENT_SEQUENCE,
                                 index=AGENT_SEQUENCE.index(st.session_state["last_agent"]),
                                 format_func=lambda x: x.upper())
st.sidebar.caption(AGENTS[agent_sel])

# keep last_agent in sync with selector
st.session_state["last_agent"] = agent_sel
current_index = AGENT_SEQUENCE.index(agent_sel)
st.session_state["next_agent"] = AGENT_SEQUENCE[current_index + 1] if current_index + 1 < len(AGENT_SEQUENCE) else None

MAX_FILES = 3
MAX_MB = 10
MAX_CONTEXT_CHARS = 10000

st.sidebar.markdown("---")
st.sidebar.markdown("### 📎 Upload files (PDF/DOCX)")
files = st.sidebar.file_uploader("Up to 3 files • 10 MB each", type=["pdf", "docx"], accept_multiple_files=True)

def _size_mb(file): return len(file.getbuffer()) / (1024 * 1024)

def extract_text_from_pdf_bytes(b: bytes) -> str:
    text = ""
    # Try selectable text first if pdfplumber is available
    if pdfplumber is not None:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages:
                    text += p.extract_text() or ""
        except Exception:
            pass
    # If nothing or no pdfplumber, try OCR (if available)
    if not text.strip() and OCR_AVAILABLE:
        try:
            imgs = convert_from_bytes(b, dpi=200)
            chunks = []
            for img in imgs:
                chunks.append(pytesseract.image_to_string(img))
            text = "\n".join(chunks)
        except Exception:
            pass
    return text.strip()

def extract_text_from_docx_bytes(b: bytes) -> str:
    try:
        doc = Document(io.BytesIO(b))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

if files:
    too_big = [f.name for f in files if _size_mb(f) > MAX_MB]
    if too_big:
        st.sidebar.error(f"Too large (>10 MB): {', '.join(too_big)}")
    else:
        texts = []
        with st.sidebar.status("Parsing files...", expanded=False) as s:
            for f in files[:MAX_FILES]:
                data = f.getvalue()
                name = f.name.lower()
                parsed = ""
                if name.endswith(".pdf"):
                    parsed = extract_text_from_pdf_bytes(data)
                elif name.endswith(".docx"):
                    parsed = extract_text_from_docx_bytes(data)
                if parsed:
                    texts.append(parsed)
            if texts:
                ctx = ("\n\n".join(texts)).strip()
                st.session_state["context"] = ctx[:MAX_CONTEXT_CHARS]
                s.update(label=f"✅ Parsed {len(ctx):,} characters", state="complete")
            else:
                s.update(label="⚠️ No readable text extracted", state="error")

if st.session_state.get("context"):
    with st.sidebar.expander("🗂 Preview extracted text", expanded=False):
        st.text_area("Context (trimmed)", st.session_state["context"][:3000], height=200)

st.sidebar.markdown("---")
if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()

# -------------------- CHAT HISTORY (scrollable) --------------------
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

# Auto-scroll chat to bottom
st.markdown("""
<script>
const el = window.parent.document.getElementById('chat');
if (el) { el.scrollTop = el.scrollHeight; }
</script>
""", unsafe_allow_html=True)

# -------------------- AGENT RUNNER --------------------
def build_query_with_context(user_q: str) -> str:
    ctx = st.session_state.get("context", "").strip()
    if not ctx:
        return user_q
    return f"Context from uploaded documents:\n{ctx}\n\nUser Query:\n{user_q}"

def run_agent(agent_key: str, user_q: str):
    if st.session_state["is_running"]:
        return
    st.session_state["is_running"] = True
    start = time.time()

    q = build_query_with_context(user_q)
    retries = 3
    output = ""
    with st.spinner(f"Running {agent_key.upper()}..."):
        for attempt in range(retries):
            try:
                result = subprocess.run(
                    ["python", "sentinal_orchestrator.py", agent_key, q],
                    capture_output=True, text=True, check=True, timeout=60
                )
                output = (result.stdout or "").strip()
                if not output:
                    output = "(no output)"
                break
            except subprocess.TimeoutExpired:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    output = "⏱️ Timeout after 60s (3 attempts)."
            except subprocess.CalledProcessError as e:
                output = e.stdout or e.stderr or "Agent execution error."
                break

    st.session_state["history"].append({
        "agent": agent_key,
        "query": user_q,
        "response": output,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    # set next agent pointer
    idx = AGENT_SEQUENCE.index(agent_key)
    st.session_state["next_agent"] = AGENT_SEQUENCE[idx + 1] if idx + 1 < len(AGENT_SEQUENCE) else None

    st.session_state["is_running"] = False

# -------------------- STATIC FOOTER (input + buttons) --------------------
st.markdown('<div class="static-footer">', unsafe_allow_html=True)
col1, col2 = st.columns([4, 2])
with col1:
    user_query = st.text_area("Type your prompt here:",
                              placeholder="Ask about a market theme, target list, or modeling scenario…",
                              height=80, key="prompt")
with col2:
    ask_btn = st.button("💬 Ask Agent", use_container_width=True, key="ask")
    next_key = st.session_state.get("next_agent")
    if next_key:
        next_btn = st.button(f"➡ Send to {next_key.upper()}", use_container_width=True, key="next")
    else:
        next_btn = False
st.markdown('</div>', unsafe_allow_html=True)

if ask_btn and user_query.strip():
    run_agent(st.session_state["last_agent"], user_query.strip())
elif next_btn and user_query.strip():
    run_agent(next_key, user_query.strip())
