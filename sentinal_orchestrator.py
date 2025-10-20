# sentinal_orchestrator.py — Sentinel Phase 2.0
# ---------------------------------------------
# Adds per-agent personas, rolling memory, rich completions,
# and GPT-4o fallback for ChatGPT-level output.
#
# Usage:
#   python sentinal_orchestrator.py [agent] [query]

import os, sys, json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# ---------- Setup ----------
load_dotenv()
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ---------- Agent Registry & Personas ----------
AGENTS = {
    "strata": {
        "role": "Market Intelligence Analyst",
        "mission": "Map sectors, subsectors, and themes within energy transition and industrials; identify where to hunt for opportunity.",
    },
    "dealhawk": {
        "role": "Deal Sourcing Specialist",
        "mission": "Find and profile private, profitable North American companies aligned with Longbow’s investment filters.",
