# sentinal_orchestrator.py — Sentinel Smart Orchestrator v2.0
# ------------------------------------------------------------
# Upgraded for richer, ChatGPT-level responses.
# Features:
#   - Per-agent system personas
#   - Rolling memory (last 3–4 turns)
#   - Tuned sampling parameters
#   - Structured JSON handoff (summary, insights, next_steps)
#   - Safe fallback defaults for missing env vars

import os, sys, json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# ---------- Setup ----------
load_dotenv()
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # default to full reasoning model
API_KEY = os.getenv("OPENAI_API_KEY", "")
if not API_KEY:
    print("⚠️  OPENAI_API_KEY not found — API calls may fail.\n")

# ---------- Agent Registry ----------
AGENTS = {
    "strata": {
        "role": "Market Intelligence Analyst",
        "mission": "Map energy transition sectors, identify emerging sub-themes, and summarize industry structure.",
        "tone": "Strategic and data-driven, outputs in Markdown with clear subsectors and next-step guidance."
    },
    "dealhawk": {
        "role": "Deal Sourcing Specialist",
        "mission": "Identify private, profitable companies aligned with Longbow Capital’s investment theses.",
        "tone": "Pragmatic and commercially focused; returns concise company lists with URLs and rationale."
    },
    "neo": {
        "role": "Financial Modeler",
        "mission": "Convert qualitative insight into scenario-based pro forma models and normalized economics.",
        "tone": "Quantitative, assumption-driven; uses short tables or bullet math where relevant."
    },
    "proforma": {
        "role": "Critical Review Analyst (PFNG)",
        "mission": "Stress-test assumptions and identify fragility, bias, and risk intensity scores (RIS).",
        "tone": "Adversarial yet objective; uses inversion logic and assigns RIS (1-5) with reasoning."
    },
    "cipher": {
        "role": "Governance & IC Compiler",
        "mission": "Assemble investment committee packets and ensure thesis, risk, and governance coherence.",
        "tone": "Formal, synthesizing, and compliance-aware; outputs Markdown-ready IC sections."
    }
}

# ---------- Simple Memory Buffers ----------
MEMORY = {a: [] for a in AGENTS}
HANDOFF_CONTEXT = ""


# ---------- Core Call ----------
def call_agent(agent: str, query: str) -> dict:
    """Call an agent with context and return structured JSON output."""
    if agent not in AGENTS:
        raise ValueError(f"Unknown agent '{agent}'. Valid agents: {', '.join(AGENTS.keys())}")

    persona = AGENTS[agent]
    print(f"\n🛰️ Routing to agent: {agent.upper()} using model {MODEL}\n")

    # --- Build memory (last 3–4 exchanges) ---
    history = MEMORY[agent][-6:]
    memory_msgs = [{"role": m["role"], "content": m["content"]} for m in history]

    # --- System prompt with persona ---
    system_prompt = (
        f"You are {agent.upper()} — {persona['role']} within Longbow Capital's Sentinel platform.\n"
        f"Mission: {persona['mission']}\n"
        f"Tone: {persona['tone']}\n\n"
        "Respond in detailed analytical prose (Markdown allowed). "
        "End with a JSON block using keys: summary, insights, next_steps."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(memory_msgs)
    messages.append({"role": "user", "content": query})

    # --- API call ---
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            top_p=0.9,
            max_tokens=1500,
            presence_penalty=0.4,
            frequency_penalty=0.2,
        )
        result = response.choices[0].message.content.strip()
    except Exception as e:
        result = f"⚠️ API call failed: {e}"
        print(result)
        return {"summary": result, "insights": "", "next_steps": ""}

    print(result)

    # --- Save memory ---
    MEMORY[agent].append({"role": "user", "content": query})
    MEMORY[agent].append({"role": "assistant", "content": result})

    # --- Parse structured output ---
    try:
        json_start = result.find("{")
        json_part = result[json_start:]
        parsed = json.loads(json_part)
    except Exception:
        parsed = {"summary": result[:800], "insights": "", "next_steps": ""}

    global HANDOFF_CONTEXT
    HANDOFF_CONTEXT = parsed.get("summary", result)

    # --- Return payload ---
    return parsed


# ---------- CLI Interface ----------
def main():
    if len(sys.argv) < 3:
        print("Usage: python sentinal_orchestrator.py [agent] [query]")
        sys.exit(1)

    agent = sys.argv[1].lower()
    query = " ".join(sys.argv[2:])

    try:
        result = call_agent(agent, query)
        print("\n✅ Structured Response:\n")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n⚠️ Error: {e}")


if __name__ == "__main__":
    main()
