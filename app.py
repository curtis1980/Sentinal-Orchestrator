# app.py – Sentinel v1.3 (enterprise build)
# -----------------------------------------
# Features:
# - Multi-file PDF/DOCX upload (3×10 MB)
# - OCR fallback (pdf2image + pytesseract) with safe guards
# - Chat-style UI with static input
# - Resilient subprocess orchestration
# - Export + reset + telemetry sidebar

import os, io, time, base64, subprocess
from datetime import datetime
from typing import List, Tuple

import streamlit as st
from docx import Document
import pdfplumber

# Optional OCR libs (safe import)
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


# ---------- Streamlit Config ----------
st.set_page_config(page_title="Sentinel | AI Orchestrator", layout="wide")

st.markdown("""
<style>
body { background:#0E0E0E; color:#E5E5E5; font-family:'Inter',sans-serif; }
.sentinel-title{font-size:36px;font-weight:800;color:#F5F5F5;}
.sentinel-sub{font-size:15px;color:#C0C0C0;}
.divider{border-bottom:1px solid #333;margin:18px 0 28px 0;}
.chat-bubble{background:#181818;border-left:4px solid #E74C3C;
  padding:12px;border-radius:10px;margin:8px 0;}
.static-input{position:fixed;bottom:0;left:0;right:0;
  background:#0E0E0E;padding:10px 20px;border-top:1px solid #222;}
</style>
""", unsafe_allow_html=True)


# ---------- Header ----------
st.markdown("""
<div style="display:flex;align-items:center;gap:14px;">
  <div>
    <div class="sentinel-title">SENTINEL</div>
    <div class="sentinel-sub">Autonomous Agents for Asymmetric Advantage</div>
  </div>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ---------- Constants ----------
MAX_FILE_MB = 10
MAX_FILES = 3
MAX_CONTEXT = 12000

AGENTS = {
    "strata": {"color": "#4CAF50", "desc": "Research and intelligence for energy & decarbonization."},
    "dealhawk": {"color": "#FF9800", "desc": "Deal sourcing of late-stage profitable transition firms."},
    "neo": {"color": "#2196F3", "desc": "Financial modeling and scenario analysis."},
    "cipher": {"color": "#9C27B0", "desc": "Governance, PII scrub, data validation."},
    "proforma": {"color": "#795548", "desc": "Formats outputs, IC-ready exports."},
}
AGENT_SEQUENCE = list(AGENTS.keys())


# ---------- Session State ----------
for key, default in {
    "history": [], "context_text": "", "last_agent": None,
    "next_agent": None, "is_running": False
}.items():
    st.session_state.setdefault(key, default)


# ---------- File Parsing & OCR ----------
def size_mb(f): return len(f.getbuffer()) / (1024 * 1024)

def extract_text_from_pdf(file) -> str:
    """Try text extraction; fallback to OCR if needed."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                text += p.extract_text() or ""
    except Exception:
        return ""
    if text.strip():  # text found
        return text
    # OCR fallback
    if not OCR_AVAILABLE:
        st.warning("⚠️ OCR libraries missing (pdf2image/pytesseract). Skipping OCR.")
        return ""
    try:
        file.seek(0)
        images = convert_from_bytes(file.read(), dpi=200)
        ocr_text = []
        for img in images:
            ocr_text.append(pytesseract.image_to_string(img))
        return "\n".join(ocr_text)
    except Exception as e:
        st.warning(f"OCR failed: {e}")
        return ""

def extract_text_from_docx(file) -> str:
    try:
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def parse_uploads(files) -> Tuple[str, float]:
    """Combine parsed text + heuristic confidence."""
    if not files: return "", 0.0
    text_parts, total_bytes = [], 0
    for f in files[:MAX_FILES]:
        total_bytes += len(f.getbuffer())
        name = f.name.lower()
        if name.endswith(".pdf"):
            text_parts.append(extract_text_from_pdf(f))
        elif name.endswith(".docx"):
            text_parts.append(extract_text_from_docx(f))
    text = "\n\n".join([t for t in text_parts if t])
    mb = max(total_bytes / (1024 * 1024), 0.001)
    conf = min(len(text) / (mb * 5000), 2.0)
    return text.strip(), round(conf * 100, 1)


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Agent Selector")
    agent = st.selectbox("Choose an agent:", AGENT_SEQUENCE,
                         format_func=lambda k: k.upper())
    st.caption(AGENTS[agent]["desc"])

    st.markdown("---")
    st.markdown("### Upload Documents")
    files = st.file_uploader(
        "PDF/DOCX (max 10 MB each, up to 3)",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    if files:
        big = [f.name for f in files if size_mb(f) > MAX_FILE_MB]
        if big:
            st.error(f"Files too large: {', '.join(big)}")
        else:
            with st.spinner("Extracting text..."):
                ctx, conf = parse_uploads(files)
                if ctx:
                    st.session_state.context_text = ctx[:MAX_CONTEXT]
                    st.success(f"✅ Parsed {len(ctx):,} chars • confidence ≈ {int(conf)}%")
                else:
                    st.warning("No readable text found (possibly scanned with poor OCR).")
    if st.session_state.context_text:
        with st.expander("📄 Preview Extracted Text"):
            st.text_area("Extracted Context (trimmed)",
                         st.session_state.context_text[:4000], height=200)


# ---------- Helper ----------
def build_query(user_query: str) -> str:
    ctx = st.session_state.get("context_text", "").strip()
    if not ctx:
        return user_query
    return f"Context from uploaded documents:\n{ctx}\n\nUser Query:\n{user_query}"


# ---------- Agent Runner ----------
def run_agent(agent_key: str, query_text: str):
    if st.session_state.is_running:
        return
    st.session_state.is_running = True
    start = time.time()
    q = build_query(query_text)

    with st.spinner(f"Running {agent_key.upper()}..."):
        attempt = 0
        while attempt < 3:
            try:
                result = subprocess.run(
                    ["python", "sentinal_orchestrator.py", agent_key, q],
                    capture_output=True, text=True, check=True, timeout=60
                )
                output = result.stdout.strip() or "(no output)"
                break
            except subprocess.TimeoutExpired:
                attempt += 1
                st.warning(f"⚠️ Timeout, retrying ({attempt}/3)...")
                time.sleep(2 ** attempt)
            except subprocess.CalledProcessError as e:
                output = e.stdout or e.stderr or "Agent execution error."
                break
        else:
            output = "❌ Agent failed after 3 attempts."

    dur = round(time.time() - start, 2)
    color = AGENTS[agent_key]["color"]
    st.markdown(
        f"<div class='chat-bubble' style='border-left-color:{color};'>"
        f"<b>{agent_key.upper()}</b><br>{output.replace(chr(10), '<br>')}"
        f"<br><small style='color:#888;'>⏱ {dur}s</small></div>",
        unsafe_allow_html=True
    )
    st.session_state.history.append({
        "agent": agent_key, "query": query_text,
        "response": output, "time": datetime.now().strftime("%H:%M:%S"),
        "runtime_s": dur
    })
    idx = AGENT_SEQUENCE.index(agent_key)
    st.session_state.next_agent = (
        AGENT_SEQUENCE[idx + 1] if idx + 1 < len(AGENT_SEQUENCE) else None
    )
    st.session_state.is_running = False


# ---------- Conversation ----------
st.markdown("### Conversation")
if st.session_state.history:
    for h in st.session_state.history[-10:]:
        c = AGENTS[h["agent"]]["color"]
        st.markdown(
            f"<div class='chat-bubble' style='border-left-color:{c};'>"
            f"<b>{h['agent'].upper()}</b> ({h['time']})<br>{h['response']}</div>",
            unsafe_allow_html=True
        )
else:
    st.info("Start by uploading documents or sending a query to an agent.")


# ---------- Input Bar ----------
st.markdown("<div class='static-input'>", unsafe_allow_html=True)
user_query = st.text_area("Type your prompt here:", height=80,
                          placeholder="Ask Sentinel anything...")

cols = st.columns(2)
with cols[0]:
    if st.button("💬 Ask Agent", use_container_width=True) and user_query.strip():
        run_agent(agent, user_query)
with cols[1]:
    nxt = st.session_state.get("next_agent")
    if nxt and st.button(f"➡ Send to {nxt.upper()}", use_container_width=True):
        run_agent(nxt, user_query)
st.markdown("</div>", unsafe_allow_html=True)


# ---------- Reset ----------
st.markdown("<hr>", unsafe_allow_html=True)
if st.button("🔁 Start New Search", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()
