# app.py
import streamlit as st
import subprocess
import time
from datetime import datetime
import base64
from docx import Document
import pdfplumber

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sentinel | Longbow Capital", layout="centered")

# --- CUSTOM STYLES ---
st.markdown("""
<style>
body {
    background-color: #0E0E0E;
    color: #E5E5E5;
    font-family: 'Inter', sans-serif;
}

.sentinel-header {
    margin-bottom: 20px;
}

img:hover {
    opacity: 1.0;
    transition: 0.25s ease-in-out;
    transform: scale(1.02);
}

.divider {
    border-bottom: 1px solid #333;
    margin: 20px 0 30px 0;
}

.sentinel-title {
    font-size: 38px;
    font-weight: 700;
    color: #F3F3F3;
    letter-spacing: 1px;
}

.sentinel-sub {
    font-size: 15px;
    color: #C0C0C0;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.chat-container {
    max-height: 550px;
    overflow-y: auto;
    padding-right: 10px;
    margin-bottom: 120px;
}

.chat-bubble {
    background-color: #1B1B1B;
    border-left: 4px solid #E74C3C;
    padding: 12px;
    border-radius: 10px;
    margin: 8px 0;
}

.static-input {
    position: fixed;
    bottom: 20px;
    left: 0;
    right: 0;
    background-color: #0E0E0E;
    padding: 10px 20px;
    border-top: 1px solid #222;
    box-shadow: 0px -1px 4px rgba(0, 0, 0, 0.3);
}
</style>
""", unsafe_allow_html=True)

# --- LONG BOW BRANDING HEADER ---
def load_logo(path: str):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = load_logo("Longbow-Capital_Logo.png")

st.markdown(f"""
<div class="sentinel-header" style="display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:14px;">
    <img src="data:image/png;base64,{logo_base64}" width="190" style="margin-right:10px;opacity:0.9;">
    <div>
      <div class="sentinel-title">SENTINEL</div>
      <div class="sentinel-sub">Autonomous Agents for Asymmetric Advantage</div>
    </div>
  </div>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# --- AGENTS CONFIG ---
AGENTS = {
    "strata": {"color": "#4CAF50", "desc": "Research and intelligence agent for energy and decarbonization ecosystems."},
    "dealhawk": {"color": "#FF9800", "desc": "Deal sourcing agent identifying late-stage, profitable private companies in energy transition."},
    "neo": {"color": "#2196F3", "desc": "Analytical agent that builds financial models and scenario simulations."},
    "cipher": {"color": "#9C27B0", "desc": "Security and coordination agent managing cross-agent communication."},
    "proforma": {"color": "#795548", "desc": "Automates and validates private equity financial assumptions and model inputs."}
}
AGENT_SEQUENCE = list(AGENTS.keys())

# --- SESSION STATE ---
st.session_state.setdefault("history", [])
st.session_state.setdefault("last_agent", None)
st.session_state.setdefault("last_response", None)
st.session_state.setdefault("next_agent", None)
st.session_state.setdefault("is_running", False)

# --- FILE UPLOAD HANDLER ---
uploaded_file = st.file_uploader("📎 Upload a PDF or DOCX (max 10MB):", type=["pdf", "docx"])
file_text = ""
if uploaded_file:
    file_size = len(uploaded_file.getbuffer())
    if file_size > 10 * 1024 * 1024:
        st.error("⚠️ File too large. Please upload files under 10 MB.")
    else:
        try:
            if uploaded_file.name.endswith(".pdf"):
                with pdfplumber.open(uploaded_file) as pdf:
                    file_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            elif uploaded_file.name.endswith(".docx"):
                doc = Document(uploaded_file)
                file_text = "\n".join([p.text for p in doc.paragraphs])
            st.success(f"✅ {uploaded_file.name} uploaded and parsed successfully.")
        except Exception as e:
            st.error(f"⚠️ Failed to read file: {e}")

# --- AGENT RUNNER FUNCTION ---
def run_agent(agent, query):
    if st.session_state.is_running:
        return
    st.session_state.is_running = True
    start = time.time()

    full_query = f"{query}\n\n(File context: {file_text[:2000]}...)" if file_text else query

    with st.spinner(f"Running {agent.upper()}..."):
        try:
            result = subprocess.run(
                ["python", "sentinal_orchestrator.py", agent, full_query],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout.strip()
            duration = round(time.time() - start, 2)

            st.markdown(
                f"<div class='chat-bubble' style='border-left:4px solid {AGENTS[agent]['color']};'>"
                f"<b>{agent.upper()}:</b><br>{output.replace(chr(10), '<br>')}<br>"
                f"<small style='color:#888;'>⏱ {duration}s</small></div>",
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
            st.session_state.next_agent = AGENT_SEQUENCE[idx + 1] if idx + 1 < len(AGENT_SEQUENCE) else None
        except subprocess.CalledProcessError as e:
            st.error(f"⚠️ Agent Error: {e.stderr or e.stdout or 'Unknown issue'}")
        finally:
            st.session_state.is_running = False

# --- MAIN CHAT AREA ---
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
if st.session_state.history:
    for item in st.session_state.history[-10:]:
        st.markdown(
            f"<div class='chat-bubble' style='border-left:4px solid {AGENTS[item['agent']]['color']};'>"
            f"<b>{item['agent'].upper()}</b> ({item['time']}): {item['response']}</div>",
            unsafe_allow_html=True
        )
st.markdown("</div>", unsafe_allow_html=True)

# --- STATIC INPUT BAR (BOTTOM) ---
st.markdown("<div class='static-input'>", unsafe_allow_html=True)
agent = st.selectbox("Choose an agent:", AGENT_SEQUENCE)
query = st.text_area("Type your prompt here:", placeholder="Ask your agent something...")
cols = st.columns(2)
with cols[0]:
    if st.button("💬 Ask Same Agent", use_container_width=True):
        if query.strip():
            run_agent(agent, query)
        else:
            st.warning("Please enter a query.")
with cols[1]:
    next_agent = st.session_state.get("next_agent")
    if next_agent:
        if st.button(f"➡️ Send to {next_agent.upper()}", use_container_width=True):
            if query.strip():
                run_agent(next_agent, query)
            else:
                st.warning("Please enter a query.")
st.markdown("</div>", unsafe_allow_html=True)

# --- RESET SESSION ---
st.markdown("<hr>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔁 Start New Search", use_container_width=True):
        with st.spinner("🧠 Clearing session and resetting Sentinel..."):
            time.sleep(1)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ Ready for a fresh search!")
            time.sleep(0.5)
            st.experimental_rerun()
