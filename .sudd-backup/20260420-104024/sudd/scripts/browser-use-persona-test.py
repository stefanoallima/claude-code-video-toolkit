#!/usr/bin/env python
"""
SUDD Browser-Use Persona Test — AI-driven browser navigation as a simulated persona.
Complements Playwright-based technical validation with natural-language persona simulation.

Usage:
  python sudd/scripts/browser-use-persona-test.py \
    --persona path/to/persona.md \
    --url http://localhost:3000 \
    --objectives "find signup form, fill with realistic data, submit" \
    --output path/to/browser-use-report.json \
    [--config path/to/sudd.yaml] \
    [--scope task|gate] \
    [--task-id T01] \
    [--screenshots-dir path/to/screenshots/] \
    [--record-video path/to/recordings/]

Requires: pip install browser-use langchain-openai langchain-anthropic
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Attempt imports — fail gracefully with clear message
try:
    from browser_use import Agent, Browser
except ImportError:
    print(json.dumps({
        "error": "browser-use not installed. Run: pip install browser-use",
        "verdict": "SKIP",
        "reason": "missing_dependency"
    }))
    sys.exit(1)


def load_llm(config: dict):
    """Load the LLM based on sudd.yaml browser_use config."""
    provider = config.get("provider", "openrouter")
    model = config.get("model", "google/gemini-2.5-flash-preview")
    api_key_env = config.get("api_key_env", "OPENROUTER_API_KEY")
    endpoint = config.get("endpoint", "")

    api_key = os.environ.get(api_key_env, "")
    if not api_key:
        print(json.dumps({
            "error": f"Missing API key: set {api_key_env} environment variable",
            "verdict": "SKIP",
            "reason": "missing_api_key"
        }))
        sys.exit(1)

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI
        base_url = endpoint or "https://openrouter.ai/api/v1"
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
    elif provider == "zai" or provider == "zai-coding-plan":
        from langchain_openai import ChatOpenAI
        base_url = endpoint or "https://api.z.ai/api/coding/paas/v4"
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key)
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key)
    else:
        # Default: treat as OpenAI-compatible with custom endpoint
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=endpoint,
        )


def load_config(config_path: str) -> dict:
    """Load browser_use config from sudd.yaml."""
    try:
        import yaml
    except ImportError:
        # Fallback: parse the browser_use section manually
        return {}

    path = Path(config_path)
    if not path.exists():
        return {}

    with open(path) as f:
        data = yaml.safe_load(f)

    return data.get("browser_use", {})


def read_persona(persona_path: str) -> str:
    """Read persona file and extract identity + objectives."""
    path = Path(persona_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def build_task_prompt(persona_text: str, url: str, objectives: str, scope: str) -> str:
    """Build the natural-language task for browser-use agent."""

    scope_instructions = ""
    if scope == "task":
        scope_instructions = """
SCOPE: You are testing a SPECIFIC TASK's UI changes. Focus narrowly on the pages/routes
affected by this task. Do not explore the entire application."""
    else:
        scope_instructions = """
SCOPE: You are doing a FULL APPLICATION walkthrough as the persona. Explore broadly.
Navigate all main routes. Try to accomplish ALL persona objectives end-to-end."""

    return f"""You are a simulated user persona testing a web application.

## Your Identity
{persona_text}

## Your Mission
Navigate to {url} and attempt to accomplish these objectives AS THIS PERSONA:
{objectives}

{scope_instructions}

## How to Test
1. FIRST IMPRESSION: Navigate to the URL. What do you see? Is it clear what this app does?
2. DISCOVERABILITY: For each objective, try to find the relevant feature WITHOUT any instructions.
   - Can you find the right page/section?
   - Is the navigation intuitive?
   - Are buttons and links clearly labeled?
3. FORM FILLING: When you encounter forms:
   - Fill them with REALISTIC data matching the persona (not "test123" — use real-looking names, emails, etc.)
   - Try submitting with missing required fields — does the app show helpful errors?
   - Try submitting with invalid data — are error messages clear?
   - Submit with valid data — does the app confirm success?
4. INTERACTION: Click buttons, follow links, use dropdowns, interact with all UI elements naturally.
5. FLOW COMPLETION: Can you complete each objective end-to-end?
6. DEAD ENDS: Note any page where you get stuck with no obvious next step.
7. ERROR RECOVERY: If something goes wrong, can you figure out how to fix it?

## What to Report
For each objective, report:
- Could you find the feature? (YES/NO + how long it took)
- Could you complete the task? (YES/NO + what happened)
- Were forms easy to fill? (YES/NO + issues)
- Any confusion points or friction?
- Overall impression as this persona

Be HONEST. If the UI is confusing, say so. If you can't figure something out, report it as a failure.
Do NOT make excuses for bad UX."""


async def run_test(args, config):
    """Run the browser-use persona test."""
    start_time = time.time()

    # Load LLM
    llm = load_llm(config)

    # Read persona
    persona_text = read_persona(args.persona)
    if not persona_text:
        return {
            "error": f"Persona file not found: {args.persona}",
            "verdict": "SKIP",
            "reason": "missing_persona"
        }

    # Build task
    task = build_task_prompt(persona_text, args.url, args.objectives, args.scope)

    # Configure browser
    browser_kwargs = {}
    if args.record_video:
        browser_kwargs["record_video_dir"] = Path(args.record_video)

    browser = Browser(**browser_kwargs)

    # Run agent
    try:
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
        )
        result = await agent.run()
        elapsed = time.time() - start_time

        # Parse agent result
        report = {
            "verdict": "DONE",
            "elapsed_seconds": round(elapsed, 1),
            "persona": args.persona,
            "url": args.url,
            "scope": args.scope,
            "objectives": args.objectives,
            "agent_result": str(result),
            "task_id": args.task_id or "",
        }

        return report

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "verdict": "ERROR",
            "error": str(e),
            "elapsed_seconds": round(elapsed, 1),
            "persona": args.persona,
            "url": args.url,
        }
    finally:
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description="SUDD Browser-Use Persona Test")
    parser.add_argument("--persona", required=True, help="Path to persona/micro-persona .md file")
    parser.add_argument("--url", required=True, help="URL of running application")
    parser.add_argument("--objectives", required=True, help="Comma-separated objectives to test")
    parser.add_argument("--output", default="", help="Path to write JSON report")
    parser.add_argument("--config", default="sudd/sudd.yaml", help="Path to sudd.yaml")
    parser.add_argument("--scope", choices=["task", "gate"], default="task", help="Test scope")
    parser.add_argument("--task-id", default="", help="Task ID (for per-task tests)")
    parser.add_argument("--screenshots-dir", default="", help="Directory for screenshots")
    parser.add_argument("--record-video", default="", help="Directory for video recordings")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Run test
    report = asyncio.run(run_test(args, config))

    # Output
    report_json = json.dumps(report, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report_json, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report_json)


if __name__ == "__main__":
    main()
