# AI QA Agent — Project Instructions

## Architecture

- `main.py` — FastAPI entry point, serves web UI at `/`, runs agent at `POST /api/run-agent`
- `agent/core_agent.py` — Orchestrates OBSERVE → SIGNUP → EXECUTE cycle
- `agent/observer.py` — Loads page, extracts fields, detects language/form type via LLM
- `agent/signup_phase.py` — Auto-creates a test account before running test cases
- `agent/planner.py` — Generates test cases via LLM (login/signup/reset)
- `agent/executor.py` — Executes each test case with Playwright, verifies via LLM
- `agent/reporter.py` — Saves JSON report to `output/report_*.json`, creates Trello cards on failure
- `tools/llm.py` — All Groq LLM calls; model is `llama-3.1-8b-instant`
- `tools/browser.py` — Playwright wrapper; supports `chromium`, `firefox`, `brave`
- `tools/trello.py` — Currently a mock (no real API integration)
- `frontend/` — Web UI served from `frontend/static/`

## Key Commands

```bash
# Install
python -m venv .venv && .venv/bin/pip install -r requirements.txt
playwright install chromium

# Run server (http://localhost:8000)
python main.py

# Run test directly (CLI)
python run_test.py

# Start via shell script
bash start_server.sh
```

## Required Setup

- `.env` at root must contain `GROQ_API_KEY`. Never commit it.
- `playwright install chromium` must be run after `pip install -r requirements.txt`
- `output/` directory is auto-created and ignored by git

## Important Quirks

- Windows: `main.py` sets `asyncio.WindowsProactorEventLoopPolicy()` at import time
- Signup phase auto-creates test accounts (up to 3 retries) before running test cases
- Credentials injected into test cases via `{{email}}` / `{{password}}` placeholders in `planner.py:_inject_credentials`
- Verification uses LLM to compare expected vs actual page state; fallback uses keyword detection
- `executor.py:reset_session()` re-creates browser context between each test case (session isolation)
- `browser.py` silently ignores failures in cookie dismissal and submit button clicks
- Trello integration (`reporter.py`) is mocked — real API not implemented
- The `playwright_stealth` import is optional; failures are silently ignored