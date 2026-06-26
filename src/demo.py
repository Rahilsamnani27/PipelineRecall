"""
demo.py
PipelineRecall demo: compares how the agent handles a KNOWN recurring
incident vs a NOVEL never-seen-before incident.

Known incident -> strong memory match -> cheap model handles it confidently
Novel incident -> no relevant memory -> agent says so instead of guessing
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
    """Simple relevance check: does the memory share key terms with the incident?"""
    pipeline_match = re.search(r"'([a-z_]+)'", new_incident)
    if pipeline_match:
        pipeline_name = pipeline_match.group(1)
        if pipeline_name in memory_text:
            return True

    incident_words = set(w.lower() for w in re.findall(r"[a-zA-Z]{5,}", new_incident))
    memory_words = set(w.lower() for w in re.findall(r"[a-zA-Z]{5,}", memory_text))
    overlap = incident_words & memory_words
    return len(overlap) >= 3


async def triage(label: str, new_incident: str):
    print("\n" + "=" * 70)
    print(f"{label}")
    print("=" * 70)
    print(f"Incident: {new_incident}\n")

    recall = await hindsight.arecall(bank_id=BANK_ID, query=new_incident, max_tokens=1024)
    all_results = [r.text for r in recall.results[:5]]

    relevant = [r for r in all_results if is_relevant(new_incident, r)]

    print(f"Memory matches found: {len(all_results)} | Relevant after filtering: {len(relevant)}")
    for i, p in enumerate(relevant, 1):
        print(f"  {i}. {p[:100]}...")

    if relevant:
        memory_context = "\n".join(relevant)
    else:
        memory_context = "NO_RELEVANT_MEMORY"
        print("  (no genuinely relevant past incidents found)")

    if memory_context == "NO_RELEVANT_MEMORY":
        prompt = (
            f"You are a data pipeline incident triage assistant.\n\n"
            f"New incident:\n{new_incident}\n\n"
            f"There is NO relevant past incident in memory for this case. "
            f"Clearly state that this is a novel issue never seen before, "
            f"then give your best general first-pass diagnosis in 2-3 sentences."
        )
    else:
        prompt = (
            f"You are a data pipeline incident triage assistant.\n\n"
            f"New incident:\n{new_incident}\n\n"
            f"Relevant past incidents from memory:\n{memory_context}\n\n"
            f"Based on the memory above, give a short root-cause diagnosis and "
            f"a recommended fix in 3-4 sentences."
        )

    result = await agent.run(prompt, max_tokens=200, temperature=0.3)

    print(f"\nDiagnosis: {result.content}\n")
    print("--- Audit Trail ---")
    print(f"Model used:        {result.model_used}")
    print(f"Cost:              ${result.total_cost:.6f}")
    print(f"Latency:           {result.latency_ms:.0f}ms")
    print(f"Draft accepted:    {result.draft_accepted}  "
          f"({'cheap model handled it' if result.draft_accepted else 'ESCALATED to strong model'})")

    return result


async def main():
    known_incident = (
        "Pipeline 'daily_orders_etl' is failing with error: "
        "Column 'customer_id' not found in source table 'orders_raw'."
    )

    novel_incident = (
        "Pipeline 'realtime_fraud_scoring' is failing with error: "
        "GPU memory allocation failed while loading the fraud detection model into the inference server."
    )

    r1 = await triage("CASE 1: KNOWN / RECURRING INCIDENT", known_incident)
    r2 = await triage("CASE 2: NOVEL / NEVER-SEEN INCIDENT", novel_incident)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Known incident   -> model: {r1.model_used}, cost: ${r1.total_cost:.6f}, escalated: {not r1.draft_accepted}")
    print(f"Novel incident   -> model: {r2.model_used}, cost: ${r2.total_cost:.6f}, escalated: {not r2.draft_accepted}")


if __name__ == "__main__":
    asyncio.run(main())