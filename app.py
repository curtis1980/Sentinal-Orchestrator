# app.py — Sentinel v2.5 (Demo Final)
# -----------------------------------
# Clean, cinematic UI + stable behavior for demo.
# - Dark dot-grid background (no image)
# - Typewriter header (SENTINEL + tagline) that stays visible
# - Tight layout (no extra blank panes)
# - Per-agent multi-turn memory + contextual handoff
# - Real-time “detonator” indicator (threaded)
# - Red handoff line + flash + sonar ping
# - JSON cleanup (no raw JSON dumped in chat)
# - Auto scroll-to-bottom on new messages

import io, os, sys, json, time, threading, subprocess
from datetime import datetime
import streamlit as st

# ---------- Optional parsers (safe to miss) ----------
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

# ---------- CSS (theme, header, chat, footer, indicators, background) ----------
st.markdown("""
<style>
:root {
  --bg:#121212; --surface:#171A1F; --card:#1E232B;
  --text:#F8F8F8; --muted:#A0A6AD; --accent:#E63946; --border:#2C313A;
}
/* Global background: dark dot grid + soft vertical fade */
html, body, [class*="css"]{
  background-color: var(--bg)!important;
  background-image:
    radial-gradient(#00000022 1px, transparent 1px),
    linear-gradient(180deg, #0f0f0f 0%, #171717 100%);
  background-size: 18px 18px, 100% 100%;
  color:var(--text)!important;
  font-family:'Courier New',monospace;
}
.block-container{padding-top:0.25rem; padding-bottom:5.5rem;}
hr{border:0; height:1px; background:var(--border);}

/* Sidebar */
[data-testid="stSidebar"]{
  background-color:#15181c; border-right:1px solid var(--border);
  padding:1rem 1rem 1.25rem 1rem;
}
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label{
  color:var(--accent)!important; font-weight:600;
}
[data-testid="stSidebar"] .stButton>button{
  background:var(--accent); border:none; color:white; border-radius:6px;
  font-weight:600; height:36px;
}
[data-testid="stSidebar"] .stButton>button:hover{ filter:brightness(1.12); }

/* Inputs */
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
.chat-bubble{
  background:rgba(32,37,44,.95); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px;
  padding:12px 14px; margin:10px 0; line-height:1.55; color:var(--text)!important;
  animation:fadeIn .3s ease;
}
.chat-bubble * { color: var(--text)!important; } /* ensure nested md visible */
.chat-bubble.error{ border-left-color:#ff6b6b; color:#ffb3b3; }
.meta{ color:var(--muted); font-size:11px; margin-top:4px; }
@keyframes fadeIn{ from{opacity:0;transform:translateY(4px);} to{opacity:1;transform:translateY(0);} }

/* Footer (fixed) */
.static-footer{
  position:fixed; left:0; right:0; bottom:0;
  background:var(--surface); border-top:2px solid var(--accent);
  box-shadow:0 -3px 12px rgba(0,0,0,.4); z-index:9999;
}
.footer-inner{
  max-width:1100px; margin:0 auto; padding:10px 16px;
  display:flex; gap:10px; align-items:flex-end;
}
.footer-left{ flex:1; }
.footer-right{ width:300px; display:flex; flex-direction:column; gap:8px; }

/* Header (typewriter, stays visible) */
.header-container{ text-align:center; margin-top:10px; margin-bottom:10px; }
.typewriter-title{
  display:inline-block; overflow:hidden; white-space:nowrap;
  border-right:.15em solid var(--accent);
  letter-spacing:.08em; color:var(--accent);
  font-weight:700; font-size:46px;
  animation:typingTitle 2.6s steps(30,end), blink-caret .75s step-end infinite;
  animation-fill-mode:forwards;
}
.typewriter-tagline{
  display:block; overflow:hidden; white-space:nowrap;
  border-right:.15em solid var(--accent);
  letter-spacing:.06em; color:var(--muted);
  font-size:14px; margin-top:6px;
  animation:typingTag 3.4s steps(40,end) 2.7s, blink-caret .75s step-end infinite 2.7s;
  animation-fill-mode:forwards;
}
@keyframes typingTitle{ from{width:0} to{width:100%} }
@keyframes typingTag{ from{width:0} to{width:100%} }
@keyframes blink-caret{ from,to{border-color:transparent} 50%{border-color:var(--accent);} }

/* Indicators */
.detonator{ display:flex; justify-content:center; align-items:center; gap:8px; margin-top:12px; }
.dot{ width:16px; height:16px; border-radius:50%; background-color:#2C313A;
  animation: blink 1.5s infinite; box-shadow:0 0 4px rgba(0,0,0,0.4); }
.dot.active{ background-color:var(--accent); box-shadow:0 0 8px rgba(230,57,70,0.8); }
@keyframes blink{ 0%,100%{opacity:0.4;} 50%{opacity:1;} }
.agent-label{ font-family:'Courier New',monospace; color:var(--accent); font-size:14px; letter-spacing:1px; margin-right:8px; }

.handoff-container{ display:flex; justify-content:center; align-items:center; margin:12px 0; gap:12px; }
.handoff-line{
  width:2px; height:40px; background:linear-gradient(180deg, #E63946 0%, #9B1C1C 100%);
  animation: pulseLine 1.2s infinite; border-radius:2px; box-shadow:0 0 8px rgba(230,57,70,0.6);
  transition: all 0.4s ease-in-out;
}
.handoff-line.flash{
  background:linear-gradient(180deg, #FF3B3B 0%, #FF7575 100%);
  box-shadow:0 0 14px rgba(255,59,59,0.9);
}
.handoff-text{ font-family:'Courier New',monospace; color:var(--accent); font-size:14px; letter-spacing:1px; animation: flickerText 1.5s infinite; }
@keyframes pulseLine{ 0%,100%{opacity:0.6; transform:scaleY(0.95);} 50%{opacity:1; transform:scaleY(1.05);} }
@keyframes flickerText{ 0%,18%,22%,25%,53%,57%,100%{opacity:1;} 20%,24%,55%{opacity:0.4;} }

.signal-flash{
  text-align:center; font-family:'Courier New',monospace; color:var(--accent);
  font-size:14px; letter-spacing:1px; margin-top:6px; animation: flashInOut 1.6s ease-in-out;
  text-shadow:0 0 8px rgba(230,57,70,0.7);
}
@keyframes flashInOut{ 0%{opacity:0; transform:scale(0.95);} 10%,80%{opacity:1; transform:scale(1.03);} 100%{opacity:0; transform:scale(1.05);} }
</style>
""", unsafe_allow_html=True)

# ---------- Sonar ping (inline WAV) ----------
st.markdown("""
<audio id="handoff-beep" preload="auto">
  <source src="data:audio/wav;base64,UklGRoQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQwAAAABAQEBAP8A/wD/AQEBAP8A/wD/AP8A/wEBAQD/AQEBAP8A/wD/AP8A/wEBAQ==" type="audio/wav">
</audio>
<script>
function playHandoffBeep(){
  const beep = window.parent.document.getElementById('handoff-beep');
  if (beep){ try{ beep.currentTime = 0; beep.play(); }catch(e){} }
}
</script>
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
  "cipher":"Governance, PII scrub, policy checks.",
  "proforma":"Formatting and exports for IC memos."
}
AGENT_SEQUENCE=list(AGENTS.keys())
for a in AGENTS: st.session_state["threads"].setdefault(a,[])

def recompute_next():
    i=AGENT_SEQUENCE.index(st.session_state["last_agent"])
    st.session_state["next_agent"]=AGENT_SEQUENCE[i+1] if i+1<len(AGENT_SEQUENCE) else None

# ---------- Sidebar ----------
st.sidebar.markdown("### ⚙️ Orchestrator")
agent=st.sidebar.selectbox("Choose agent",AGENT_SEQUENCE,index=AGENT_SEQUENCE.index(st.session_state["last_agent"]))
st.session_state["last_agent"]=agent; recompute_next()
st.sidebar.caption(AGENTS[agent])
st.sidebar.markdown("---")

files=st.sidebar.file_uploader("📎 Upload files (PDF/DOCX)",type=["pdf","docx"],accept_multiple_files=True)

def _pdf_text(b):
    t=""
    if pdfplumber:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages: t+=(p.extract_text() or "")+"\n"
        except: pass
    if not t.strip() and OCR_AVAILABLE:
        try:
            imgs=convert_from_bytes(b,dpi=200); t="\n".join(pytesseract.image_to_string(i) for i in imgs)
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
        data=f.getvalue(); parsed=_pdf_text(data) if f.name.lower().endswith(".pdf") else _docx_text(data)
        if parsed:texts.append(parsed)
    st.session_state["context"]=("\n\n".join(texts))[:10000]

if st.sidebar.button("🔁 Reset Session",use_container_width=True):
    st.session_state.clear(); st.rerun()

# ---------- Chat (cleaned layout) ----------
thread = st.session_state["threads"][agent]

if thread:
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for item in thread[-15:]:
        css_extra = " error" if item.get("error") else ""
        cleaned = item["response"]

        # Strip accidental JSON blocks if present
        if "```json" in cleaned:
            start = cleaned.find("```json"); end = cleaned.find("```", start + 6)
            if end > start: cleaned = cleaned[:start] + cleaned[end + 3:]
        if cleaned.strip().startswith("{") and cleaned.strip().endswith("}"):
            try:
                _ = json.loads(cleaned); cleaned = "✅ Structured data received (parsed internally)."
            except Exception:
                pass

        st.markdown(
            f"""
            <div class="chat-bubble{css_extra}">
              <b>{item['agent'].upper()}</b><br>
              {cleaned.replace(chr(10), '<br>')}
              <div class="meta">⏱ {item['time']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Select an agent and type your first prompt below.")

# Reduce vertical spacing between chat and footer
st.markdown("<div style='height:36px;'></div>", unsafe_allow_html=True)

# ---------- Helpers ----------
def _compose(user_q:str)->str:
    ctx=st.session_state.get("context","").strip()
    prior=st.session_state["threads"][agent][-10:]
    mem="\n".join(f"ASSISTANT: {m['response']}" for m in prior[-5:])
    base=user_q
    if ctx: base=f"Context:\n{ctx}\n\nUser Query:\n{base}"
    if mem: base=f"Conversation:\n{mem}\n\n{base}"
    return base

def detonator_progress_live(agent_name="AGENT",stop_flag=None,delay=0.25):
    ph=st.empty(); step=0; total=8
    while not stop_flag.is_set():
        dots="".join(f"<div class='dot {'active' if j<=step%total else ''}'></div>" for j in range(total))
        ph.markdown(f"<div class='detonator'><div class='agent-label'>{agent_name.upper()} — PROCESSING</div>{dots}</div>",unsafe_allow_html=True)
        time.sleep(delay); step+=1
    ph.empty()

def show_signal_received(agent_name="AGENT"):
    ph=st.empty()
    ph.markdown(f"<div class='signal-flash'>⚡ SIGNAL RECEIVED — {agent_name.upper()} RESPONSE INBOUND</div>",unsafe_allow_html=True)
    time.sleep(1.6); ph.empty()

def show_handoff_animation(from_agent,to_agent,duration=2.6):
    ph=st.empty()
    ph.markdown(f"<div class='handoff-container'><div class='handoff-line'></div><div class='handoff-text'>HANDOFF IN PROGRESS: {from_agent.upper()} → {to_agent.upper()}</div><div class='handoff-line'></div></div>",unsafe_allow_html=True)
    time.sleep(duration)
    ph.markdown(f"<div class='handoff-container'><div class='handoff-line flash'></div><div class='handoff-text'>HANDOFF COMPLETE — ACTIVATING {to_agent.upper()}</div><div class='handoff-line flash'></div></div><script>playHandoffBeep();</script>",unsafe_allow_html=True)
    time.sleep(0.7); ph.empty()

def _scroll_to_bottom():
    st.markdown("""
    <script>
      setTimeout(() => {
        const chat = window.parent.document.querySelector('.chat-wrap');
        if (chat) chat.scrollTop = chat.scrollHeight;
      }, 500);
    </script>
    """, unsafe_allow_html=True)

# ---------- Agent runner ----------
def run_agent(agent_key,user_q):
    st.toast(f"Routing to agent: {agent_key.upper()}...", icon="🛰️")
    q=_compose(user_q); stop_flag=threading.Event()
    anim=threading.Thread(target=detonator_progress_live,args=(agent_key.upper(),stop_flag)); anim.start()
    output=""; is_error=False
    try:
        res=subprocess.run(["python","sentinal_orchestrator.py",agent_key,q],capture_output=True,text=True,check=False,timeout=90)
        output=(res.stdout or "").strip() or (res.stderr or "").strip()
    except Exception as e:
        output=f"⚠️ Execution error: {e}"; is_error=True
    finally:
        stop_flag.set(); anim.join(); show_signal_received(agent_key)

    # Format JSON into readable Markdown if present
    try:
        jstart=output.find("{"); parsed=json.loads(output[jstart:]) if jstart>=0 else None
        if isinstance(parsed,dict):
            pretty=""
            if parsed.get("summary"):   pretty+=f"**Summary:** {parsed['summary']}\n\n"
            if parsed.get("insights"):  pretty+=f"**Insights:** {parsed['insights']}\n\n"
            if parsed.get("next_steps"):pretty+=f"**Next Steps:** {parsed['next_steps']}"
            output=pretty or output
    except: pass

    st.session_state["threads"][agent_key].append({
        "agent":agent_key,"query":user_q,"response":output,
        "time":datetime.now().strftime("%H:%M:%S"),"error":is_error
    })
    _scroll_to_bottom()
    st.rerun()

# ---------- Footer ----------
st.markdown("""
<div class='static-footer'>
  <div class='footer-inner'>
    <div class='footer-left'></div>
    <div class='footer-right'></div>
  </div>
</div>
""", unsafe_allow_html=True)
left,right=st.empty(),st.empty()
with left.container():
    st.session_state["prompt"]=st.text_area("Type your prompt here:",value=st.session_state["prompt"],key="prompt_box",placeholder=f"Ask {agent.capitalize()}…",height=80)
with right.container():
    ask_btn=st.button("💬 Ask Agent",use_container_width=True)
    nxt=st.session_state.get("next_agent")
    send_next_btn=st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next Agent",use_container_width=True,disabled=(nxt is None))

# ---------- Buttons ----------
user_q=(st.session_state["prompt"] or "").strip()
if ask_btn:
    if user_q:
        run_agent(agent,user_q); st.session_state["prompt"]=""
    else:
        st.warning("Type a question first.")
elif send_next_btn and nxt:
    if st.session_state["threads"][agent]:
        last_resp = st.session_state["threads"][agent][-1]["response"]
        # try to extract summary from pretty text
        summary = last_resp
        try:
            low = last_resp.lower()
            s = low.find("**summary:**")
            i = low.find("**insights:**")
            if s>=0: summary = last_resp[s+11:i].strip() if i>=0 else last_resp[s+11:].strip()
        except: pass
        show_handoff_animation(agent, nxt, duration=2.6)
        run_agent(nxt, summary)
    else:
        st.warning("No output to pass forward from the current agent.")

# ---------- Keyboard shortcut: Ctrl/Cmd + Enter to send ----------
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
