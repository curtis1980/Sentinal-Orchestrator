# sentinal_orchestrator.py — Sentinel Phase 2.0 (Stable)
# ------------------------------------------------------
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
MODEL = os.getenv("OPENAI_MODEL") or "gpt-4o"
API_KEY = os.getenv("OPENAI_API_KEY", "")
if not API_KEY:
    print("⚠️  OPENAI_API_KEY not found — API calls may fail.\n")

# ---------- Agent Registry & Personas ----------
AGENTS = {
    "strata": {
        "role": "Market Intelligence Analyst",
        "mission": "Map sectors, subsectors, and themes within energy transition and industrials; identify where to hunt for opportunity."
    },
    "dealhawk": {
        "role": "Deal Sourcing Specialist",
        "mission": "Find and profile private, profitable North American companies aligned with Longbow’s investment filters."
    },
    "neo": {
        "role": "Financial Modeler",
        "mission": "Translate qualitative insight into financial scenarios and pro forma models; identify value drivers and sensitivities."
    },
    "proforma": {
        "role": "Critical Review Analyst (PFNG)",
        "mission": "Rebuild the thesis from first principles; stress-test assumptions; assign Risk Intensity Scores (1–5) and list counterfactuals."
    },
    "cipher": {
        "role": "Governance & IC Compiler",
        "mission": "Assemble and validate the final Investment Committee packet; ensure logic, risk, and compliance coherence."
    }
}

# ---------- In-memory storage ----------
MEMORY = {a: [] for a in AGENTS}
HANDOFF_CONTEXT = ""

# ---------- Core Call ----------
def call_agent(agent: str, query: str) -> dict:
    """Call an agent with context and return structured JSON output."""
    if agent not in AGENTS:
        raise ValueError(f"Unknown agent '{agent}'. Valid agents: {', '.join(AGENTS.keys())}")

    persona = AGENTS[agent]
    print(f"\n🛰️ Routing to agent: {agent.upper()} using model {MODEL}\n")

    # Rolling memory (last 3–4 exchanges)
    history = MEMORY[agent][-4:]
    memory_msgs = [{"role": m["role"], "content": m["content"]} for m in history]

    # Persona-based system prompt
    system_prompt = (
        f"You are {agent.upper()}, a {persona['role']} within Longbow Capital’s Sentinel platform. "
        f"Mission: {persona['mission']} "
        "Respond in detailed analytical prose (Markdown allowed). "
        "Conclude with a JSON block containing keys: summary, insights, next_steps."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(memory_msgs)
    messages.append({"role": "user", "content": query})

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

    # Store interaction in memory
    MEMORY[agent].append({"role": "user", "content": query})
    MEMORY[agent].append({"role": "assistant", "content": result})

    # Try to parse JSON
    try:
        json_start = result.find("{")
        json_part = result[json_start:]
        parsed = json.loads(json_part)
    except Exception:
        parsed = {"summary": result[:800], "insights": "", "next_steps": ""}

    global HANDOFF_CONTEXT
    HANDOFF_CONTEXT = parsed.get("summary", result)
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
