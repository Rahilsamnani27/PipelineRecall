"""
load_incidents.py
Loads synthetic pipeline incident data into Hindsight memory (retain step).
Run this once to populate your memory bank.
"""

import json
import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "pipelinerecall")

client = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY,
)


def build_content(incident: dict) -> str:
    """Turn one incident record into a natural-language memory string."""
    if incident["status"] == "failure":
        return (
            f"Pipeline '{incident['pipeline']}' FAILED on {incident['timestamp']}. "
            f"Error: {incident['error']} "
            f"Root cause: {incident['root_cause']} "
            f"Fix applied: {incident['fix']}"
        )
    else:
        return (
            f"Pipeline '{incident['pipeline']}' SUCCEEDED on {incident['timestamp']}. "
            f"Details: {incident['details']}"
        )


def main():
    with open("data/incidents.json", "r") as f:
        incidents = json.load(f)

    print(f"Loading {len(incidents)} incidents into Hindsight bank '{BANK_ID}'...")

    items = []
    for incident in incidents:
        items.append({
            "content": build_content(incident),
            "context": f"pipeline:{incident['pipeline']} status:{incident['status']}",
            "document_id": incident["id"],
        })

    client.retain_batch(
        bank_id=BANK_ID,
        items=items,
        retain_async=False,
    )

    print("Done. All incidents retained into memory.")


if __name__ == "__main__":
    main()