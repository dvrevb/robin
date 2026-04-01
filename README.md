# 🐦 Robin

> Your intelligent sidekick that takes on tasks, scrapes the web, and doesn't stop until the job is done right.

---

## What is Robin?

Robin is an agentic task runner with a built-in evaluator loop. You give it a task and define what success looks like — Robin goes to work, scrapes the web if needed, and checks its own output against your criteria. If it doesn't pass, it tries again. When it does, it delivers the result to you.

No hand-holding. No half-finished answers. Just results that meet the bar.

---

## How It Works

```
You → Task + Success Criteria
         ↓
      🤖 Agent
    (scrapes web, reasons, acts)
         ↓
      ⚖️  Evaluator
    (checks against your criteria)
         ↓
   Pass? → ✅ Delivered to you
   Fail? → 🔁 Back to Agent
```

1. **You define the task** — what needs to be done and what "done" looks like
2. **The Agent gets to work** — it reasons, searches the web, and produces an output
3. **The Evaluator checks it** — compares the output against your success criteria
4. **Loop or deliver** — if it passes, you get the result; if not, the agent tries again

---

## Features

- 🌐 **Web scraping** — Robin can search and extract information from the web autonomously
- 🔁 **Self-correcting loop** — the evaluator sends failed attempts back to the agent with feedback
- ✅ **Criteria-driven** — you define success; Robin works until it's achieved
- 🧠 **Agentic reasoning** — the agent breaks down tasks and adapts its approach across iterations
- 📬 **Clean delivery** — once the output passes evaluation, it's returned to you directly

---

## Quick Start

```bash
# Install
pip install robin-agent

# Run a task
robin run \
  --task "Find the top 5 open-source LLM projects on GitHub by stars this month" \
  --criteria "Must include project name, star count, and a one-line description for each"
```

---

## Usage

### CLI

```bash
robin run --task "<your task>" --criteria "<your success criteria>"
```

### Python

```python
from robin import Robin

result = Robin().run(
    task="Summarize the latest AI research papers published this week",
    criteria="Must cover at least 3 papers, include authors, and highlight key findings"
)

print(result)
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--task` | The task for the agent to complete | required |
| `--criteria` | Success criteria for the evaluator | required |
| `--max-iterations` | Max retry loops before giving up | `5` |
| `--verbose` | Show agent and evaluator reasoning | `false` |
| `--output` | Save result to a file | stdout |

---

## Example

**Task:** Find the current pricing for the top 3 cloud providers for a single GPU instance.

**Criteria:** Must include AWS, GCP, and Azure. Each entry should have instance name, GPU type, and hourly price in USD.

**Robin's process:**
1. Agent scrapes AWS, GCP, and Azure pricing pages
2. Evaluator checks: are all 3 providers present? Is pricing included?
3. First attempt missing Azure → agent retries
4. Second attempt passes → result delivered ✅

---

## Architecture

```
will be updated
```

---
