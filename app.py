# ---------- SENTINEL v4.1 (DEMO-STABLE BUILD) ----------
import streamlit as st
# --- backward-compatibility shim ---
if not hasattr(st, "experimental_rerun"):
    st.experimental_rerun = st.rerun

st.set_page_config(page_title="SENTINEL", layout="wide")

# ---------- GLOBAL STYLE ----------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stSidebar"], .stApp, .main, .block-container {
  background-color:#0D0F12 !important; color:#F8F8F8 !important;
  font-family:'Courier New', monospace !important;
}
.stButton>button {background:#E63946 !important; color:#fff !important;
  border:none !important; border-radius:6px !important; font-weight:600 !important;
  box-shadow:0 0 8px rgba(230,57,70,.28);}
.stButton>button:hover{background:#FF465A !important;}
.chat-pane{background:#1E232B; border:1px solid #1C232C; border-radius:8px;
  padding:16px 18px; height:50vh; overflow-y:auto;}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
state = st.session_state
if "app_mode" not in state: state.app_mode = "intro"
if "threads" not in state: state.threads = {}
if "prompt" not in state: state.prompt = ""

# ---------- CINEMATIC INTRO ----------
if state.app_mode == "intro":
    placeholder = st.empty()
    placeholder.markdown("""
    <div style="height:90vh;display:flex;flex-direction:column;justify-content:center;align-items:center;
                text-align:center;font-family:'Courier New',monospace;">
      <div style="color:#E63946;font-size:42px;letter-spacing:.10em;font-weight:800;
                  border-right:3px solid #E63946;white-space:nowrap;overflow:hidden;
                  animation:typing 2.6s steps(9,end), blink .8s step-end 3;">
        SENTINEL
      </div>
      <div style="color:#A8B2BD;margin-top:10px;">AUTHENTICATING SESSION…</div>
      <div style="color:#9AA6B1;margin-top:8px;font-size:13px;text-align:left;line-height:1.6;">
        🛰 INITIALIZING NODES…<br>
        <span style="color:#48FF7F;">✅ STRATA NODE ONLINE</span><br>
        <span style="color:#48FF7F;">✅ DEALHAWK NODE ONLINE</span><br>
        <span style="color:#48FF7F;">✅ NEO NODE ONLINE</span><br>
        <span style="color:#48FF7F;">✅ PFNG NODE ONLINE</span><br>
        <span style="color:#48FF7F;">✅ CIPHER SECURE CHANNEL</span>
      </div>
    </div>
    <style>
    @keyframes typing {from {width:0ch;} to {width:10ch;}}
    @keyframes blink {0%,50%{border-color:#E63946;}51%,100%{border-color:transparent;}}
    </style>
    """, unsafe_allow_html=True)
    time.sleep(4.5)
    placeholder.empty()
    state.app_mode = "console"
    st.experimental_rerun()

# ---------- MAIN CONSOLE ----------
st.markdown("""
<div style="text-align:center;margin-top:8px;">
  <div style="color:#E63946;font-size:42px;font-weight:800;">SENTINEL</div>
  <div style="color:#A8B2BD;font-size:15px;">Autonomous Agents for Asymmetric Advantage</div>
</div>
<hr style="margin:14px 0 20px;">
""", unsafe_allow_html=True)

AGENTS = {
    "strata": "Research & intelligence for energy/decarbonization.",
    "dealhawk": "Deal sourcing for private companies.",
    "neo": "Financial modeling & scenario analysis.",
    "proforma": "Risk calibration & diligence (PFNG).",
    "cipher": "IC assembly & governance validation."
}
CHAIN = {"strata":"dealhawk","dealhawk":"neo","neo":"proforma","proforma":"cipher","cipher":None}

c1,c2,c3 = st.columns([1,2,1])
with c2:
    agent = st.selectbox("Choose agent", list(AGENTS.keys()), index=0, key="agent_select")
st.caption(f"⚙ {AGENTS[agent]}")

# ---------- CHAT PANEL ----------
thread = state.threads.get(agent, [])
if thread:
    st.markdown('<div class="chat-pane">', unsafe_allow_html=True)
    for msg in thread[-10:]:
        st.markdown(f"""
        <div style='border-left:3px solid #E63946;padding:8px 10px;margin:6px 0;color:#F8F8F8;'>
            <b>{msg['agent'].upper()}</b><br>{msg['response']}
            <div style='color:#9AA6B1;font-size:11px;margin-top:3px;'>⏱ {msg['time']}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No messages yet.")

# ---------- PROMPT ----------
st.markdown(f"<div style='color:#A8B2BD;'>Type your prompt for {agent.upper()}:</div>", unsafe_allow_html=True)
user_prompt = st.text_area("", placeholder=f"Ask {agent.capitalize()}…", height=90, label_visibility="collapsed", key="prompt_box")

# ---------- BACKEND SAFE CALL ----------
def call_orchestrator(agent_key, query):
    try:
        result = subprocess.run(
            [sys.executable, "sentinal_orchestrator.py", agent_key, query],
            capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        if "error" in data:
            return f"⚠️ {data['error']}"
        return data.get("output", str(data))
    except FileNotFoundError:
        return f"[DEMO RESPONSE] Simulated output from {agent_key.upper()}."
    except subprocess.TimeoutExpired:
        return f"⏱️ {agent_key.upper()} timed out."
    except Exception as e:
        return f"💥 {type(e).__name__}: {e}"

def store(agent_key, text):
    msg = {"agent": agent_key, "response": text, "time": datetime.now().strftime("%H:%M:%S")}
    state.threads.setdefault(agent_key, []).append(msg)

# ---------- CONTROLS ----------
c1,c2,c3 = st.columns([4,2,2])
with c1:
    if st.button("🔁 Reset Session", use_container_width=True):
        for k in ["threads","prompt_box"]: state.pop(k, None)
        st.experimental_rerun()
with c2:
    if st.button("💬 Ask Agent", use_container_width=True):
        q = state.get("prompt_box","").strip()
        if not q: st.warning("Enter a prompt."); st.stop()
        with st.spinner(f"⚙️ ACCESSING {agent.upper()} NODE..."):
            out = call_orchestrator(agent,q)
        store(agent,out)
        st.success("✅ RESPONSE RECEIVED"); st.experimental_rerun()
with c3:
    if st.button("➡ Send to Next", use_container_width=True):
        nxt = CHAIN.get(agent)
        if not nxt: st.info("No next agent in chain."); st.stop()
        prev = state.threads.get(agent, [])
        if not prev: st.warning("No output to forward."); st.stop()
        data = prev[-1]["response"][:2000]
        with st.spinner(f"➡ Forwarding to {nxt.upper()}..."):
            out = call_orchestrator(nxt,data)
        store(nxt,out)
        st.success(f"✅ {nxt.upper()} RESPONSE RECEIVED"); st.experimental_rerun()

