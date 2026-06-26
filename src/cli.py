"""
cli.py
Interactive CLI for PipelineRecall.
Type in a pipeline incident description and watch the agent:
1. Recall similar past incidents from Hindsight memory
2. Filter for genuine relevance
3. Route through cascadeflow (cheap model first, escalate if needed)
4. Show a full diagnosis + audit trail

Type 'quit' or 'exit' to stop.
"""

import os
import re
import asyncio
from dotenv import load_dotenv
from hindsight_client import Hindsight
from cascadeflow import CascadeAgent, ModelConfig

load_dotenv()

hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY"),
)
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "pipelinerecall")

agent = CascadeAgent(models=[
    ModelConfig(name="llama-3.1-8b-instant", provider="groq", cost=0.0, speed_ms=200),
    ModelConfig(name="llama-3.3-70b-versatile", provider="groq", cost=0.0, speed_ms=600),
])


def is_relevant(new_incident: str, memory_text: str) -> bool:
    pipeline_match = re.search(r"'([a-z_]+)'", new_incident)
    if pipeline_match:
        pipeline_name = pipeline_match.group(1)
        if pipeline_name in memory_text:
            return True

    incident_words = set(w.lower() for w in re.findall(r"[a-zA-Z]{5,}", new_incident))
    memory_words = set(w.lower() for w in re.findall(r"[a-zA-Z]{5,}", memory_text))
    overlap = incident_words & memory_words
    return len(overlap) >= 3


async def triage(new_incident: str):
    print("\nSearching memory...")
    recall = await hindsight.arecall(bank_id=BANK_ID, query=new_incident, max_tokens=1024)
    all_results = [r.text for r in recall.results[:5]]
    relevant = [r for r in all_results if is_relevant(new_incident, r)]

    print(f"Memory matches found: {len(all_results)} | Relevant: {len(relevant)}")
    for i, p in enumerate(relevant, 1):
        print(f"  {i}. {p[:120]}...")

    if relevant:
        memory_context = "\n".join(relevant)
        prompt = (
            f"You are a data pipeline incident triage assistant.\n\n"
            f"New incident:\n{new_incident}\n\n"
            f"Relevant past incidents from memory:\n{memory_context}\n\n"
            f"Based on the memory above, give a short root-cause diagnosis and "
            f"a recommended fix in 3-4 sentences."
        )
    else:
        print("  (no genuinely relevant past incidents found)")
        prompt = (
            f"You are a data pipeline incident triage assistant.\n\n"
            f"New incident:\n{new_incident}\n\n"
            f"There is NO relevant past incident in memory for this case. "
            f"Clearly state that this is a novel issue never seen before, "
            f"then give your best general first-pass diagnosis in 2-3 sentences."
        )

    print("Diagnosing...")
    result = await agent.run(prompt, max_tokens=200, temperature=0.3)

    print(f"\n--- DIAGNOSIS ---\n{result.content}\n")
    print("--- AUDIT TRAIL ---")
    print(f"Model used:     {result.model_used}")
    print(f"Cost:           ${result.total_cost:.6f}")
    print(f"Latency:        {result.latency_ms:.0f}ms")
    status = "cheap model handled it" if result.draft_accepted else "ESCALATED to strong model"
    print(f"Draft accepted: {result.draft_accepted}  ({status})")

    # Retain this new incident + outcome back into memory so the agent keeps learning
    await hindsight.aretain(
        bank_id=BANK_ID,
        content=f"New incident handled: {new_incident} Diagnosis given: {result.content}",
        context="live_demo_session",
    )
    print("\n(This incident has been saved to memory for future recall.)")


async def main():
    print("=" * 70)
    print("PipelineRecall — Interactive Incident Triage")
    print("=" * 70)
    print("Type a pipeline incident description (or 'quit' to exit).\n")
    print("Example:")
    print("  Pipeline 'daily_orders_etl' is failing with error: Column")
    print("  'customer_id' not found in source table 'orders_raw'.\n")

    while True:
        user_input = input(">> Incident: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        if not user_input:
            continue
        await triage(user_input)
        print("\n" + "-" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())