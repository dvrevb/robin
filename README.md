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
2. **The Agent gets to work** — it reasons, searches the web, writes files, runs code, and produces an output
3. **The Evaluator checks it** — compares the output against your success criteria
4. **Loop or deliver** — if it passes, you get the result; if not, the agent tries again with feedback

---

## Features

- 🌐 **Web browsing** — Robin navigates and scrapes pages autonomously using a real browser (Playwright)
- 🔍 **Web search** — searches the web for current, real-time information via Serper
- 🐍 **Code execution** — runs Python code on the fly with a built-in REPL
- 📁 **File management** — reads and writes files to a sandboxed directory
- 📬 **Push notifications** — alerts you when a task is done via Pushover
- 🔁 **Self-correcting loop** — the evaluator sends failed attempts back to the agent with feedback
- ✅ **Criteria-driven** — you define success; Robin works until it's achieved
- 🧠 **Agentic reasoning** — the agent breaks down tasks and adapts its approach across iterations

---

## Quick Start

**1. Clone and install**
```bash
git clone https://github.com/yourname/robin
cd robin
```

**2. Install uv (if not already)**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**3. Install dependencies**
```bash
uv sync
uv run playwright install chromium
```

**4. Set up your `.env`**
```env
OPENAI_API_KEY=your_key
PUSHOVER_TOKEN=your_token
PUSHOVER_USER=your_user
SERPER_API_KEY=your_key
```

**5. Run**
```bash
uv run app.py
```

---

## Usage

Open the Gradio UI in your browser. Enter your task and define your success criteria, then hit **Go!**

- **Task** — what you want Robin to do
- **Success Criteria** — what a good answer looks like; Robin won't stop until this is met
- **Reset** — clears the session and starts fresh with a new agent

---

## Example

**Task:** Find the current pricing for the top 3 cloud providers for a single GPU instance.

**Success Criteria:** Must include AWS, GCP, and Azure. Each entry should have instance name, GPU type, and hourly price in USD.

**Robin's process:**
1. Agent browses AWS, GCP, and Azure pricing pages
2. Evaluator checks: are all 3 providers present? Is pricing included?
3. First attempt missing Azure → agent retries with feedback
4. Second attempt passes → result delivered ✅

---

## Architecture

```
app.py              → Gradio UI
robin.py         → LangGraph graph, worker + evaluator nodes
robin_tools.py   → Tool definitions (browser, search, REPL, files, push)
sandbox/            → File output directory for agent-written files
```

---

## Stack

| Layer | Technology |
|-------|------------|
| UI | Gradio |
| Orchestration | LangGraph |
| LLM | GPT-4o-mini (OpenAI) |
| Browser | Playwright (Chromium) |
| Search | Google Serper |
| Package manager | uv |

## Langraph Steps
# Step 1: Define the State object
# Step 2: Start the Graph Builder with this State class
# Step 3: Create a Node
# Step 4: Create Edges
# Step 5: Compile the Graph