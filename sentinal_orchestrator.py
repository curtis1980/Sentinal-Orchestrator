import os
from openai import OpenAI
from dotenv import load_dotenv
import sys

# ✅ Load environment variables from .env file
load_dotenv()

# ✅ Set up OpenAI client (works with the new SDK, e.g., openai>=1.0)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ✅ Define your agents and their basic purposes
AGENTS = {
    "strata": "Research and intelligence agent for energy and decarbonization ecosystems.",
    "dealhawk": "Deal sourcing agent focused on identifying late-stage, profitable private companies in energy transition.",
    "neo": "Analytical agent that creates financial models, pro formas, and scenario simulations.",
    "cipher": "Security and control agent coordinating communication between other agents and maintaining data integrity.",
    "proforma": "Automates and validates private equity financial assumptions and model inputs."
}

def call_agent(agent, query):
    """Call an AI agent with a query."""
    print(f"\n🤖 Routing to agent: {agent.upper()}...\n")

    # ✅ Use the new chat completions API
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"You are {agent}. {AGENTS.ge



def main():
    """Main command-line interface"""
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
        print("\n✅ Response:\n")
        print(result)
    except Exception as e:
        print(f"\n⚠️ Error while calling {agent}: {e}")


if __name__ == "__main__":
    main()





