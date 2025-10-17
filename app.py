# --- Follow-up + Next Agent ---
if st.session_state.last_agent and st.session_state.last_response:
    st.markdown("### 🔁 Last Interaction")
    st.write(f"**Agent:** {st.session_state.last_agent.upper()}")
    st.write(f"**Response:** {st.session_state.last_response}")

    # Suggest next agent if any
    if st.session_state.next_agent:
        st.markdown("---")
        st.markdown(f"**Next Recommended Agent:** `{st.session_state.next_agent.upper()}`")
        follow_up = st.text_input("🔍 Follow-up query (optional):")

        if st.button(f"Continue with {st.session_state.next_agent.upper()}"):
            if follow_up.strip():
                run_agent(st.session_state.next_agent, follow_up)
            else:
                st.warning("Please enter a follow-up query before continuing.")
