# PipelineRecall

**An AI agent that remembers why your data pipelines break — and runs smarter every time it diagnoses one.**

PipelineRecall is an incident-triage agent for data engineering teams. It uses [Hindsight](https://hindsight.vectorize.io/) for persistent agent memory and [cascadeflow](https://docs.cascadeflow.ai/) for cost-aware model routing, so it doesn't just answer questions about pipeline failures — it remembers them, recalls similar past incidents instantly, and only spends money on an expensive model when the problem actually warrants it.

## The Problem

When a data pipeline breaks, engineers often re-diagnose the same recurring failure from scratch — digging through logs, Slack history, or asking a senior engineer "haven't we seen this before?" That institutional knowledge usually lives in people's heads, not in any tool. On top of that, every AI-assisted triage call typically hits the same expensive model regardless of how simple or routine the failure actually is.

## What PipelineRecall Does

1. **Retains** every incident it triages — error, root cause, and fix — as a persistent memory.
2. **Recalls** similar past incidents the moment a new failure comes in, instead of starting from zero.
3. **Routes** the diagnosis through cascadeflow: known/simple issues are handled by a fast, cheap model; novel or ambiguous ones are escalated to a stronger model — automatically, based on response quality.
4. **Reflects**, generalizing fixes across pipelines (e.g. a deduplication fix discovered for one table gets reused when the same pattern shows up in a different table).
5. **Logs a full audit trail** of every decision: which model was used, why, the cost, and the latency.

## Demo: Known vs Novel Incident

| | Known/recurring incident | Novel incident |
|---|---|---|
| Memory matches | Multiple relevant past incidents found | Zero relevant matches found |
| Agent behavior | Confident, specific diagnosis citing past fixes | Explicitly states "novel issue," gives a first-pass diagnosis |
| Model routing | Usually handled by the cheap model | Often escalates to the stronger model |

Run `python src/demo.py` to see this comparison live.

The agent also **learns during the session itself** — diagnose a brand-new incident, then ask about a similar one seconds later, and watch it recall what it just learned (try this in `src/cli.py`).

## Tech Stack

- **Hindsight** — persistent agent memory (retain / recall / reflect), via Hindsight Cloud
- **cascadeflow** — runtime intelligence: model routing, cost tracking, audit trail
- **Groq** — fast, free-tier LLM inference (`llama-3.1-8b-instant` and `llama-3.3-70b-versatile`)
- **Python** — `hindsight-client`, `cascadeflow`, `python-dotenv`

## Project Structure

```
pipelinerecall/
├── data/
│   └── incidents.json        # 30 synthetic pipeline incidents (failures + successes)
├── src/
│   ├── load_incidents.py     # Loads synthetic incidents into Hindsight memory
│   ├── test_recall.py        # Simple script to test memory recall
│   ├── triage_agent.py       # Core agent: recall + cascadeflow routing + diagnosis
│   ├── demo.py                # Known vs novel incident comparison demo
│   └── cli.py                 # Interactive CLI — type any incident, get live triage
├── .env.example                # Template for required API keys
└── README.md
```

## Setup

1. **Clone and install dependencies:**
   ```
   pip install hindsight-client "cascadeflow[groq]" python-dotenv
   ```

2. **Set up your `.env` file** (copy `.env.example` and fill in your keys):
   ```
   HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
   HINDSIGHT_API_KEY=your_hindsight_api_key
   HINDSIGHT_BANK_ID=pipelinerecall
   GROQ_API_KEY=your_groq_api_key
   ```
   - Get a Hindsight Cloud key at [ui.hindsight.vectorize.io](https://ui.hindsight.vectorize.io)
   - Get a free Groq key at [console.groq.com](https://console.groq.com)

3. **Load the synthetic incident history into memory:**
   ```
   python src/load_incidents.py
   ```

4. **Run the comparison demo:**
   ```
   python src/demo.py
   ```

5. **Or try it interactively:**
   ```
   python src/cli.py
   ```

## Synthetic Data Note

`data/incidents.json` contains 30 realistic but fully synthetic pipeline incidents, generated to simulate a data team's incident history. No real company data is used. Several incidents are deliberately recurring (e.g. the same schema-drift issue appearing 3 times) to demonstrate memory recall and pattern reflection clearly.

## Real-World Impact

Any team running data pipelines deals with this problem — recurring failures, tribal knowledge that disappears when an engineer leaves, and AI tooling that doesn't get cheaper or smarter as it sees more of your system. PipelineRecall is a small step toward an agent that becomes more valuable to a team the longer it runs alongside them.
