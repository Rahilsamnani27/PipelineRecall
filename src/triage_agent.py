"""
triage_agent.py
The core PipelineRecall agent loop:
1. Recall similar past incidents from Hindsight (memory)
2. Use cascadeflow to route the diagnosis to a cheap or strong model
   depending on whether this looks like a known recurring pattern
3. Print a full decision/audit trail (model used, cost, reasoning)
"""

import os
import asyncio
from dotenv import load_dotenv
from hindsight_client import Hindsight
from cascadeflow import CascadeAgent, ModelConfig

load_dotenv()

# --- Hindsight setup ---
hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY"),
)
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "pipelinerecall")

# --- cascadeflow setup: cheap/fast model first, strong model as escalation ---
agent = CascadeAgent(models=[
    ModelConfig(name="llama-3.1-8b-instant", provider="groq", cost=0.0, speed_ms=200),
    ModelConfig(name="llama-3.3-70b-versatile", provider="groq", cost=0.0, speed_ms=600),
])


async def triage(new_incident: str):
    print(f"\n New incident: {new_incident}\n")

    # Step 1 — recall similar past incidents
    recall = await hindsight.arecall(bank_id=BANK_ID, query=new_incident, max_tokens=1024)
    past_incidents = [r.text for r in recall.results[:5]]

    print(" Recalled similar past incidents:")
    for i, p in enumerate(past_incidents, 1):
        print(f"  {i}. {p}")

    memory_context = "\n".join(past_incidents) if past_incidents else "No similar past incidents found."

    # Step 2 — build prompt for the LLM, asking it to diagnose using memory
    prompt = (
        f"You are a data pipeline incident triage assistant.\n\n"
        f"New incident:\n{new_incident}\n\n"
        f"Relevant past incidents from memory:\n{memory_context}\n\n"
        f"Based on the memory above, give a short root-cause diagnosis and "
        f"a recommended fix in 3-4 sentences."
    )

    # Step 3 — run through cascadeflow (auto routes cheap -> strong model)
    result = await agent.run(prompt, max_tokens=200, temperature=0.3)

    # Step 4 — audit trail
    print("\n Diagnosis:")
    print(result.content)
    print("\n Audit trail:")
    print(f"  Model used: {result.model_used}")
    print(f"  Cost: ${result.total_cost:.6f}")
    print(f"  Latency: {result.latency_ms:.0f}ms")
    print(f"  Draft accepted (no escalation needed): {result.draft_accepted}")

    return result


if __name__ == "__main__":
    new_incident = (
        "Pipeline 'daily_orders_etl' is failing with error: "
        "Column 'customer_id' not found in source table 'orders_raw'."
    )
    asyncio.run(triage(new_incident))