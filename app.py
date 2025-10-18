# app.py
import streamlit as st
import subprocess
import time
from datetime import datetime
import io
import csv
from docx import Document

# ----------------------------
# Page + Branding
# ----------------------------
st.set_page_config(page_title="Sentinel", layout="wide")
st.markdown(
    """
    <style>
        .sentinel-header {
            background: linear-gradient(90deg, #0d6efd, #6610f2);
            color: white; padding: 14px 18px; border-radius: 12px; margin-bottom: 10px;
        }
        .chat-container {
            height: 520px; overflow-y: auto; background: #f8f9fa; border: 1px solid #e9ecef;
            border-radius: 10px; padding: 12px;
        }
        .bubble {
            padding: 12px; border-radius: 10px; color: white; margin: 8px 0;
        }
        .legend-pill {
            display: inline-block; padding: 6px 10px; border-radius: 999px; color: #fff; margin-right: 8px; font-size: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="sentinel-header">
        <h2 style="margin:0;">🧠 Sentinel</h2>
        <div>Autonomous Agents for Asymmetric Advantage</div>
        <small>Multi-agent intelligence stack for energy, capital, and strategy.</small>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Agent Data
# ----------------------------
AGENTS = {
    "strata":   {"color": "#4CAF50", "desc": "Research & intelligence for energy/decarbonization ecosystems."},
    "dealhawk": {"color": "#FF9800", "desc": "Deal sourcing for late-stage, profitable ET companies."},
    "neo":      {"color": "#2196F3", "desc": "Analytics & modeling: pro formas, scenarios, sensitivities."},
    "cipher":   {"color": "#9C27B0", "desc": "Security/coordination between agents; integrity & routing."},
    "proforma": {"color": "#795548", "desc": "Automates/validates PE financial assumptions & inputs."},
}
SEQUENCE = list(AGENTS.keys())

# ----------------------------
# Session State (with safe defaults)
# ----------------------------
st.session_state.setdefault("history", [])            # list of dicts: {agent, query, response, time}
st.session_state.setdefault("last_agent", None)
st.session_state.setdefault("last_response", None)
st.session_state.setdefault("next_agent", None)
st.session_state.setdefault("is_running", False)      # prevents repeated runs per click
st.session_state.setdefault("user_query", "")         # bind main query input
st.session_state.setdefault("follow_up", "")          # bind follow-up input

# ----------------------------
# Sidebar: Controls, Legend, Export
# ----------------------------
with st.sidebar:
    st.subheader("⚙️ Controls")
    start_agent = st.selectbox("Start agent", SEQUENCE, index=0)
    st.caption(AGENTS[start_agent]["desc"])
    st.markdown("---")

    # Color legend
    st.subheader("🎨 Legend")
    for a, meta in AGENTS.items():
        st.markdown(
            f"<span class='legend-pill' style='background:{meta['color']}'>{a.upper()}</span>",
            unsafe_allow_html=True
        )
    st.markdown("---")

    # Session metadata
    st.subheader("📊 Session")
    st.write(f"Current agent: **{(st.session_state.last_agent or start_agent).upper()}**")
    st.write(f"Interactions: **{len(st.session_state.history)}**")
    st.write(f"Last updated: **{datetime.now().strftime('%H:%M:%S')}**")

    st.markdown("---")
    st.subheader("💾 Export Session")

    def export_txt():
        buf = io.StringIO()
        for h in st.session_state.history:
            buf.write(f"[{h['time']}] {h['agent'].upper()} | Q: {h['query']}\n{h['response']}\n\n")
        return buf.getvalue().encode("utf-8")

    def export_csv():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["time", "agent", "query", "response"])
        for h in st.session_state.history:
            writer.writerow([h["time"], h["agent"], h["query"], h["response"]])
        return buf.getvalue().encode("utf-8")

    def export_docx():
        doc = Document()
        doc.add_heading("Sentinel Session Export", level=1)
        doc.add_paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        doc.add_paragraph("")
        for h in st.session_state.history:
            doc.add_heading(f"{h['time']} — {h['agent'].upper()}", level=2)
            doc.add_paragraph(f"Query: {h['query']}")
            doc.add_paragraph(h["response"])
            doc.add_paragraph("")
        b = io.BytesIO()
        doc.save(b)
        return b.getvalue()

    colx1, colx2, colx3 = st.columns(3)
    with colx1:
        st.download_button("TXT", data=export_txt(), file_name="sentinel_session.txt", mime="text/plain", use_container_width=True)
    with colx2:
        st.download_button("CSV", data=export_csv(), file_name="sentinel_session.csv", mime="text/csv", use_container_width=True)
    with colx3:
        st.download_button("DOCX", data=export_docx(), file_name="sentinel_session.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)

    st.markdown("---")
    # Full Reset (logic + UI)
    if st.button("🔁 Start New Search", use_container_width=True):
        with st.spinner("🧠 Resetting Sentinel…"):
            time.sleep(0.8)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ Ready for a fresh session")
            time.sleep(0.4)
            st.experimental_rerun()

# ----------------------------
# Helpers
# ----------------------------
def run_agent(agent: str, query: str):
    """Run a specific agent safely (prevents 4x repeats)."""
    if st.session_state.is_running:
        return
    st.session_state.is_running = True
    start = time.time()

    with st.spinner(f"Running {agent.upper()}…"):
        try:
            # call your orchestrator script
            result = subprocess.run(
                ["python", "sentinal_orchestrator.py", agent, query],
                capture_output=True, text=True, check=True
            )
            raw = result.stdout or ""
            # Clean artifacts & accidental repeats
            lines = [ln for ln in raw.splitlines() if ln.strip()]
            output = "\n".join(lines).strip()
            duration = round(time.time() - start, 2)

            # Render bubble
            st.markdown(
                f"<div class='bubble' style='background:{AGENTS[agent]['color']};'>"
                f"<b>{agent.upper()} says:</b><br><br>{output.replace(chr(10), '<br>')}"
                f"<br><small>⏱️ {duration}s</small></div>",
                unsafe_allow_html=True
            )

            # Save history
            st.session_state.history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "agent": agent,
                "query": query,
                "response": output
            })
            st.session_state.last_agent = agent
            st.session_state.last_response = output

            # Suggest next in chain
            idx = SEQUENCE.index(agent)
            st.session_state.next_agent = SEQUENCE[idx + 1] if idx + 1 < len(SEQUENCE) else None

        except subprocess.CalledProcessError as e:
            err = e.stderr or e.stdout or "Unknown error"
            st.markdown(
                f"<div class='bubble' style='background:#dc3545;'>"
                f"<b>{agent.upper()} error:</b><br><br>{err.replace(chr(10), '<br>')}"
                f"</div>",
                unsafe_allow_html=True
            )
        finally:
            st.session_state.is_running = False

# ----------------------------
# Main Body (two columns)
# ----------------------------
left, right = st.columns([7, 5])

with left:
    st.subheader("Compose")
    st.session_state.user_query = st.text_area(
        "Your prompt", value=st.session_state.user_query, placeholder="e.g., Map the industrial decarbonization ecosystem in Canada"
    )

    if st.button("🚀 Run Agent", use_container_width=True):
        if st.session_state.user_query.strip():
            run_agent(start_agent, st.session_state.user_query.strip())
        else:
            st.warning("Please enter a query first.")

    st.markdown("### Conversation")
    chat_box = st.container()
    with chat_box:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        # Only render last 10 interactions for speed
        for h in st.session_state.history[-10:]:
            st.markdown(
                f"<div class='bubble' style='background:{AGENTS[h['agent']]['color']};'>"
                f"<b>{h['agent'].upper()} ({h['time']}):</b><br><br>{h['response'].replace(chr(10), '<br>')}"
                f"</div>", unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.subheader("Follow-up / Next")
    if st.session_state.last_agent and st.session_state.last_response:
        st.write(f"**Last agent:** {st.session_state.last_agent.upper()}")
        st.write(f"**Next recommended:** {(st.session_state.next_agent or '—').upper() if st.session_state.next_agent else '—'}")

        st.session_state.follow_up = st.text_area(
            "Follow-up (optional)",
            value=st.session_state.follow_up,
            placeholder="e.g., Summarize the top 3 investable themes and key players.",
            height=140
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💬 Ask Same Agent", use_container_width=True):
                if st.session_state.follow_up.strip():
                    combined = f"{st.session_state.last_response}\n\nFollow-up: {st.session_state.follow_up.strip()}"
                    run_agent(st.session_state.last_agent, combined)
                else:
                    st.warning("Enter a follow-up first.")
        with c2:
            if st.session_state.next_agent and st.button(f"➡️ Send to {st.session_state.next_agent.upper()}", use_container_width=True):
                # pass context forward
                context = (
                    f"Context from {st.session_state.last_agent.upper()}:\n"
                    f"{st.session_state.last_response}\n\n"
                    f"New instructions: {st.session_state.follow_up.strip() or 'Continue the workflow using this context.'}"
                )
                run_agent(st.session_state.next_agent, context)
    else:
        st.info("Run an agent to enable follow-up and chaining.")
