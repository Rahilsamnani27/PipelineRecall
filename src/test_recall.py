"""
test_recall.py
Simulates a NEW incident coming in and asks Hindsight to recall similar past ones.
This proves the memory actually works.
"""

import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY"),
)

BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "pipelinerecall")

# Simulate a NEW incident - similar to the daily_orders_etl schema issue
new_incident_query = (
    "Pipeline 'daily_orders_etl' is failing with error: "
    "Column 'customer_id' not found in source table 'orders_raw'."
)

print(f"New incident: {new_incident_query}\n")
print("Recalling similar past incidents from memory...\n")

results = client.recall(
    bank_id=BANK_ID,
    query=new_incident_query,
    max_tokens=1024,
)

# Only show top 5 most relevant
for i, r in enumerate(results.results[:5], 1):
    print(f"{i}. {r.text}\n")