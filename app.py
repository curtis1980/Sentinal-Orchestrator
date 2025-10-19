# app.py — Sentinel v2.6 (Demo Stable Build)
# ------------------------------------------
# Longbow Capital | Sentinel Platform
# Autonomous Agents for Asymmetric Advantage
#
# ✅ Stable dark UI (dot-grid background)
# ✅ Typewriter header (Courier New)
# ✅ Correct chain order (Strata → Dealhawk → Neo → Pro Forma → Cipher)
# ✅ Fixed rerun/agent handoff logic
# ✅ No empty chat window / lighter upload labels
# ✅ Agent overview panel for internal demo use

import io, os, sys, json, time, threading, subprocess
from datetime import datetime
import streamlit as st

# ---------- Optional parsers ----------
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
try:
    from docx import Document
except Exception:
    Document = None

# ---------- Page config ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
:root {
  --bg:#121212; --surface:#171A1F; --card:#1E232B;
  --text:#F8F8F8; --muted:#A0A6AD; --accent:#E63946; --border:#2C313A;
}

/* Background override for Streamlit container */
[data-testid="stAppViewContainer"], html, body {
  background-color: var(--bg)!important;
  background-image:
    radial-gradient(#00000022 1px, transparent 1px),
    linear-gradient(180deg, #0f0f0f 0%, #171717 100%);
  background-size: 18px 18px, 100% 100%;
  color:var(--text)!important;
  font-family:'Courier New', monospace;
}

.block-container{padding-top:0.25rem; padding-bottom:5.5rem; background-color:transparent!important;}
[data-testid="stSidebar"]{
  background-color:#15181c; border-right:1px solid var(--border);
  padding:1rem 1rem 1.25rem 1rem;
}
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label{
  color:var(--accent)!important; font-weight:600;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p{
  color:#e6e6e6!important; font-weight:500;
}
[data-testid="stFileUploader"] svg{
  color:var(--accent)!important; opacity:0.9;
}
[data-testid="stFileUploaderFileName"]{color:#f5f5f5!important; font-weight:600;}
[data-testid="stFileUploaderFileDetails"]{color:#d0d0d0!important;}

.stTextArea textarea{
  background:var(--surface); color:var(--text);
  border:1px solid var(--border); border-radius:8px; height:80px;
  caret-color: var(--text);
}
.stButton>button{
  background:var(--accent); color:#fff; border:0; border-radius:8px;
  height:38px; font-weight:600;
}
.stButton>button:hover{ filter:brightness(1.12); }

/* Chat */
.chat-wrap{
  background:var(--card); border:1px solid var(--border);
  border-radius:12px; padding:16px 18px; height:64vh; overflow-y:auto;
}
.chat-wrap:empty{display:none!important;}
.chat-bubble{
  background:rgba(32,37,44,.95); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px;
  padding:12px 14px; margin:10px 0; line-height:1.55;
  color:var(--text)!important; animation:fadeIn .3s ease;
}
.chat-bubble *{color:var(--text)!important;}
.meta{color:var(--muted); font-size:11px; margin-top:4px;}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}

/* Footer */
.static-footer{position:fixed; left:0; right:0; bottom:0;
  background:var(--surface); border-top:2px solid var(--accent);
  box-shadow:0 -3px 12px rgba(0,0,0,.4); z-index:9999;}
.footer-inner{max-width:1100px; margin:0 auto; padding:10px 16px;
  display:flex; gap:10px; align-items:flex-end;}
.footer-left{flex:1;} .footer-right{width:300px; display:flex; flex-direction:column; gap:8px;}

/* Header */
.header-container{text-align:center; margin-top:20px; margin-bottom:12px; font-family:'Courier New', monospace;}
.typewriter-title{display:inline-block; overflow:hidden; white-space:nowrap;
  border-right:.15em solid var(--accent); color:var(--accent);
  font-weight:700; font-size:46px; letter-spacing:.08em;
  animation:typingTitle 2.6s steps(30,end), blink-caret .75s step-end infinite;
  animation-fill-mode:forwards;}
.typewriter-tagline{display:block; overflow:hidden; white-space:nowrap;
  border-right:.15em solid var(--accent); color:var(--muted);
  font-size:14px; letter-spacing:.06em; margin-top:6px;
  animation:typingTag 3.4s steps(40,end) 2.8s, blink-caret .75s step-end infinite 2.8s;
  animation-fill-mode:forwards;}
@keyframes typingTitle{from{width:0}to{width:100%}}
@keyframes typingTag{from{width:0}to{width:100%}}
@keyframes blink-caret{from,to{border-color:transparent}50%{border-color:var(--accent);}}

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

# ---------- Session state ----------
defaults = {"threads":{}, "context":"", "last_agent":"strata", "is_running":False, "prompt":"", "next_agent":"dealhawk"}
for k,v in defaults.items(): st.session_state.setdefault(k,v)

AGENTS = {
  "strata":"Research & intelligence for energy/decarbonization.",
  "dealhawk":"Deal sourcing for profitable private companies.",
  "neo":"Financial modeling and scenario analysis.",
  "proforma":"Critical review and risk calibration (PFNG).",
  "cipher":"IC assembly and governance validation."
}
AGENT_SEQUENCE = ["strata","dealhawk","neo","proforma","cipher"]

for a in AGENTS: st.session_state["threads"].setdefault(a,[])

def _recompute_next():
    current = st.session_state.get("last_agent", "strata")
    try:
        idx = AGENT_SEQUENCE.index(current)
        st.session_state["next_agent"] = AGENT_SEQUENCE[idx + 1] if idx + 1 < len(AGENT_SEQUENCE) else None
    except ValueError:
        st.session_state["next_agent"] = None

# ---------- Sidebar ----------
st.sidebar.markdown("### ⚙️ Orchestrator")
agent = st.sidebar.selectbox("Choose agent", AGENT_SEQUENCE, index=AGENT_SEQUENCE.index(st.session_state["last_agent"]))
st.session_state["last_agent"] = agent
_recompute_next()
st.sidebar.caption(AGENTS[agent])
st.sidebar.markdown("---")
files = st.sidebar.file_uploader("📎 Upload files (PDF/DOCX)", type=["pdf","docx"], accept_multiple_files=True)

def _pdf_text(b):
    t=""
    if pdfplumber:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages: t+=(p.extract_text() or "")+"\n"
        except: pass
    if not t.strip() and OCR_AVAILABLE:
        try:
            imgs=convert_from_bytes(b,dpi=200)
            t="\n".join(pytesseract.image_to_string(i) for i in imgs)
        except: pass
    return t.strip()

def _docx_text(b):
    if not Document: return ""
    try:
        doc=Document(io.BytesIO(b)); return "\n".join(p.text for p in doc.paragraphs)
    except: return ""

if files:
    texts=[]
    for f in files[:3]:
        data=f.getvalue()
        parsed=_pdf_text(data) if f.name.lower().endswith(".pdf") else _docx_text(data)
        if parsed:texts.append(parsed)
    st.session_state["context"]=("\n\n".join(texts))[:10000]

if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    st.session_state.clear(); st.rerun()

# ---------- Chat ----------
thread = st.session_state["threads"][agent]
if thread:
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for item in thread[-15:]:
        css_extra = " error" if item.get("error") else ""
        cleaned = item["response"]
        if "```json" in cleaned:
            start = cleaned.find("```json"); end = cleaned.find("```", start + 6)
            if end > start: cleaned = cleaned[:start] + cleaned[end + 3:]
        if cleaned.strip().startswith("{") and cleaned.strip().endswith("}"):
            try:
                _ = json.loads(cleaned); cleaned = "✅ Structured data received (parsed internally)."
            except Exception: pass
        st.markdown(
            f"""<div class="chat-bubble{css_extra}">
                <b>{item['agent'].upper()}</b><br>{cleaned.replace(chr(10), '<br>')}
                <div class="meta">⏱ {item['time']}</div></div>""", unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)

# ---------- Helper ----------
def _compose(user_q:str)->str:
    ctx=st.session_state.get("context","").strip()
    prior=st.session_state["threads"][agent][-10:]
    mem="\n".join(f"ASSISTANT: {m['response']}" for m in prior[-5:])
    base=user_q
    if ctx: base=f"Context:\n{ctx}\n\nUser Query:\n{base}"
    if mem: base=f"Conversation:\n{mem}\n\n{base}"
    return base

def _scroll_to_bottom():
    st.markdown("""
    <script>
      setTimeout(() => {
        const chat = window.parent.document.querySelector('.chat-wrap');
        if (chat) chat.scrollTop = chat.scrollHeight;
      }, 500);
    </script>
    """, unsafe_allow_html=True)

# ---------- Agent Runner ----------
def run_agent(agent_key: str, user_q: str):
    if st.session_state["is_running"]: return
    st.session_state["is_running"] = True
    q = _compose(user_q)
    output = ""; is_error = False

    st.toast(f"Routing to agent: {agent_key.upper()}...", icon="🛰️")

    try:
        res = subprocess.run(["python","sentinal_orchestrator.py", agent_key, q],
                             capture_output=True, text=True, check=False, timeout=90)
        output = (res.stdout or "").strip() or (res.stderr or "").strip()
    except Exception as e:
        output = f"⚠️ Execution error: {e}"; is_error = True

    if "threads" not in st.session_state: st.session_state["threads"] = {}
    if agent_key not in st.session_state["threads"]: st.session_state["threads"][agent_key] = []
    st.session_state["threads"][agent_key].append({
        "agent": agent_key, "query": user_q, "response": output,
        "time": datetime.now().strftime("%H:%M:%S"), "error": is_error
    })
    _scroll_to_bottom()
    time.sleep(0.35)
    st.session_state["is_running"] = False
    st.experimental_rerun()

# ---------- Footer ----------
st.markdown("""
<div class='static-footer'><div class='footer-inner'>
  <div class='footer-left'></div><div class='footer-right'></div>
</div></div>
""", unsafe_allow_html=True)
left,right=st.empty(),st.empty()
with left.container():
    st.session_state["prompt"]=st.text_area("Type your prompt here:",
        value=st.session_state["prompt"], key="prompt_box",
        placeholder=f"Ask {agent.capitalize()}…", height=80)
with right.container():
    ask_btn=st.button("💬 Ask Agent", use_container_width=True)
    nxt=st.session_state.get("next_agent")
    send_next_btn=st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next Agent",
                            use_container_width=True, disabled=(nxt is None))

user_q=(st.session_state["prompt"] or "").strip()
if ask_btn:
    if user_q:
        run_agent(agent, user_q); st.session_state["prompt"]=""
    else:
        st.warning("Type a question first.")
elif send_next_btn and nxt:
    if st.session_state["threads"][agent]:
        last_resp = st.session_state["threads"][agent][-1]["response"]
        summary = last_resp
        try:
            low = last_resp.lower()
            s = low.find("**summary:**"); i = low.find("**insights:**")
            if s>=0: summary = last_resp[s+11:i].strip() if i>=0 else last_resp[s+11:].strip()
        except: pass
        time.sleep(0.4)
        run_agent(nxt, summary)
    else:
        st.warning("No output to pass forward from the current agent.")

# ---------- Agent Overview ----------
with st.expander("🧠 Sentinel Agent Overview — Roles & Prompting Guide", expanded=False):
    st.markdown("""
**SENTINEL** is a coordinated suite of autonomous agents for private-market intelligence, sourcing, and decision analysis in energy transition & industrials.  
You can iterate with each agent across multiple turns before handing off to the next.

---

### 🧭 STRATA — Market Mapping
Breaks sectors into clear subsectors and themes; defines where to hunt.
**Best prompts:**
- "Map the North American grid modernization ecosystem."
- "Break down the energy storage value chain by technology and stage."
**Outputs:** hierarchy in Markdown + **Next Steps for Sourcing** (keywords, filters, data sources).

---

### 🦅 DEALHAWK — Deal Sourcing
Finds and profiles companies that fit Longbow’s criteria (private, profitable, Canada).
**Best prompts:**
- "Using the above filters, find 8–10 Canadian private companies in grid analytics."
- "Identify founder-led businesses in industrial electrification with EBITDA > 0."
**Outputs:** company table + **Top 3 to Advance**.

---

### 🧮 NEO — Financial Modeling
Converts qualitative inputs into quantitative scenarios; explains assumptions.
**Best prompts:**
- "Build a base vs. bull case for a battery recycling roll-up."
- "Estimate normalized EBITDA for a controls integrator."
**Outputs:** concise modeling narrative with drivers and scenario deltas.

---

### 📊 PRO FORMA NON GRATA — Critical Review & Risk Calibration
**Mission:** fact-based second-order review of Neo/Dealhawk outputs. Protects capital, not feelings.  
**Objectives:** rebuild thesis from first principles; verify assumptions; find fragility/bias; assign **Risk Intensity Scores (RIS)**; define **counterfactuals**.  
**Core principles:** Capital Preservation First; Evidence over Narrative; Second-Order Thinking; Inversion; Counterfactual Testing.  
**Framework:** Narrative Logic, Financial Integrity, Market Realism, Operational Scalability, Governance & Incentives, Legal & ESG.  
RIS scale: 4.5–5.0 Severe | 3.5–4.4 High | 2.5–3.4 Moderate | 1.0–2.4 Low.  
**Best prompts:**
- "Run PFNG on Neo’s summary; assign RIS and list counterfactuals."
- "Audit assumptions and identify where the numbers disagree with the story."
**Outputs:** **Critical Review Memo** or **IC One-Pager**.

---

### 🔐 CIPHER — Orchestrator & IC Assembly
Decoding layer of Sentinel — composes final IC materials and ensures compliance with Longbow’s thesis.  
**Modes:**  
- `/strata` — market mapping (structured hierarchy + sourcing block)  
- `/dealhawk` — sourcing (10 companies, ≥2 URLs each)  
- `/screen` — scoring (25-pt scale)  
- `/profile` — CRM-ready company profiles (≥2 URLs each)  
**Investment criteria:** Canadian, profitable, founder/family-led, 5–25 yrs; exclude EV infra, Bullfrog Power, Greengate Power, pre-revenue, financings <24m.  
**Best prompts:**  
- "/strata Power & Utilities"  
- "/dealhawk using the above filters"  
- "/screen these companies"  
- "/profile ArcLight Energy Systems Ltd"  
**Outputs:** Markdown-only reports with cited URLs + **Suggested Next Command**.

---

💡 *Tip:* Refine each agent’s output for multiple turns before pressing **Send to Next** — cleaner context, better downstream logic.
""")

# ---------- Keyboard Shortcut ----------
st.markdown("""
# ---------- Keyboard Shortcut ----------
st.markdown("""
<script>
(function(){
  const root = window.parent.document;
  root.addEventListener('keydown', function(e){
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter'){
      const btns = Array.from(root.querySelectorAll('button'));
      const ask = btns.find(b => b.innerText.trim().toLowerCase().includes('ask agent'));
      if (ask) ask.click();
      e.preventDefault();
    }
  }, false);
})();
</script>
""", unsafe_allow_html=True)
