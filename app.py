# ---------- Sentinel v3.3 — Stable Console Build ----------
# Features: fade intro, safe rerun, centered agent select, improved agent runner

import io, os, sys, json, time, subprocess, streamlit as st
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Sentinel", layout="wide")

# ---------- Add scroll-fade CSS ----------
st.markdown("""
<style>
.chat-fade {
  position:relative;
}
.chat-fade::after {
  content:"";
  position:absolute;
  bottom:0;
  left:0;
  width:100%;
  height:20px;
  pointer-events:none;
  background:linear-gradient(to top, #0d0f12 0%, transparent 100%);
}
</style>
""", unsafe_allow_html=True)


# ---------- SESSION DEFAULTS ----------
defaults = {
    "threads": {},
    "context": "",
    "last_agent": "strata",
    "next_agent": "dealhawk",
    "is_running": False,
    "active_agent": None,
    "entry_done": False,
    "prompt": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Reset hung state if prior run stuck mid-call
if st.session_state.get("is_running", False):
    st.session_state["is_running"] = False

# ---------- AGENT DEFINITIONS ----------
AGENTS = {
    "strata": "Research & intelligence for energy/decarbonization.",
    "dealhawk": "Deal sourcing for profitable private companies.",
    "neo": "Financial modeling and scenario analysis.",
    "proforma": "Critical review and risk calibration (PFNG).",
    "cipher": "IC assembly and governance validation."
}
AGENT_SEQUENCE = list(AGENTS.keys())


def _recompute_next():
    cur = st.session_state.get("last_agent", "strata")
    try:
        i = AGENT_SEQUENCE.index(cur)
        st.session_state["next_agent"] = (
            AGENT_SEQUENCE[i + 1] if i + 1 < len(AGENT_SEQUENCE) else None
        )
    except ValueError:
        st.session_state["next_agent"] = None


# ---------- SECURE ENTRY (fade intro) ----------
if not st.session_state.get("entry_done", False):
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(
            """
            <style>
            @keyframes fadeOut {0%{opacity:1;} 90%{opacity:0;} 100%{opacity:0;display:none;}}
            body {background-color:#0E0F11;}
            </style>
            <div id="boot-seq"
                 style="height:70vh;display:flex;flex-direction:column;
                        justify-content:center;align-items:center;
                        text-align:center;animation:fadeOut 1.6s ease-out 3.2s forwards;">
              <div style="font-size:40px;color:#E63946;letter-spacing:.10em;
                          font-weight:800;margin-bottom:8px;">SENTINEL</div>
              <div style="color:#A8B2BD;font-size:14px;letter-spacing:.06em;">
                  AUTHENTICATING SESSION…
              </div>
              <div style="margin-top:36px;color:#A4B8C9;font-size:13px;
                          text-align:left;line-height:1.6;">
                🛰 INITIALIZING NODES…<br>
                <span style="color:#48FF7F;">✅ STRATA NODE ONLINE</span><br>
                <span style="color:#48FF7F;">✅ DEALHAWK NODE ONLINE</span><br>
                <span style="color:#48FF7F;">✅ NEO NODE ONLINE</span><br>
                <span style="color:#48FF7F;">✅ PFNG NODE ONLINE</span><br>
                <span style="color:#48FF7F;">✅ CIPHER SECURE CHANNEL</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    time.sleep(4.8)  # total animation duration
    st.session_state["entry_done"] = True
    st.rerun()

# ---------- HEADER ----------
st.markdown(
    """
    <div style="text-align:center;margin-top:10px;margin-bottom:8px;">
      <span style="color:#E63946;font-family:'Courier New',monospace;
                  font-weight:700;font-size:46px;letter-spacing:.08em;">
        SENTINEL
      </span>
      <div style="color:#A0A6AD;font-size:14px;letter-spacing:.05em;
                  margin-top:4px;">
        Autonomous Agents for Asymmetric Advantage
      </div>
    </div>
    <hr style="border:0;border-top:1px solid #2C313A;margin:8px 0 14px;">
    """,
    unsafe_allow_html=True,
)

# ---------- AGENT SELECTOR (Option A) ----------
st.markdown(
    """
    <style>
    div[data-testid="stSelectbox"] > div:first-child {
        max-width:340px !important;
        margin:0 auto !important;
        border:1px solid #E63946;
        border-radius:6px;
        box-shadow:0 0 6px #E6394622;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    agent = st.selectbox(
        "Choose agent",
        AGENT_SEQUENCE,
        index=AGENT_SEQUENCE.index(st.session_state["last_agent"]),
    )
st.session_state["last_agent"] = agent
_recompute_next()
st.caption(AGENTS[agent])

# ---------- COMPOSER ----------
def _compose(user_q: str) -> str:
    ctx = st.session_state.get("context", "").strip()
    prior = st.session_state["threads"][agent][-5:]
    mem = "\n".join(f"{m['agent'].upper()}: {m['response'][:400]}" for m in prior)
    base = user_q
    if ctx:
        base = f"Context:\n{ctx}\n\n{base}"
    if mem:
        base = f"Recent Discussion:\n{mem}\n\n{base}"
    return base


# ---------- AGENT RUNNER ----------
def run_agent(agent_key: str, user_q: str):
    if st.session_state.get("is_running"):
        st.toast("⚠️ Sentinel busy — please wait or reset.", icon="🚧")
        return

    if not user_q.strip():
        st.warning("Type a question first.")
        return

    st.session_state["is_running"] = True
    st.session_state["active_agent"] = agent_key
    q = _compose(user_q)
    st.toast(f"🛰 Accessing {agent_key.upper()}...", icon="🔴")

    try:
        res = subprocess.run(
            ["python", "sentinal_orchestrator.py", agent_key, q],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = res.stdout.strip() or res.stderr.strip()
        if not output:
            st.error(f"⚠️ {agent_key.upper()} returned no output.")
    except Exception as e:
        output = f"⚠️ Execution error: {e}"
        st.error(output)

    st.session_state["threads"].setdefault(agent_key, []).append(
        {
            "agent": agent_key,
            "query": user_q,
            "response": output,
            "time": datetime.now().strftime("%H:%M:%S"),
        }
    )

    st.session_state["is_running"] = False
    st.session_state["active_agent"] = None
    st.rerun()


# ---------- CHAT DISPLAY ----------
thread = st.session_state["threads"][agent]
if thread:
    st.markdown("<div style='background:#1E232B;border-radius:10px;"
                "padding:16px 18px;height:60vh;overflow-y:auto;'>",
                unsafe_allow_html=True)
    for msg in thread[-12:]:
        st.markdown(
            f"<div style='border-left:4px solid #E63946;"
            f"padding:8px 10px;margin:6px 0;color:#F8F8F8;'>"
            f"<b>{msg['agent'].upper()}</b><br>"
            f"{msg['response'].replace(chr(10), '<br>')}"
            f"<div style='color:#A0A6AD;font-size:11px;margin-top:3px;'>⏱ {msg['time']}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No messages yet.")


# ---------- PROMPT + BUTTONS ----------
colA, colB, colC = st.columns([5, 2, 2])
with colA:
    st.session_state["prompt"] = st.text_area(
        "Type your prompt:",
        value=st.session_state["prompt"],
        key="prompt_box",
        placeholder=f"Ask {agent.capitalize()}…",
        height=80,
    )
with colB:
    ask_btn = st.button("💬 Ask Agent", use_container_width=True)
with colC:
    nxt = st.session_state.get("next_agent")
    send_btn = st.button(
        f"➡ Send to {nxt.upper()}" if nxt else "No Next",
        use_container_width=True,
        disabled=(nxt is None),
    )

# ---------- ACTION HANDLERS ----------
user_q = (st.session_state["prompt"] or "").strip()
if ask_btn and user_q:
    run_agent(agent, user_q)
elif send_btn and nxt:
    if st.session_state["threads"][agent]:
        last = st.session_state["threads"][agent][-1]["response"]
        run_agent(nxt, last[:1600])
    else:
        st.warning("No output to send.")

# ---------- RESET SESSION ----------
st.markdown("<hr style='border:0;border-top:1px solid #2C313A;margin:10px 0;'>", unsafe_allow_html=True)
if st.button("🔁 Reset Session", use_container_width=True):
    st.session_state.clear()
    st.rerun()
