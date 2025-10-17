# app.py
import streamlit as st
import subprocess
import sys

st.set_page_config(page_title="Sentinal-Orchestrator Demo")
st.title("🛰️ Sentinal-Orchestrator Demo (STRATA)")

st.write("Type a question, then click Run.")
query = st.text_area("Your question:", "Map Canada's energy transition ecosystem")

if st.button("Run STRATA"):
    st.info("Running STRATA… please wait 10–20 seconds.")
    # Call your existing Python file with the user's text
    result = subprocess.run(
        [sys.executable, "sentinal_orchestrator.py", "strata", query],
        capture_output=True, text=True
    )
    st.subheader("Output")
    st.code(result.stdout or "(No output)")
    if result.stderr:
        st.subheader("Errors")
        st.code(result.stderr)
