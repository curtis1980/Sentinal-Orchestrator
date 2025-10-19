# sentinal_orchestrator.py — Sentinel Phase 1.5
# ---------------------------------------------
# Adds per-agent memory, contextual hand-off, and structured JSON output.
# Backward-compatible with:  python sentinal_orchestrator.py [agent] [query]

import os, sys, json
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Setup ----------
load_dotenv()
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ---------- Agent Registry ----------
AGENTS = {
    "strata": "Research and intelligence agent for energy and decarbonization ecosystems.",
    "dealhawk": "Deal sourcing agent focused on identifying late-stage, profitable private companies in energy transition.",
    "neo": "Analytical agent that creates financial models, pro formas, and scenario simulations.",
    "cipher": "Security and control agent coordinating communication between other agents and maintaining data integrity.",
    "proforma": "Automates and validates private equity financial assumptions and model inputs."
}

# ---------- Simple In-Memory Buffers ----------
MEMORY = {a: [] for a in AGENTS}
HANDOFF_CONTEXT = ""  # stores latest summary passed between agents


# ---------- Core Call ----------
def call_agent(agent: str, query: str) -> dict:
    """Call an agent with memory and return structured JSON output."""
    print(f"\n🤖 Routing to agent: {agent.upper()}...\n")

    # build short rolling memory (last 5 turns)
    history = MEMORY[agent][-5:]
    history_text = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history])

    prompt = (
        f"You are {agent}, {AGENTS[agent]}\n\n"
        f"Conversation so far:\n{history_text}\n\n"
        f"New user query:\n{query}\n\n"
        "Respond in concise business prose. "
        "At the end, provide a JSON block with keys: summary, insights, next_steps."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": prompt}],
        temperature=0.3,
    )

    result = response.choices[0].message.content.strip()
    print(result)

    # store message pair in memory
    MEMORY[agent].append({"role": "user", "content": query})
    MEMORY[agent].append({"role": "assistant", "content": result})

    # try to extract structured output for downstream agents
    try:
        json_start = result.find("{")
        json_part = result[json_start:]
        parsed = json.loads(json_part)
    except Exception:
        parsed = {"summary": result[:500], "insights": "", "next_steps": ""}

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

    if agent not in AGENTS:
        print(f"❌ Unknown agent: {agent}")
        print(f"Available agents: {', '.join(AGENTS.keys())}")
        sys.exit(1)

    try:
        result = call_agent(agent, query)
        print("\n✅ Structured Response:\n")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n⚠️ Error while calling {agent}: {e}")


if __name__ == "__main__":
    main()
