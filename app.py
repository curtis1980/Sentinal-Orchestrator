# app.py — Sentinel v3.2 (Espionage Console)
# -----------------------------------------------------------
# UX + Aesthetic pass (no password gate):
# - Secure-entry boot animation (first load per session)
# - Cinematic header glint, noise film overlay, subtle blue underglow
# - Unified chat (top) → prompt + buttons (below)
# - Typing indicator, relative timestamps, chain breadcrumb
# - Alternating chat bubbles; "redacted shimmer" on long messages
# - Fixed-width agent selector; Send→Next handoff corrected
# - Reliable subprocess calls with retry, caps, and safe defaults

import io, os, json, time, subprocess, re
from datetime import datetime, timezone
import streamlit as st

SENTINEL_VERSION = "v3.2"

# ---------- Optional parsers ----------
try: import pdfplumber
except Exception: pdfplumber = None
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False
try: from docx import Document
except Exception: Document = None

# ---------- Page config ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- CSS (theme, espionage styling) ----------
st.markdown(f"""
<style>
:root {{
  --bg:#0d0f12; --surface:#151920; --card:#1A1F27;
  --text:#F3F6FB; --muted:#9AA3AD; --accent:#E63946; --accent-blue:#48A8FF;
  --border:#2B323C;
}}
/* Hide Streamlit chrome */
[data-testid="stHeader"], [data-testid="stToolbar"], header, body>header {{ display:none!important; }}
html,body {{
  margin:0!important; padding:0!important; overflow-x:hidden!important;
  background: var(--bg); color:var(--text)!important; font-family:'Courier New', monospace;
}}
/* Background grid + blue underglow */
[data-testid="stAppViewContainer"] {{
  background:
   radial-gradient(#00000026 1px, transparent 1px) 0 0 / 18px 18px,
   radial-gradient(ellipse at top, #0c1220 0%, #0d0f12 55%);
}}
/* Film grain overlay */
body::before {{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:1;
  background-image:url("data:image/svg+xml;utf8,\
  <svg xmlns='http://www.w3.org/2000/svg' width='140' height='140' viewBox='0 0 140 140'>\
  <filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/><feComponentTransfer><feFuncA type='table' tableValues='0 0 0 0 .05 .08 .05 0 0 0 0'/></feComponentTransfer></filter>\
  <rect width='100%' height='100%' filter='url(%23n)' opacity='.65'/></svg>");
  mix-blend-mode:soft-light; opacity:.25; animation:grainMove 12s steps(8,end) infinite;
}}
@keyframes grainMove {{ 0%{{transform:translate3d(0,0,0)}} 100%{{transform:translate3d(-10%,10%,0)}} }}

/* Content wrapper */
.content-inner {{ max-width:1100px; margin:0 auto; padding:0 1.2rem 4rem; position:relative; z-index:2; }}

/* Header with glint */
.header-container {{ text-align:center; margin:14px 0 6px; }}
.typewriter-title {{
  display:inline-block; position:relative; overflow:hidden; white-space:nowrap;
  color:var(--accent); font-weight:800; font-size:46px; letter-spacing:.10em;
  animation:typingTitle 4.4s steps(40,end) forwards;
}}
.typewriter-title::after {{
  content:""; position:absolute; inset:0; transform:translateX(-120%);
  background:linear-gradient(115deg, transparent 20%, rgba(255,255,255,.15) 50%, transparent 80%);
  animation:glint 10s linear infinite 3s;
}}
@keyframes typingTitle {{ from{{width:0}} to{{width:100%}} }}
@keyframes glint {{ 0%{{transform:translateX(-120%)}} 100%{{transform:translateX(120%)}} }}
.typewriter-tagline {{
  opacity:0; display:block; color:var(--muted); font-size:14px; letter-spacing:.06em; margin-top:6px;
  animation:fadeInTag 1.6s ease forwards; animation-delay:4.8s;
}}
@keyframes fadeInTag {{ from{{opacity:0}} to{{opacity:1}} }}

/* Chain breadcrumb */
.chain {{ color:var(--muted); font-size:12px; letter-spacing:.06em; text-align:center; margin:4px 0 10px; }}
.chain b {{ color:var(--text); }}

/* Agent selector (fixed width, centered) */
.agent-wrap {{ max-width:340px; margin:0 auto 6px auto; }}
.agent-wrap .stSelectbox div[data-baseweb="select"] > div {{ background:#11161c; border:1px solid var(--accent); border-radius:6px; box-shadow:0 0 6px #E6394622; }}
.version-label {{ color:var(--muted); font-size:12px; text-align:right; }}

/* Chat window */
.chat-container {{
  background:var(--card); border:1px solid var(--border);
  border-radius:12px; padding:16px 18px; height:60vh; overflow-y:auto; margin:10px 0 12px;
  box-shadow:0 10px 30px rgba(0,0,0,.35);
}}
.bubble {{
  background:rgba(30,36,45,.95); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px;
  padding:12px 14px; margin:10px 0; line-height:1.55; color:var(--text);
  animation:fadeIn .25s ease;
}}
.bubble.alt {{ background:rgba(26,32,44,.95); border-left-color:var(--accent-blue); }}
.bubble.error {{ border-left-color:#FFB703; background:#2a1c1c; }}
.meta {{ color:var(--muted); font-size:11px; margin-top:4px; }}
@keyframes fadeIn {{ from{{opacity:0;transform:translateY(4px)}} to{{opacity:1;transform:none}} }}

/* Redacted shimmer for long messages */
.redacted {{
  background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(72,168,255,.08) 50%, rgba(255,255,255,0) 100%);
  background-size: 200% 100%; animation:shimmer 7s ease-in-out infinite;
}}
@keyframes shimmer {{ 0%{{background-position:200% 0}} 100%{{background-position:-200% 0}} }}

/* Typing indicator bubble */
.typing {{
  display:inline-block; padding:10px 12px; border-radius:8px; border:1px solid var(--border);
  background:#1e2530; color:#cdd6df;
}}
.typing .dot {{ height:6px; width:6px; margin:0 2px; display:inline-block; background:#cdd6df; border-radius:50%; animation:blink 1.2s infinite; }}
.typing .dot:nth-child(2){{ animation-delay:.2s; }} .typing .dot:nth-child(3){{ animation-delay:.4s; }}
@keyframes blink {{ 0%,80%,100%{{opacity:.2}} 40%{{opacity:1}} }}

/* Input block (command style) */
.input-block {{ margin-top:8px; }}
.stTextArea textarea {{
  background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:8px; height:92px;
  caret-color:var(--text); transition:all .2s ease;
  background-image:linear-gradient(180deg, rgba(72,168,255,.05), transparent 40%);
}}
.stTextArea textarea::placeholder {{ color:#9aa3ad; }}
.stTextArea textarea:hover {{ border-color:#8B0000; box-shadow:0 0 10px #48A8FF22; }}
.buttons-row {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:8px; }}
.buttons-row .stButton>button {{
  background:var(--accent); color:#fff; border:0; border-radius:8px; height:40px; font-weight:700;
  box-shadow:0 8px 18px rgba(230,57,70,.18), inset 0 0 0 1px #ffffff08;
  transition:transform .12s ease, filter .12s ease, box-shadow .2s ease;
}}
.buttons-row .stButton>button:hover {{ filter:brightness(1.1); box-shadow:0 10px 22px rgba(72,168,255,.18), inset 0 0 0 1px #48A8FF22; transform:translateY(-1px); }}
.buttons-row .stButton>button:disabled {{ opacity:.6; cursor:not-allowed; transform:none; }}

/* Footer tag */
.footer-tag {{ margin-top:10px; text-align:center; color:#7f8b96; font-size:11px; letter-spacing:.12em; }}
.footer-tag b {{ color:#a4b1bd; }}

/* Status chip */
.status-chip{{ position:fixed; top:10px; right:14px; background:#1f242b; border:1px solid var(--border); color:#fff;
  padding:6px 10px; border-radius:999px; font-size:12px; box-shadow:0 2px 10px rgba(0,0,0,.25); z-index:10000; }}
.status-dot{{ width:8px; height:8px; display:inline-block; border-radius:50%; background:var(--accent); margin-right:6px;
  animation:pulse 1.2s ease-in-out infinite; }}
@keyframes pulse {{ 0%,100%{{opacity:.4}} 50%{{opacity:1}} }}
</style>
""", unsafe_allow_html=True)

# ---------- Session ----------
defaults = {
    "threads": {}, "context": "", "last_agent": "strata", "next_agent": "dealhawk",
    "is_running": False, "active_agent": None, "prompt": "",
    "entry_done": False,   # secure-entry animation gate
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

AGENTS = {
  "strata":   "Research & intelligence for energy/decarbonization.",
  "dealhawk": "Deal sourcing for profitable private companies.",
  "neo":      "Financial modeling and scenario analysis.",
  "proforma": "Critical review and risk calibration (PFNG).",
  "cipher":   "IC assembly and governance validation."
}
AGENT_SEQUENCE = ["strata","dealhawk","neo","proforma","cipher"]
for a in AGENTS: st.session_state["threads"].setdefault(a, [])

def _recompute_next():
    cur = st.session_state.get("last_agent","strata")
    try:
        i = AGENT_SEQUENCE.index(cur)
        st.session_state["next_agent"] = AGENT_SEQUENCE[i+1] if i+1 < len(AGENT_SEQUENCE) else None
    except ValueError:
        st.session_state["next_agent"] = None

# ---------- Helpers ----------
def _compose(user_q: str) -> str:
    ctx = (st.session_state.get("context") or "").strip()
    prior = st.session_state["threads"][agent][-5:]
    mem = "\n".join(f"{m['agent'].upper()}: {m['response'][:400]}" for m in prior if m.get("response"))
    base = user_q
    if ctx: base = f"Context:\n{ctx}\n\n{base}"
    if mem: base = f"Recent Discussion:\n{mem}\n\n{base}"
    return base

def _extract_summary(resp: str, fallback_len: int = 1600) -> str:
    if not resp: return ""
    try:
        js = resp.rfind("{")
        if js != -1:
            parsed = json.loads(resp[js:])
            s = parsed.get("summary","")
            if isinstance(s,str) and s.strip(): return s.strip()[:fallback_len]
    except: pass
    m = re.search(r'(?i)(?:\\*\\*summary\\*\\*:|^#*\\s*summary\\s*:?)\\s*(.+?)(?:\\n\\s*\\n|$)', resp, re.S|re.M)
    if m: return m.group(1).strip()[:fallback_len]
    clean = re.sub(r'<[^>]+>','', resp).strip()
    return clean[:fallback_len]

def _cap(text: str, limit: int = 8000) -> str:
    return text if len(text) <= limit else text[:limit-20] + " …[truncated]"

def _rel_time(ts_str: str) -> str:
    # expects "%H:%M:%S" today; fallback to raw
    try:
        now = datetime.now()
        ts = datetime.strptime(ts_str, "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)
        delta = (now - ts).total_seconds()
        if delta < 60: return f"{int(delta)}s ago"
        if delta < 3600: return f"{int(delta//60)}m ago"
        return f"{int(delta//3600)}h ago"
    except:
        return ts_str

# ---------- Secure-entry animation (first load only) ----------
if not st.session_state["entry_done"]:
    ph = st.empty()
    with ph.container():
        st.markdown("""
        <div style="height:80vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:10px;">
          <div style="font-size:40px;color:#E63946;letter-spacing:.10em;font-weight:800;">SENTINEL</div>
          <div style="color:#9AA3AD;">AUTHENTICATING SESSION…</div>
        </div>
        """, unsafe_allow_html=True)
        # tiny boot scroll
        boot = st.empty()
        with boot.container():
            st.markdown("<div style='color:#9AA3AD;text-align:center;'>🛰 INITIALIZING NODES…</div>", unsafe_allow_html=True); time.sleep(0.6)
            st.markdown("<div style='color:#9AA3AD;text-align:center;'>✅ STRATA NODE ONLINE</div>", unsafe_allow_html=True); time.sleep(0.4)
            st.markdown("<div style='color:#9AA3AD;text-align:center;'>✅ DEALHAWK NODE ONLINE</div>", unsafe_allow_html=True); time.sleep(0.4)
            st.markdown("<div style='color:#9AA3AD;text-align:center;'>✅ NEO NODE ONLINE</div>", unsafe_allow_html=True); time.sleep(0.3)
            st.markdown("<div style='color:#9AA3AD;text-align:center;'>✅ PFNG NODE ONLINE</div>", unsafe_allow_html=True); time.sleep(0.3)
            st.markdown("<div style='color:#9AA3AD;text-align:center;'>✅ CIPHER SECURE CHANNEL</div>", unsafe_allow_html=True); time.sleep(0.4)
    st.session_state["entry_done"] = True
    st.rerun()

# ---------- HEADER ----------
st.markdown("""
<div class="header-container">
  <div class="typewriter-title">SENTINEL</div>
  <div class="typewriter-tagline">Autonomous Agents for Asymmetric Advantage</div>
</div>
<hr/>
""", unsafe_allow_html=True)

# chain breadcrumb + version
chain_html = " &rarr; ".join([f"<b>{a.upper()}</b>" if i==0 else a.capitalize() for i,a in enumerate(AGENT_SEQUENCE)])
st.markdown(f"<div class='chain'>{chain_html}<span style='float:right'>{SENTINEL_VERSION}</span></div>", unsafe_allow_html=True)

# ---------- CONTENT WRAP ----------
st.markdown("<div class='content-inner'>", unsafe_allow_html=True)

# Agent selector (fixed width centered)
st.markdown("<div class='agent-wrap'>", unsafe_allow_html=True)
agent = st.selectbox("Choose agent", AGENT_SEQUENCE, index=AGENT_SEQUENCE.index(st.session_state["last_agent"]))
st.markdown("</div>", unsafe_allow_html=True)
st.session_state["last_agent"] = agent
_recompute_next()
st.caption(AGENTS[agent])

# ---------- Status chip ----------
if st.session_state.get("is_running") and st.session_state.get("active_agent"):
    st.markdown(
        f"<div class='status-chip'><span class='status-dot'></span>🛰 {st.session_state['active_agent'].upper()} RUNNING…</div>",
        unsafe_allow_html=True
    )

# ---------- CHAT (top) ----------
thread = st.session_state["threads"][agent]
st.markdown('<div class="chat-container" id="chatwrap">', unsafe_allow_html=True)
if thread:
    for idx, m in enumerate(thread[-18:]):
        resp = (m.get("response") or "")
        # long messages get shimmer class
        long_class = " redacted" if len(resp) > 1200 else ""
        klass = "bubble"
        if m.get("error"): klass += " error"
        elif idx % 2 == 1: klass += " alt"
        # escape -> render with <br>
        safe = resp.replace(chr(10), "<br>")
        meta = _rel_time(m.get("time",""))
        st.markdown(
            f"""<div class="{klass}{long_class}">
                <b>{m['agent'].upper()}</b><br>{safe}
                <div class="meta">{meta}</div>
            </div>""",
            unsafe_allow_html=True
        )
else:
    st.markdown('<div style="color:#9AA3AD;text-align:center;margin-top:22vh;">No messages yet.</div>', unsafe_allow_html=True)

# typing indicator when running
if st.session_state.get("is_running"):
    st.markdown("""
    <div style="margin-top:8px;"><span class="typing">
    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </span></div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- INPUT (below chat) ----------
st.markdown("<div class='input-block'>", unsafe_allow_html=True)
st.session_state["prompt"] = st.text_area(
    "Type your prompt:", value=st.session_state.get("prompt",""),
    key="prompt_box", placeholder=f">_ Ask {agent.capitalize()}…", height=92
)
colA, colB = st.columns(2)
with colA:
    ask_btn = st.button("💬 Ask Agent", use_container_width=True, disabled=st.session_state.get("is_running", False))
with colB:
    nxt = st.session_state.get("next_agent")
    send_btn = st.button(f"➡ Send to {nxt.upper()}" if nxt else "No Next",
                         use_container_width=True, disabled=(nxt is None or st.session_state.get("is_running", False)))
st.markdown("</div>", unsafe_allow_html=True)

# ---------- Agent Runner ----------
def run_agent(agent_key: str, user_q: str):
    if st.session_state.get("is_running") or not user_q.strip(): return
    st.session_state["is_running"] = True
    st.session_state["active_agent"] = agent_key
    st.toast(f"🛰 Accessing {agent_key.upper()}...", icon="🔴")

    composed = _cap(_compose(user_q), 8000)
    attempts, output, is_error = 0, "", False
    start_t = time.time()

    while attempts < 2:
        attempts += 1
        try:
            res = subprocess.run(
                ["python","sentinal_orchestrator.py",agent_key,composed],
                capture_output=True, text=True, check=False, timeout=120
            )
            stdout = (res.stdout or "").strip()
            stderr = (res.stderr or "").strip()
            output = stdout if stdout else stderr
            if output: break
        except Exception as e:
            output = f"⚠️ Execution error: {e}"
            is_error = True
        time.sleep(0.6)  # small backoff

    elapsed = time.time() - start_t
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["threads"][agent_key].append({
        "agent": agent_key, "query": user_q, "response": output or "⚠️ No output received.",
        "time": ts, "error": is_error or (not bool(output)), "elapsed": round(elapsed,2)
    })

    st.session_state["is_running"] = False
    st.session_state["active_agent"] = None
    st.session_state["prompt"] = ""
    st.experimental_rerun()

# ---------- Actions ----------
user_q = (st.session_state.get("prompt") or "").strip()
if ask_btn:
    run_agent(agent, user_q)
elif send_btn and nxt:
    if st.session_state["threads"][agent]:
        last_resp = st.session_state["threads"][agent][-1].get("response","")
        summary = _extract_summary(last_resp, 1600)
        st.session_state["last_agent"] = nxt   # advance selection for UI + state
        _recompute_next()
        run_agent(nxt, summary or last_resp[:1600])
    else:
        st.warning("No output to pass forward from the current agent.")

# ---------- Attach Context ----------
with st.expander("📎 Attach Context (PDF/DOCX)", expanded=False):
    uploads = st.file_uploader("Upload files", type=["pdf","docx"], accept_multiple_files=True)
    def _pdf_text(b: bytes) -> str:
        t=""
        if pdfplumber:
            try:
                with pdfplumber.open(io.BytesIO(b)) as pdf:
                    for p in pdf.pages: t += (p.extract_text() or "") + "\\n"
            except: pass
        if not t.strip() and OCR_AVAILABLE:
            try:
                imgs = convert_from_bytes(b, dpi=200)
                t = "\\n".join(pytesseract.image_to_string(i) for i in imgs)
            except: pass
        return t.strip()
    def _docx_text(b: bytes) -> str:
        if not Document: return ""
        try:
            doc = Document(io.BytesIO(b))
            return "\\n".join(p.text for p in doc.paragraphs)
        except: return ""
    if uploads:
        chunks=[]
        for f in uploads[:3]:
            data=f.getvalue()
            txt = _pdf_text(data) if f.name.lower().endswith(".pdf") else _docx_text(data)
            if txt: chunks.append(txt)
        st.session_state["context"] = ("\\n\\n".join(chunks))[:10000]
        st.success("Context attached successfully.")

# ---------- Agent Guide (brighter headings) ----------
with st.expander("🧠 Sentinel Agent Overview — Roles & Prompting Guide", expanded=False):
    st.markdown("""
<div style="line-height:1.55">
<b style="color:#fff;">SENTINEL</b> coordinates autonomous agents for private-market intelligence and decision analysis across energy transition & industrials.
<h4 style="color:#fff;margin:10px 0 4px;">🧭 STRATA — Market Mapping</h4>
<p style="color:#cfd6de;margin:0 0 10px;">“Map emerging U.S. midstream decarbonization subsectors.”</p>
<h4 style="color:#fff;margin:10px 0 4px;">🦅 DEALHAWK — Deal Sourcing</h4>
<p style="color:#cfd6de;margin:0 0 10px;">“Find five late-stage private grid-modernization firms in Texas.”</p>
<h4 style="color:#fff;margin:10px 0 4px;">🧮 NEO — Financial Modeling</h4>
<p style="color:#cfd6de;margin:0 0 10px;">“Translate Strata’s findings into a base-case P&L for 2025–2030.”</p>
<h4 style="color:#fff;margin:10px 0 4px;">⚖️ PRO FORMA NON GRATA (PFNG)</h4>
<p style="color:#cfd6de;margin:0 0 10px;">“Run PFNG on Neo’s summary; assign RIS and counterfactuals.”</p>
<h4 style="color:#fff;margin:10px 0 4px;">🔐 CIPHER — IC Assembly</h4>
<p style="color:#cfd6de;margin:0 0 10px;">“/profile ArcLight Energy Systems Ltd.”</p>
</div>
""", unsafe_allow_html=True)

# ---------- Footer tag ----------
st.markdown("<div class='footer-tag'>🔒 INTERNAL USE — <b>LONG BOW INTELLIGENCE DIRECTORATE</b></div>", unsafe_allow_html=True)

# ---------- Autofocus + autoscroll ----------
st.markdown("""
<script>
setTimeout(()=>{const ta=window.parent.document.querySelector('textarea'); if(ta){ta.focus();}},300);
const el = window.parent.document.querySelector('#chatwrap');
if(el){el.scrollTo({top:el.scrollHeight, behavior:'smooth'});}
</script>
""", unsafe_allow_html=True)

# ---------- Close content wrapper ----------
st.markdown("</div>", unsafe_allow_html=True)

