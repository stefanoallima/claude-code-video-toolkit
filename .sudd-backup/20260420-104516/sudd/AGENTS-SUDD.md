# SUDD Framework Guide

> **Framework-owned file.** Auto-updated by `sudd update`. Do not edit manually —
> changes will be overwritten. Put repo-specific guidance in `AGENTS.md` instead.

This project uses **SUDD** (Simulated User-Driven Development) for autonomous
AI-driven development. The CLI agent IS the orchestrator. Everything else is
markdown. Code is only "done" when validated from the actual user's perspective.

## Framework Priority

**Default to SUDD for any new change.** If the user says "let's build X" or
"fix Y" or "add Z", use SUDD — not openspec, not superpowers, not feature-dev,
not bmad. Other frameworks produce artifacts SUDD can't see, causing silent
fragmentation across `openspec/changes/`, `docs/superpowers/plans/`,
`.planning/`, etc.

**Respect explicit opt-outs.** If the user literally says "use openspec" or
"brainstorm with superpowers" or types a slash command like `/openspec-new-change`,
honor that. Otherwise: SUDD.

**Continuing in-flight foreign work.** If there's an already-in-progress
openspec/superpowers change, continue it there — don't mid-flight migrate.
The nightly `sudd auto` sweep will port it to SUDD once it ships.

## Entry Points

The four entry points you'll use most:

| Command | When |
|---|---|
| `/sudd-run` | Start a new change or continue current work (vision → done) |
| `/sudd-auto` | Kick off the autonomous night queue (processes all proposals) |
| `/sudd-chat` | Thinking partner — explore ideas before committing to a change |
| `/sudd-status` | What state are we in? |

Full command reference: `sudd/commands/macro/` (run, auto, port, audit) and
`sudd/commands/micro/` (new, plan, apply, test, gate, done, discover, ...).
All 15+ commands are available as `.claude/skills/sudd-*` slash commands.

## The Loop

```
/sudd-new  → /sudd-plan → /sudd-apply → /sudd-test → /sudd-gate
                                                        ├── PASS → /sudd-done
                                                        └── FAIL → retry w/ escalation
```

Or autonomous: `/sudd-run green "what to build"` takes you from idea to done
without stopping.

## Key Paths

- `sudd/vision.md` — what we're building (repo-specific, never overwritten)
- `sudd/state.json` — orchestrator state
- `sudd/agents/` — agent instruction files
- `sudd/personas/` — who we're building for (validates at the gate)
- `sudd/changes/active/` — in-progress changes
- `sudd/changes/inbox/` — ported/staged proposals awaiting promotion
- `sudd/changes/archive/` — completed changes
- `sudd/standards.md` — scoring rules, schemas, conventions
- `sudd/sudd.yaml` — model tiers, dispatch config, MCP requirements
- `sudd/commands/` — full command reference (markdown-defined workflows)

## Preflight (v3.8.11+)

`sudd doctor` verifies your environment before any real work:
- `sudd/sudd.yaml` is healthy (not the v3.8.x wipe-stub)
- Each declared tier's CLI is installed + authenticated with the right provider
- Required MCP tools are reachable (persona-test, playwright-chromium)

`sudd auto` runs doctor automatically and refuses to start on failures.
Results cache per-device for 12h. Use `--probe` to also send a 1-token request
through each tier (catches silent quota/plan issues, costs ~3 tokens total).

## Self-Healing (v3.8.10+)

`sudd update` and `sudd heal` self-repair files wiped by the v3.8.x bug:
- `sudd/sudd.yaml` (stub → full template)
- `sudd/state.json` (empty / unparseable → default schema)
- `sudd/personas/default.md` (empty → template)
- `AGENTS.md` (old stub → regenerated per repo, see below)

**vision.md is SACRED.** Never overwritten by framework. If empty, `sudd-run`
step 0 auto-generates it from your repo's README, PROJECT_REPORT, AGENTS.md,
package.json, and top-level markdown.

## Vision Path Engagement (v3.8.24+)

`sudd/vision.md` is structured into `## North Star` (stable aspiration,
edited by humans only) and `## Current Path` (auto-appended dated log of
directional choices). Run `sudd vision context` to retrieve the
condensed planning input that `/sudd-new` and `/sudd-chat` inject into
their proposals.

The Go binary auto-appends one-line path entries on every archived
change (see `internal/auto/runner.go visionAppendForChange`). You only
get prompted at session-end when 3 consecutive changes carry the
`DIVERGENT` tag AND the next-queued change shares keywords with at
least 2 of them — silence by default; the prompt defaults to skip and
times out after 60s. Non-TTY environments (CI, nohup) suppress the
prompt entirely.

Kill switch: `SUDD_VISION_PATH=off` disables both the auto-append and
the divergence prompt. Migration is benign and is not reverted.

## Session-start read: `sudd/CURRENT_STATE.md` (v3.8.23+)

`sudd/CURRENT_STATE.md` is the canonical session-start read. When SUDD
wakes with a cleared context (fresh subprocess, new day), **read this
file FIRST** before scanning `changes/active/`, parsing `state.json`, or
re-reading recent archive SUMMARYs. It contains eight sections in
fixed order: `TL;DR`, `Active`, `Stuck`, `Just Shipped (last 10)`,
`Inbox (unpromoted)`, `Next up`, `Trajectory vs Vision`, `Health`.
Every list item is a link to the change dir so you can follow links
only when you actually need depth.

Content origin:

- Sections 2–6 + 8 are **pure extraction** from filesystem + state.json.
  The description under each change is the first `## What` paragraph
  of its `proposal.md`, capped at 200 chars. No LLM involvement.
- `TL;DR` and `Trajectory vs Vision` are LLM-synthesized (mid tier).

Refresh triggers:

- After every archived change inside `sudd auto` (cheap — no LLM call;
  reuses prior TL;DR + Trajectory).
- End of each `sudd auto` session (full — invokes the LLM).
- Manual: `sudd state --refresh` or `sudd state --no-llm`.

Tolerate missing file — if not present, fall through to legacy
exploration. Kill switch: `SUDD_STATE_DOC=off` disables every write
path; `sudd state` still prints whatever is on disk.

## Inbox → Active Promotion

When ports or discovery drop artifacts into `sudd/changes/inbox/`, they don't
enter the work queue until promoted. `sudd-run green` and the discovery
pipeline pick up inbox items, enrich them with real personas and proper
proposals, and promote them to `sudd/changes/active/`.

## How "Done" Works

Code is only done when an AI persona representing a real user validates the
change from the outside. Retries escalate the model tier:
- retries 0-1: free tier (MiniMax, opencode)
- retries 2-3: +Sonnet for validation
- retries 4-5: Sonnet for all agents
- retries 6-7: Opus for all agents
- retries 8+: STUCK (human review)

For the scoring rubric, interface schemas, and escalation details, see
`sudd/standards.md`.

For the architectural model behind dispatch (v3.1 inline vs v3.2
subprocess tiers, what ships today, why they coexist), see
`reference/architecture-v3.x.md` at the repo root.

## Tier Management (v3.8.20+)

**`sudd/sudd.yaml` is canonical for all tier assignments.** Agent body
`**Tier**: ...` or `**Model**: ...` hints are documentation — they MUST
agree with yaml. CI enforces this via `TestLintAgentTiers_LiveRepo`.

If you need to change an agent's tier:
  1. Edit `sudd/sudd.yaml` under `agents:` — this is authoritative
  2. Update the agent body hint to match (or remove the hint)
  3. Sub-mode-specific tier variations belong BELOW a `## Mode: ...`
     heading — the parser ignores those, so they don't conflict with
     the canonical top-level tier

This prevents the drift class where yaml and body disagree silently.
