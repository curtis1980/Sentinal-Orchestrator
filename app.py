# app.py — Sentinel v2.8 (Demo Stable Build)
# ------------------------------------------
# Longbow Capital | Sentinel Platform (Streamlit)
# Autonomous Agents for Asymmetric Advantage
#
# ✅ Sequential header animation (title then tagline; caret fades)
# ✅ Ghost textbox removed (dynamic input placeholder)
# ✅ Reliable handoff (sanitize + retry + auto-switch + success toast)
# ✅ Cold War progress indicator (inline; min 4s)
# ✅ Finalize step for Cipher (IC packet + download)
# ✅ Lightened uploader + truncated filenames + size limits
# ✅ Compact console footer + smooth scroll + hover red glow on input
# ✅ Agent chain tracker bar + per-agent accent colors
# ✅ Pinned Context Viewer + Lock Auto-Scroll
# ✅ Satellite “Accessing [AGENT]” badge (pulsing)
# ✅ Basic & structured logging (sentinel_log.txt + sentinel_log.jsonl)
# ✅ Env checks + rate-limit cooldown

import io, os, sys, json, time, subprocess, unicodedata
from datetime import datetime
from typing import List, Tuple, Optional
import streamlit as st

# ---------- Environment checks ----------
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_KEY:
    st.warning("⚠️ OPENAI_API_KEY not set. The orchestrator may fail to respond.", icon="⚠️")

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
st.set_page_config(page_title="Sentinel", page_icon="🛰️", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
:root {
  --bg:#101113; --surface:#14161b; --card:#1a1e24;
  --text:#F0F0F0; --muted:#B0B6BD; --accent:#E63946; --border:#2C313A;
  --ok:#23c55e; --warn:#f59f00; --err:#ef4444;
  /* Agent accents */
  --strata:#14b8a6; --dealhawk:#f59e0b; --neo:#60a5fa; --proforma:#ef4444; --cipher:#9ca3af;
}

/* App-wide dark dot-grid with faint motion layer */
[data-testid="stAppViewContainer"], html, body {
  background-color: var(--bg)!important;
  background-image:
    radial-gradient(#ffffff12 1px, transparent 1px),
    linear-gradient(180deg, #0e0f11 0%, #141518 100%);
  background-size: 18px 18px, 100% 100%;
  color:var(--text)!important;
  font-family:'Courier New', ui-monospace, Menlo, monospace;
}
body::after{
  content:"";
  position:fixed; inset:0;
  pointer-events:none;
  background:repeating-linear-gradient(
    45deg, rgba(230,57,70,.03) 0px, rgba(230,57,70,.03) 2px,
    transparent 2px, transparent 6px);
  animation:bgmove 40s linear infinite;
  z-index:-1;
}
@keyframes bgmove{ from{background-position:0 0;} to{background-position:600px 600px;} }

.block-container{padding-top:0.1rem; padding-bottom:5.0rem; background-color:transparent!important;}
[data-testid="stSidebar"]{
  background-color:#12141a; border-right:1px solid var(--border);
  padding:1rem 1rem 1.25rem 1rem;
}
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label{
  color:var(--accent)!important; font-weight:600;
}

/* File uploader (lightened + truncation) */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p{ color:#e6e6e6!important; font-weight:500; }
[data-testid="stFileUploader"] svg{ color:#c7c7cc!important; opacity:0.85; }
[data-testid="stFileUploaderFileName"]{
  color:#e0e0e0!important; font-weight:500; max-width:240px; display:inline-block;
  overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
}
[data-testid="stFileUploaderFileDetails"]{ color:#b0b0b0!important; font-size:12px; }

/* Header (sequential typewriter; caret fades) */
.header-container{text-align:center; margin-top:14px; margin-bottom:6px;}
.typewriter-line{
  display:inline-block; overflow:hidden; white-space:nowrap; border-right:.15em solid var(--accent);
  width:0; animation:typing 2.5s steps(24,end) 0s 1 normal forwards, caret-fade .8s linear 3.0s 1 forwards;
}
.typewriter-line.title{ color:var(--accent); font-weight:800; font-size:46px; letter-spacing:.08em; }
.typewriter-line.tag{
  color:var(--muted); font-size:14px; letter-spacing:.06em; margin-top:6px; display:block; width:0;
  animation:typing 3.0s steps(36,end) 2.6s 1 normal forwards, caret-fade .8s linear 6.0s 1 forwards;
}
@keyframes typing{from{width:0}to{width:100%}}
@keyframes caret-fade{to{border-right-color:transparent; opacity:0}}

/* Chain tracker */
.chain-bar{ display:flex; justify-content:center; gap:10px; margin:6px 0 8px 0; }
.stage{ padding:4px 10px; border-radius:999px; font-size:12px; border:1px solid var(--border); color:#d7d7d9; opacity:.8 }
.stage.done{ opacity:1; background:#162024; border-color:#26413a; }
.stage.active{ opacity:1; background:#1f2229; border-color:var(--accent); box-shadow:0 0 8px rgba(230,57,70,.18); color:#fff; }

/* Chat */
.chat-wrap{
  background:var(--card); border:1px solid var(--border);
  border-radius:12px; padding:12px 16px; height:58vh; overflow-y:auto;
  scroll-behavior:smooth;
}
.chat-wrap:empty{display:none!important;}
.chat-bubble{
  background:rgba(28,32,39,.95); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px;
  padding:12px 14px; margin:10px 0 8px 0; line-height:1.55;
  color:var(--text)!important; animation:fadeIn .25s ease;
  box-shadow: -2px 0 8px rgba(230,57,70,.12);
}
.chat-bubble.error{ border-left-color: var(--err); }
.chat-bubble.ok{ border-left-color: var(--ok); }

/* Per-agent accent on bubble left border */
.chat-bubble.agent-strata{ border-left-color: var(--strata); box-shadow:-2px 0 8px rgba(20,184,166,.18); }
.chat-bubble.agent-dealhawk{ border-left-color: var(--dealhawk); box-shadow:-2px 0 8px rgba(245,158,11,.18); }
.chat-bubble.agent-neo{ border-left-color: var(--neo); box-shadow:-2px 0 8px rgba(96,165,250,.18); }
.chat-bubble.agent-proforma{ border-left-color: var(--proforma); box-shadow:-2px 0 8px rgba(239,68,68,.18); }
.chat-bubble.agent-cipher{ border-left-color: var(--cipher); box-shadow:-2px 0 8px rgba(156,163,175,.18); }

.chat-bubble *{color:var(--text)!important;}
.meta{color:var(--muted); font-size:11px; margin-top:6px; font-family: ui-monospace, Menlo, monospace;}

/* Inline progress block */
.progress-block{
  background:#14181f; border:1px dashed #334; border-radius:10px;
  padding:10px 12px; margin:8px 0 6px 0;
}
.step{ color:#cfd3d9; font-size:12px; }
.step .hot{ color:var(--accent); font-weight:700; }

/* Footer (console aesthetic + glow + centered) */
.static-footer{
  position:fixed; left:0; right:0; bottom:0;
  background:linear-gradient(180deg,#191b1e 0%, #101214 100%);
  border-top:2px solid var(--accent);
  border-radius:12px 12px 0 0;
  box-shadow:0 -3px 14px rgba(230,57,70,.18), 0 -6px 22px rgba(230,57,70,.08);
  z-index:9999;
}
.footer-inner{
  max-width:1100px; margin:0 auto; padding:12px 16px 14px 16px;
  display:flex; gap:10px; align-items:flex-end;
}
.footer-left{flex:1;}
.footer-right{ width:320px; display:flex; flex-direction:column; gap:10px; }

/* Input & buttons (hover red glow) */
.stTextArea textarea{
  background:var(--surface); color:var(--text);
  border:1px solid var(--border); border-radius:6px; height:60px;
  caret-color: var(--text); transition: all 0.25s ease;
  box-shadow:0 0 0 rgba(230,57,70,0);
}
.stTextArea textarea:hover, .stTextArea textarea:focus{
  border-color:rgba(230,57,70,.6);
  box-shadow:0 0 8px rgba(230,57,70,.3);
  outline:none;
}
.stButton>button{
  background:var(--accent); color:#fff; border:0; border-radius:8px;
  height:36px; font-weight:700; padding:0 10px;
}
.secondary>button{
  background:var(--surface)!important; color:var(--text)!important;
  border:1px solid var(--border)!important;
}
.stButton>button:hover{ filter:brightness(1.08); }

/* Toast tweak */
[data-testid="stToast"]{ right: 16px!important; left: auto!important; }

/* Expander styling */
details[data-testid="stExpander"]{
  background:#14161b!important; border:1px solid var(--border)!important;
  border-radius:10px!important;
}
details[data-testid="stExpander"] > summary{ color:#e8e8e8!important; }

/* Thin hr */
hr { border:0; border-top:1px solid var(--border); margin:6px 0 8px 0; }

/* Live Agent Access Badge */
.agent-badge {
  position: fixed; top: 12px; right: 18px;
  background: rgba(230,57,70,0.12);
  color: var(--accent);
  border: 1px solid rgba(230,57,70,0.35);
  border-radius: 10px;
  padding: 6px 12px 6px 10px;
  font-size: 13px; letter-spacing: 0.03em;
  box-shadow: 0 0 12px rgba(230,57,70,0.15);
  backdrop-filter: blur(4px);
  animation: badgePulse 1.6s ease-in-out infinite;
  z-index: 99999;
}
@keyframes badgePulse{
  0%{ box-shadow:0 0 6px rgba(230,57,70,.12); transform:translateY(0); }
  50%{ box-shadow:0 0 12px rgba(230,57,70,.25); transform:translateY(1px); }
  100%{ box-shadow:0 0 6px rgba(230,57,70,.12); transform:translateY(0); }
}

@keyframes fadeIn{from{opacity:0;transform:translateY(3px);}to{opacity:1;transform:translateY(0);}}

/* Hide Streamlit menu/headers if desired (kept minimal) */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class="header-container">
  <div class="typewriter-line title">SENTINEL</div><br/>
  <div class="typewriter-line tag">Autonomous Agents for Asymmetric Advantage</div>
</div>
""", unsafe_allow_html=True)

# ---------- Chain Tracker ----------
AGENTS = {
  "strata":"Research & intelligence for energy/decarbonization.",
  "dealhawk":"Deal sourcing for profitable private companies.",
  "neo":"Financial modeling and scenario analysis.",
  "proforma":"Critical review and risk calibration (PFNG).",
  "cipher":"IC assembly and governance validation."
}
AGENT_SEQUENCE = ["strata","dealhawk","neo","proforma","cipher"]

def chain_tracker(active_key:str):
    items=[]
    for i,k in enumerate(AGENT_SEQUENCE):
        cls = "stage"
        if k == active_key: cls += " active"
        elif AGENT_SEQUENCE.index(active_key) > i: cls += " done"
        label = k.upper()
        items.append(f"<div class='{cls}'>{label}</div>")
    st.markdown(f"<div class='chain-bar'>{''.join(items)}</div><hr/>", unsafe_allow_html=True)

# ---------- Session state ----------
defaults = {
    "threads":{},
    "context":"",              # uploads text
    "last_agent":"strata",
    "is_running":False,
    "prompt":"",               # current prompt entry
    "next_agent":"dealhawk",
    "handoff_preview":"",      # preview of handoff content
    "lock_scroll":False,       # disable auto-scroll when reading
    "handoff_toast":""         # shows success toast after rerun
}
for k,v in defaults.items(): st.session_state.setdefault(k,v)
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

MAX_UPLOAD_MB = 10
files = st.sidebar.file_uploader("📎 Upload files (PDF/DOCX)", type=["pdf","docx"], accept_multiple_files=True)
st.sidebar.checkbox("📌 Lock auto-scroll", key="lock_scroll", value=st.session_state["lock_scroll"])

def _clean_utf8(text:str, limit:int=40000)->str:
    if not text: return ""
    text = unicodedata.normalize("NFC", text)
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return text[:limit]

def _pdf_text(b: bytes) -> str:
    t=""
    if pdfplumber:
        try:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                for p in pdf.pages: t+=(p.extract_text() or "")+"\n"
        except: pass
    if (not t.strip()) and OCR_AVAILABLE:
        try:
            imgs=convert_from_bytes(b,dpi=200)
            t="\n".join(pytesseract.image_to_string(i) for i in imgs)
        except: pass
    return _clean_utf8(t.strip())

def _docx_text(b: bytes) -> str:
    if not Document: return ""
    try:
        doc=Document(io.BytesIO(b))
        text="\n".join(p.text for p in doc.paragraphs)
        return _clean_utf8(text)
    except:
        return ""

# Process uploads with size limit
if files:
    texts=[]
    for f in files[:3]:
        size_mb = (len(f.getvalue())/ (1024*1024))
        if size_mb > MAX_UPLOAD_MB:
            st.sidebar.error(f"'{f.name}' is {size_mb:.1f} MB (> {MAX_UPLOAD_MB} MB). Please upload a smaller file.", icon="⚠️")
            continue
        data=f.getvalue()
        parsed=_pdf_text(data) if f.name.lower().endswith(".pdf") else _docx_text(data)
        if parsed:
            texts.append(f"# {f.name}\n{parsed}")
            # Inline parsing feedback into chat:
            st.session_state["threads"][agent].append({
                "agent":"system",
                "query":"",
                "response":f"📄 `{f.name}` processed ({len(parsed.split()):,} words, {'OCR ✓' if (not parsed and OCR_AVAILABLE) else 'Parsed ✓'})",
                "time": datetime.now().strftime("%H:%M:%S"),
                "error": False,
                "meta":"parse"
            })
    if texts:
        st.session_state["context"]=("\n\n".join(texts))[:40000]

if st.sidebar.button("🔁 Reset Session", use_container_width=True):
    st.session_state.clear(); st.rerun()

# ---------- Chain Tracker Render ----------
chain_tracker(agent)

# ---------- Context Viewer (pinned expander) ----------
with st.expander("📄 Context Viewer (uploads)", expanded=False):
    ctx = st.session_state.get("context","").strip()
    st.caption(f"Characters: {len(ctx):,} (cap 40,000)")
    st.text_area("Context", value=ctx, height=220, label_visibility="collapsed")

# ---------- Chat Transcript ----------
thread = st.session_state["threads"][agent]
if thread:
    st.markdown('<div class="chat-wrap" id="chatwrap">', unsafe_allow_html=True)
    for item in thread[-24:]:
        # class for per-agent accent; map system/meta to current agent style for continuity
        akey = item.get('agent', agent)
        aclass = f"agent-{akey}" if akey in AGENT_SEQUENCE else f"agent-{agent}"
        css_extra = " error" if item.get("error") else (" ok" if item.get("meta")=="final" else "")
        cleaned = item["response"]
        # hide large JSON/code fences visually
        if "```json" in cleaned:
            start = cleaned.find("```json"); end = cleaned.find("```", start + 6)
            if end > start: cleaned = cleaned[:start] + "✅ Structured data received (parsed internally)." + cleaned[end + 3:]
        if cleaned.strip().startswith("{") and cleaned.strip().endswith("}"):
            try:
                _ = json.loads(cleaned)
                cleaned = "✅ Structured data received (parsed internally)."
            except Exception:
                pass

        # token/latency strip (approx token count from chars)
        tokens_est = int(max(1, len(item.get('response',''))/4))  # rough 4 chars/token
        metrics = item.get('metrics','')
        meta_strip = f"≈{tokens_est:,} tok" + (f" · {metrics}" if metrics else "")

        st.markdown(
            f"""<div class="chat-bubble {aclass}{css_extra}">
                <b>{akey.upper()}</b><br>{cleaned.replace(chr(10), '<br>')}
                <div class="meta">{meta_strip} · ⏱ {item['time']}</div></div>""",
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Helpers ----------
def _compose(user_q:str)->str:
    ctx=_clean_utf8(st.session_state.get("context",""))
    prior=st.session_state["threads"][agent][-10:]
    mem="\n".join(f"ASSISTANT: {m['response']}" for m in prior if m.get('agent')==agent)[-3000:]
    base=_clean_utf8(user_q, 12000)
    if ctx: base=f"Context:\n{ctx}\n\nUser Query:\n{base}"
    if mem: base=f"Conversation:\n{mem}\n\n{base}"
    return base

def _scroll_to_bottom():
    if st.session_state.get("lock_scroll", False):  # do nothing when locked
        return
    st.markdown("""
    <script>
      setTimeout(() => {
        const chat = window.parent.document.querySelector('#chatwrap');
        if (chat) chat.scrollTop = chat.scrollHeight;
      }, 350);
    </script>
    """, unsafe_allow_html=True)

# ---------- Subprocess helpers ----------
ESPIONAGE_STEPS = [
    "Establishing secure link…",
    "Decrypting intercepts…",
    "Cross-checking HUMINT…",
    "Synthesizing brief…",
    "Transmission received."
]

def _sanitize_for_subprocess(text:str, cap:int=5000)->str:
    if not text: return ""
    t = text.replace("\n"," ").replace("\r"," ")
    t = t.replace('"', "'")
    t = " ".join(t.split())  # collapse whitespace
    return t[:cap]

def _run_agent_subprocess(agent_key:str, payload:str, timeout_sec:int=90) -> Tuple[str, str, int]:
    """
    Returns (stdout, stderr, returncode). Retries once if stdout empty.
    """
    cmd = ["python","sentinal_orchestrator.py", agent_key, payload]
    start = time.time()

    def _exec():
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout_sec)
            return (res.stdout or "").strip(), (res.stderr or "").strip(), res.returncode
        except subprocess.TimeoutExpired:
            return "", f"TimeoutExpired after {timeout_sec}s", 124
        except Exception as e:
            return "", f"Execution error: {e}", 125

    out, err, rc = _exec()
    # Retry once if stdout empty but not a hard error
    if not out.strip() and rc in (0, 124) and "error" not in (err or "").lower():
        time.sleep(2.0)
        out2, err2, rc2 = _exec()
        if out2.strip():
            out, err, rc = out2, err2, rc2

    dur_ms = int((time.time()-start)*1000)
    return out, err, rc

# ---------- Agent Runner with inline progress ----------
def run_agent(agent_key: str, user_q: str, is_handoff: bool=False):
    # Rate-limit basic cooldown to avoid spam
    now = time.time()
    last_click = st.session_state.get("last_click_ts", 0)
    if now - last_click < 1.2:
        st.warning("Slow down — processing in progress.", icon="⏱️")
        return
    st.session_state["last_click_ts"] = now

    if st.session_state["is_running"]: return
    st.session_state["is_running"] = True

    q_full = _compose(user_q) if not is_handoff else user_q
    payload = _sanitize_for_subprocess(q_full)
    output = ""; is_error = False; metrics = ""

    # Satellite badge
    st.markdown(f"<div class='agent-badge'>🛰️ Accessing <b>{agent_key.upper()}</b></div>", unsafe_allow_html=True)

    # Inline progress block
    prog_holder = st.empty()
    bar = st.progress(0, text="🛰️ Establishing secure link…")
    with prog_holder.container():
        st.markdown('<div class="progress-block"><div class="step"><span class="hot">SIGINT</span> uplink active</div></div>', unsafe_allow_html=True)

    # Animate steps for min duration
    min_ms = 4000
    step_count = len(ESPIONAGE_STEPS)
    start_ms = int(time.time()*1000)
    for i,step in enumerate(ESPIONAGE_STEPS):
        bar.progress(min(80, int((i+1)/step_count*80)), text=f"🛰️ {step}")
        time.sleep(0.7 if i < step_count-1 else 0.4)

    # Execute subprocess
    s0 = time.time()
    stdout, stderr, rc = _run_agent_subprocess(agent_key, payload, timeout_sec=90)
    dur_ms = int((time.time()-s0)*1000)

    # Ensure minimum visible time
    elapsed_ms = int(time.time()*1000) - start_ms
    if elapsed_ms < min_ms:
        time.sleep((min_ms - elapsed_ms)/1000)

    # Finalize progress
    bar.progress(100, text="🛰️ Transmission received")
    time.sleep(0.25)
    prog_holder.empty()
    # Remove badge
    st.markdown("<script>const b=document.querySelector('.agent-badge'); if(b) b.remove();</script>", unsafe_allow_html=True)

    if rc != 0 or (not stdout and stderr):
        is_error = True
        output = stderr or (stdout or "⚠️ No output received.")
    else:
        output = stdout or "⚠️ Empty response."
    metrics = f"duration {dur_ms} ms"

    # Append to thread
    if "threads" not in st.session_state: st.session_state["threads"] = {}
    if agent_key not in st.session_state["threads"]: st.session_state["threads"][agent_key] = []
    st.session_state["threads"][agent_key].append({
        "agent": agent_key, "query": user_q, "response": output,
        "time": datetime.now().strftime("%H:%M:%S"), "error": is_error,
        "metrics": metrics
    })

    # Simple logs
    try:
        with open("sentinel_log.txt","a",encoding="utf-8") as lf:
            lf.write(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] {agent_key} | {metrics} | in:{len(payload)} out:{len(output)} rc:{rc}\n")
    except: pass
    try:
        with open("sentinel_log.jsonl","a",encoding="utf-8") as jf:
            jf.write(json.dumps({
                "ts": datetime.now().isoformat(),
                "agent": agent_key,
                "duration_ms": dur_ms,
                "input_chars": len(payload),
                "output_chars": len(output),
                "rc": rc,
                "error": is_error
            })+"\n")
    except: pass

    _scroll_to_bottom()
    st.session_state["is_running"] = False
    st.rerun()

# ---------- Footer (dynamic input placeholder: only when idle) ----------
st.markdown("""
<div class='static-footer'><div class='footer-inner'>
  <div class='footer-left' id='footer-left'></div><div class='footer-right' id='footer-right'></div>
</div></div>
""", unsafe_allow_html=True)

left_placeholder = st.empty()
right_placeholder = st.empty()

if not st.session_state["is_running"]:
    with left_placeholder.container():
        st.session_state["prompt"]=st.text_area(
            "Type your prompt here:",
            value=st.session_state["prompt"],
            key="prompt_box",
            placeholder=f"Ask {agent.capitalize()}…",
            height=60,
            label_visibility="collapsed"
        )
    with right_placeholder.container():
        ask_btn=st.button("💬 Ask Agent", use_container_width=True)
        nxt=st.session_state.get("next_agent")
        if agent == "cipher":
            finalize_btn = st.button("🔒 Finalize IC Packet", use_container_width=True)
            send_next_btn = None
        else:
            send_next_btn=st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next Agent",
                                    use_container_width=True,
                                    disabled=(nxt is None),
                                    key="send_next_btn",
                                    type="secondary")
            finalize_btn = None
else:
    left_placeholder.empty()
    right_placeholder.empty()

# ---------- Post-rerun toast (handoff) ----------
if st.session_state.get("handoff_toast"):
    st.toast(f"📡 Handoff complete → {st.session_state['handoff_toast'].upper()} ready.", icon="✅")
    st.session_state["handoff_toast"] = ""

# ---------- Actions ----------
user_q=(st.session_state.get("prompt") or "").strip()

if not st.session_state.get("is_running", False):
    if agent == "cipher" and 'finalize_btn' in locals() and finalize_btn:
        # Collate last responses across the chain
        bundle = []
        for a in AGENT_SEQUENCE:
            last = st.session_state["threads"][a][-1]["response"] if st.session_state["threads"][a] else ""
            bundle.append(f"## {a.upper()}\n{last}\n")
        packet = "\n".join(bundle).strip() or "No content available."
        # Write file & offer download
        try:
            with open("ic_packet.txt","w",encoding="utf-8") as f:
                f.write(packet)
        except: pass
        st.session_state["threads"][agent].append({
            "agent":"cipher","query":"","response":"> Transmission Complete – IC Packet Saved",
            "time": datetime.now().strftime("%H:%M:%S"), "error": False, "meta":"final"
        })
        st.download_button("⬇ Download IC Packet", data=packet.encode("utf-8"),
                           file_name="ic_packet.txt", mime="text/plain")
        _scroll_to_bottom()

    elif 'ask_btn' in locals() and ask_btn:
        if user_q:
            st.session_state["prompt"] = ""
            run_agent(agent, user_q)
        else:
            st.warning("Type a question first.")

    elif 'send_next_btn' in locals() and send_next_btn:
        nxt = st.session_state.get("next_agent")
        if nxt and st.session_state["threads"][agent]:
            last_resp = st.session_state["threads"][agent][-1]["response"]
            # Extract a safe summary (simple fallback)
            summary = last_resp
            try:
                low = last_resp.lower()
                s = low.find("**summary:**"); i = low.find("**insights:**")
                if s>=0: summary = last_resp[s+11:i].strip() if i>=0 else last_resp[s+11:].strip()
            except: pass
            summary = _sanitize_for_subprocess(summary, cap=5000)
            st.session_state["handoff_preview"] = summary[:300]
            st.session_state["handoff_toast"] = nxt  # show on next load
            # Run next agent with handoff payload
            run_agent(nxt, f"Handoff from {agent.upper()}:\n{summary}", is_handoff=True)
            # After run_agent triggers rerun, we want to land on next agent
            st.session_state["last_agent"] = nxt
            _recompute_next()
        else:
            st.warning("No output to pass forward from the current agent.")

# ---------- Agent Overview ----------
with st.expander("🧠 Sentinel Agent Overview — Roles & Prompting Guide", expanded=False):
    st.markdown("""
**SENTINEL** is a coordinated suite of autonomous agents for private-market intelligence, sourcing, and decision analysis in energy transition & industrials.  
Refine with each agent for multiple turns before handing off to the next.

---

### 🧭 STRATA — Market Mapping
Role: map sectors, TAM/SAM/SOM, value chains, regulatory signals.  
**Best prompts:**
- "Map the North American grid modernization ecosystem."
- "Break down the energy storage value chain by technology and stage."
**Outputs:** hierarchy in Markdown + Next Steps for Sourcing.

---

### 🦅 DEALHAWK — Deal Sourcing
Role: discover targets and build shortlists; quick profiles for fit.  
**Best prompts:**
- "Using the above filters, find 8–10 Canadian private companies in grid analytics."
- "Identify founder-led businesses in industrial electrification with EBITDA > 0."
**Outputs:** ranked shortlist + Top 3 to advance.

---

### 🧮 NEO — Financial Modeling
Role: scrub data, model unit economics, run scenarios.  
**Best prompts:**
- "Build base vs. bull case for a battery recycling roll-up."
- "Estimate normalized EBITDA for a controls integrator."
**Outputs:** scenario diffs and drivers.

---

### 📊 PRO FORMA NON GRATA — Critical Review & Risk Calibration
Mission: adversarial second-order review; assign **Risk Intensity Scores (RIS)** and define **counterfactuals**.  
**Best prompts:**
- "Run PFNG on Neo’s summary; assign RIS and list counterfactuals."
- "Audit assumptions and identify where numbers disagree with the story."
**Outputs:** Critical Review Memo / IC One-Pager.

---

### 🔐 CIPHER — IC Assembly & Governance Validation
Role: compile IC materials, decision log, approvals checklist.  
**Best prompts:**  
- "/strata Power & Utilities"  
- "/dealhawk using the above filters"  
- "/screen these companies"  
- "/profile ArcLight Energy Systems Ltd"  
**Outputs:** IC-ready packet: thesis, risks, KPIs, go/no-go grid.
""")

# ---------- Keyboard Shortcut (Ctrl/Cmd + Enter = Ask Agent) ----------
st.markdown("""
<script>
(function(){
  const root = window.parent.document;
  root.addEventListener('keydown', function(e){
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter'){
      const btns = Array.from(root.querySelectorAll('button'));
      const ask = btns.find(b => b.innerText.trim().toLowerCase().includes('ask agent'));
      if (ask) { e.preventDefault(); ask.click(); }
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')){
      e.preventDefault();
    }
  }, true);
})();
</script>
""", unsafe_allow_html=True)
