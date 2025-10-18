# app.py — Sentinel v1.2 enterprise build
import io, os, time, base64, subprocess
from datetime import datetime
from typing import List, Tuple

import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from docx import Document
import pandas as pd

# ---------- CONFIG ----------
st.set_page_config(page_title="Sentinel", layout="wide")
MAX_FILE_MB = 10
MAX_FILES = 3
PARSE_TIMEOUT = 60

DARK_BG = "#0E0E0E"
ACCENT = "#E63946"
SURFACE = "#15171C"
CARD = "#1C1F26"
TEXT = "#E6E6E6"
SUBTLE = "#A6A8AD"

# ---------- STYLE ----------
st.markdown(f"""
<style>
html, body, [class*="css"] {{
  background-color: {DARK_BG} !important;
  color: {TEXT} !important;
  font-family: 'Inter', sans-serif;
}}
.block-container {{padding-bottom:8rem;}}
img:hover {{
  opacity:1; transform:scale(1.02); transition:0.25s ease-in-out;
}}
.chat-bubble {{
  border-left:4px solid {ACCENT};
  background:{CARD}; padding:14px; border-radius:10px; margin:10px 0;
}}
.static-input {{
  position:fixed; bottom:0; left:0; right:0;
  background:{DARK_BG}; border-top:1px solid #222; padding:12px 20px;
  backdrop-filter:blur(4px); z-index:999;
}}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
st.session_state.setdefault("history", [])
st.session_state.setdefault("telemetry", [])
st.session_state.setdefault("context_text", "")
st.session_state.setdefault("is_running", False)

# ---------- HELPERS ----------
def _size_mb(file): return len(file.getbuffer()) / (1024 * 1024)

def extract_text_pdf(file_bytes: bytes) -> Tuple[str, bool]:
    """Extract text; fallback to OCR if empty."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception:
        pass
    if text.strip():
        return text, False  # not OCR

    # OCR fallback
    try:
        images = convert_from_bytes(file_bytes)
        ocr_text = []
        for img in images:
            ocr_text.append(pytesseract.image_to_string(img))
        return "\n".join(ocr_text), True
    except Exception:
        return "", True

def extract_text_docx(file_bytes: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

def parse_files(files) -> Tuple[str, float]:
    """Return combined text + confidence estimate."""
    total_bytes, all_text = 0, []
    for f in files[:MAX_FILES]:
        total_bytes += len(f.getbuffer())
        name = f.name.lower()
        data = f.getvalue()
        txt = ""
        ocr = False
        if name.endswith(".pdf"):
            txt, ocr = extract_text_pdf(data)
        elif name.endswith(".docx"):
            txt = extract_text_docx(data)
        if txt:
            all_text.append(txt)
    combined = "\n\n".join(all_text)
    mb = max(total_bytes / (1024 * 1024), 0.001)
    coverage = min(len(combined) / (mb * 5000), 2.0)
    return combined[:15000], coverage

def run_agent(agent: str, query: str, ctx: str):
    if st.session_state.is_running: return
    st.session_state.is_running = True
    start = time.time()

    full_query = f"{query}\n\n[Attached Context]\n{ctx[:4000]}" if ctx else query
    retries = 3
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["python", "sentinal_orchestrator.py", agent, full_query],
                text=True, capture_output=True, check=True, timeout=60
            )
            out = result.stdout.strip()
            break
        except Exception as e:
            out = f"Error: {e}"
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
    duration = round(time.time() - start, 2)
    st.session_state.history.append({
        "agent": agent, "query": query, "response": out,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    st.session_state.telemetry.append({
        "ts": datetime.now(), "agent": agent, "runtime_s": duration,
        "tokens_est": len(full_query)//4, "success": "Error" not in out
    })
    st.session_state.is_running = False
    st.markdown(f"<div class='chat-bubble'><b>{agent.upper()}</b><br>{out}</div>", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown(f"""
<h2 style='color:{TEXT};'>🧠 SENTINEL</h2>
<p style='color:{SUBTLE};margin-top:-10px;'>Autonomous Agents for Asymmetric Advantage</p>
<hr style='border:1px solid {ACCENT};opacity:0.5;'>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### ⚙️ Agent Orchestrator")
    agents = ["strata","dealhawk","neo","cipher","proforma"]
    agent = st.selectbox("Choose an agent:", agents)
    st.markdown("---")

    st.markdown("### 📎 Upload Files (PDF/DOCX)")
    files = st.file_uploader(
        "Up to 3 files (10 MB each)", type=["pdf","docx"], accept_multiple_files=True
    )
    ctx = ""
    if files:
        too_big = [f.name for f in files if _size_mb(f) > MAX_FILE_MB]
        if too_big:
            st.error(f"Files too large: {', '.join(too_big)}")
        else:
            with st.spinner("Parsing files..."):
                ctx, conf = parse_files(files)
                if ctx:
                    st.success(f"Extracted {len(ctx):,} chars • confidence ~{int(min(conf,1.0)*100)}%")
                    st.session_state.context_text = ctx
                else:
                    st.warning("No text extracted (possibly scanned image).")

    if st.session_state.context_text:
        with st.expander("🗂 Preview Extracted Text"):
            st.text_area("Parsed content (trimmed)", st.session_state.context_text[:4000], height=200)

    # -------- Session Insights --------
    st.markdown("---")
    with st.expander("📊 Session Insights", expanded=False):
        if st.session_state.telemetry:
            df = pd.DataFrame(st.session_state.telemetry)
            st.dataframe(df.tail(3), use_container_width=True)
            st.caption(f"Total tokens ≈ {df['tokens_est'].sum():,}")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Export CSV Logs", data=csv, file_name="sentinel_logs.csv", mime="text/csv")
        else:
            st.caption("No runs yet.")

    st.markdown("---")
    if st.button("🔁 Start New Session", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.experimental_rerun()

# ---------- CHAT HISTORY ----------
if st.session_state.history:
    for h in st.session_state.history[-10:]:
        st.markdown(
            f"<div class='chat-bubble'><b>{h['agent'].upper()}</b> ({h['time']}):<br>{h['response']}</div>",
            unsafe_allow_html=True)
else:
    st.info("Start by uploading documents or typing a prompt below.")

# ---------- STATIC INPUT ----------
st.markdown("<div class='static-input'>", unsafe_allow_html=True)
cols = st.columns([4,1,1])
with cols[0]:
    query = st.text_input("💬 Type your prompt and press Enter", "")
with cols[1]:
    if st.button("Ask Same"):
        if query.strip(): run_agent(agent, query, st.session_state.get("context_text",""))
with cols[2]:
    nxt = agents[agents.index(agent)+1] if agents.index(agent)+1 < len(agents) else None
    if nxt and st.button(f"Next → {nxt.upper()}"):
        if query.strip(): run_agent(nxt, query, st.session_state.get("context_text",""))
st.markdown("</div>", unsafe_allow_html=True)
