# app.py — Sentinel Beta v1.4
import streamlit as st
import subprocess
import time
from datetime import datetime
from io import BytesIO
from docx import Document
import fitz  # PyMuPDF for PDFs
import os

# =========================================================
# Sentinel Header
# =========================================================
st.set_page_config(page_title="Sentinel", layout="centered")

st.markdown("""
<div style="
    text-align:center;
    background-color:#0a0a0a;
    padding:50px 0 30px 0;
    border-bottom:3px solid #e63946;
">
    <h1 style="color:#f2f2f2;font-size:46px;font-weight:800;letter-spacing:2px;margin-bottom:10px;">
        SENTINEL
    </h1>
    <h4 style="color:#e63946;font-weight:600;letter-spacing:1.5px;margin-top:0;">
        AUTONOMOUS AGENTS FOR ASYMMETRIC ADVANTAGE
    </h4>
</div>
""", unsafe_allow_html=True)

# =========================================================
# Sentinel Theme
# =========================================================
st.markdown("""
<style>
body, .main, .block-container {
    background-color:#0a0a0a !important;
    color:#f2f2f2 !important;
    font-family:'Inter',sans-serif;
}
.chat-container {
    height:65vh;
    overflow-y:auto;
    background-color:#111;
    border:1px solid #1f1f1f;
    border-radius:8px;
    padding:16px;
    box-shadow:inset 0 0 8px rgba(0,0,0,0.5);
    scroll-behavior:smooth;
    font-size:15px;
}
.input-area {
    position:sticky;
    bottom:0;
    background-color:#0a0a0a;
    border-top:1px solid #222;
    padding:12px;
    box-shadow:0 -2px 10px rgba(0,0,0,0.3);
    backdrop-filter:blur(6px);
}
.bubble {
    padding:14px 16px;
    border-radius:10px;
    margin:10px 0;
    color:#fff;
    line-height:1.4em;
    box-shadow:0 1px 3px rgba(0,0,0,0.4);
    transition:all 0.2s ease;
}
.bubble:hover {box-shadow:0 0 8px rgba(230,57,70,0.4);}
.bubble.strata {background:#123524;}
.bubble.dealhawk {background:#3a2f0b;}
.bubble.neo {background:#102941;}
.bubble.cipher {background:#2d1b4a;}
.bubble.proforma {background:#2e1d1f;}
div.stButton > button:first-child {
    background-color:#e63946 !important;
    color:#fff !important;
    border:1px solid #e63946 !important;
    font-weight:600 !important;
    border-radius:6px !important;
}
div.stButton > button:first-child:hover {
    background-color:#ff4d5a !important;
    color:white !important;
}
textarea {
    background-color:#111 !important;
    color:#fff !important;
    border:1px solid #333 !important;
}
hr {border:0;border-top:1px solid #333;margin-top:25px;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# Agent Registry
# =========================================================
AGENTS = {
    "strata": {"color":"#123524","desc":"Research and intelligence agent for energy and decarbonization ecosystems."},
    "dealhawk": {"color":"#3a2f0b","desc":"Deal sourcing agent identifying late-stage, profitable private companies in energy transition."},
    "neo": {"color":"#102941","desc":"Analytical agent that builds financial models, pro formas, and scenario simulations."},
    "cipher": {"color":"#2d1b4a","desc":"Security and coordination agent managing communication between other agents."},
    "proforma": {"color":"#2e1d1f","desc":"Automates and validates private-equity financial assumptions and model inputs."}
}
AGENT_SEQUENCE = list(AGENTS.keys())

# =========================================================
# Session State Setup
# =========================================================
st.session_state.setdefault("history", [])
st.session_state.setdefault("uploaded_text", None)
st.session_state.setdefault("uploaded_filename", None)
st.session_state.setdefault("last_agent", None)
st.session_state.setdefault("last_response", None)
st.session_state.setdefault("next_agent", None)
st.session_state.setdefault("is_running", False)

# =========================================================
# File Processing Helpers
# =========================================================
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text("text")
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

# =========================================================
# Core Agent Runner
# =========================================================
def run_agent(agent, query):
    if st.session_state.is_running:
        return
    st.session_state.is_running = True
    start = time.time()
    with st.spinner(f"Running {agent.upper()}..."):
        try:
            result = subprocess.run(
                ["python", "sentinal_orchestrator.py", agent, query],
                capture_output=True, text=True, check=True
            )
            output = "\n".join([ln for ln in result.stdout.splitlines() if ln.strip()])
            duration = round(time.time() - start, 2)
            st.markdown(
                f"<div class='bubble {agent}'><b>{agent.upper()}:</b><br>{output.replace(chr(10), '<br>')}"
                f"<br><small>⏱ {duration}s</small></div>",
                unsafe_allow_html=True
            )
            st.session_state.history.append({
                "agent": agent,
                "query": query,
                "response": output,
                "time": datetime.now().strftime("%H:%M:%S")
            })
            st.session_state.last_agent = agent
            st.session_state.last_response = output
            idx = AGENT_SEQUENCE.index(agent)
            st.session_state.next_agent = (
                AGENT_SEQUENCE[idx+1] if idx+1 < len(AGENT_SEQUENCE) else None
            )
        except subprocess.CalledProcessError as e:
            st.error(f"⚠ Agent Error: {e.stderr or e.stdout or 'Unknown issue'}")
        finally:
            st.session_state.is_running = False

# =========================================================
# Chat Console
# =========================================================
st.markdown("### 🧠 Sentinel Console")
st.markdown("<div class='chat-container' id='chatbox'>", unsafe_allow_html=True)
if st.session_state.history:
    for h in st.session_state.history[-10:]:
        st.markdown(
            f"<div class='bubble {h['agent']}'><b>{h['agent'].upper()}:</b><br>{h['response'].replace(chr(10), '<br>')}</div>",
            unsafe_allow_html=True
        )
else:
    st.markdown("<p style='color:#666;'>No conversations yet. Start by asking an agent below.</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# File Upload + Processing
# =========================================================
st.markdown("### 📎 Upload a Document for Diligence")
uploaded_file = st.file_uploader("Drag and drop a PDF or DOCX file (max 10MB)", type=["pdf","docx"])

if uploaded_file:
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("⚠ File too large. Please upload a file under 10 MB.")
    else:
        with st.spinner("Extracting text..."):
            try:
                if uploaded_file.type == "application/pdf":
                    text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                    text = extract_text_from_docx(uploaded_file)
                else:
                    st.error("Unsupported file format.")
                    text = None
                if text:
                    st.session_state.uploaded_text = text
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.success(f"✅ {uploaded_file.name} uploaded and processed successfully.")
            except Exception as e:
                st.error(f"Error processing file: {e}")

# =========================================================
# Input Bar (Sticky)
# =========================================================
st.markdown("<div class='input-area'>", unsafe_allow_html=True)
agent = st.selectbox("Choose an agent:", AGENT_SEQUENCE)
query = st.text_area("Type your prompt here:", key="user_query", placeholder="Ask your agent something...")

col1, col2, col3 = st.columns([1,1,1])
ask_clicked = col1.button("💬 Ask Same Agent", use_container_width=True)
next_agent = st.session_state.get("next_agent")
next_label = f"➡ Send to {next_agent.upper()}" if next_agent else "➡ Send to Next Agent"
next_clicked = col2.button(next_label, use_container_width=True)
analyze_clicked = col3.button("📄 Analyze Uploaded Document", use_container_width=True)

if ask_clicked:
    if query.strip():
        run_agent(agent, query)
        st.session_state.user_query = ""
    else:
        st.warning("Please enter a query first.")

if next_clicked:
    if next_agent and query.strip():
        run_agent(next_agent, query)
        st.session_state.user_query = ""
    elif not next_agent:
        st.warning("No next agent available — start with STRATA.")
    else:
        st.warning("Please enter a query first.")

if analyze_clicked:
    if st.session_state.uploaded_text:
        with st.spinner("Analyzing document..."):
            doc_summary = st.session_state.uploaded_text[:4000]  # truncate for token safety
            query = f"Analyze the following document for key insights, risks, and investment relevance:\n\n{doc_summary}"
            run_agent(agent, query)
    else:
        st.warning("Please upload a PDF or DOCX file first.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# Reset Session
# =========================================================
st.markdown("<hr>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("🔁 Start New Search", use_container_width=True):
        with st.spinner("🧠 Clearing session and resetting Sentinel..."):
            time.sleep(1)
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.success("✅ Ready for a fresh search!")
            time.sleep(0.8)
            st.experimental_rerun()

# =========================================================
# Auto-scroll JS
# =========================================================
st.markdown("""
<script>
var chatBox = window.parent.document.querySelector('#chatbox');
if (chatBox) { chatBox.scrollTop = chatBox.scrollHeight; }
</script>
""", unsafe_allow_html=True)
