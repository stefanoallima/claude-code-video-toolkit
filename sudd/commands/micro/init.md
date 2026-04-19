---
name: "SUDD: Init"
description: Initialize SUDD2 in any repository — copies agents, commands, memory structure, and personas
category: SUDD
tags: [sudd, init, setup]
---

You are initializing SUDD2 in the current repository. This sets up the full autonomous development framework with 20 agents, memory system, and orchestrator commands.

**Input**: Optional project description (e.g., `/sudd:init This is a FastAPI backend for consumer insights`)

---

## Step 1: Check if already initialized

Look for `agents/` folder and `.claude/commands/sudd/run.md`. If both exist:
```
SUDD2 already initialized in this repo.
Run /sudd:run to start processing tasks.
```
Stop here.

---

## Step 2: Create folder structure

Create these directories:
```
agents/
personas/
changes/active/
changes/archive/
memory/
memory/context-cache/
memory/stuck-history/
```

---

## Step 3: Copy agent files (20 agents)

Create each of the following agent `.md` files in `agents/`. Each file contains the full agent instructions.

**Copy from the sudd2 template repo.** If not available, create from the canonical definitions:

### Discovery & Research
1. `agents/researcher.md`
2. `agents/persona-detector.md`
3. `agents/persona-researcher.md`
4. `agents/task-discoverer.md`

### Planning
5. `agents/antigravity.md`
6. `agents/deep-think.md`
7. `agents/solution-explorer.md`
8. `agents/architect.md`
9. `agents/decomposer.md`

### Implementation
10. `agents/coder.md`
11. `agents/qa.md`

### Validation
12. `agents/handoff-validator.md`
13. `agents/contract-verifier.md`
14. `agents/peer-reviewer.md`
15. `agents/persona-validator.md`
16. `agents/ux-tester.md`
17. `agents/blocker-detector.md`

### System Management
18. `agents/learning-engine.md`
19. `agents/monitor.md`
20. `agents/context-manager.md`

**Source**: Read each file from `C:\Users\tucan\Documents\stefano\hackaton\huggingface_gradio\sudd2\agents\` and write to `{cwd}/agents/`.

If the sudd2 template path is not accessible, use WebFetch to get from the GitHub repo.

---

## Step 4: Create memory files

Write `memory/lessons.md`:
```markdown
# SUDD2 Lessons Learned

This file is updated automatically after each task. Agents read it to avoid repeating mistakes.

## Template
- **Task**: [name]
- **What worked**: [approach that succeeded]
- **What failed**: [approach that didn't work]
- **Lesson**: [takeaway for future tasks]

---

(No lessons yet — run `/sudd:run` to start building history)
```

Write `memory/patterns.md`:
```markdown
# SUDD2 Patterns

Patterns are lessons that appear 3+ times. Automatically promoted from `lessons.md` by the learning-engine agent.

## Failure Patterns

(No patterns detected yet)

## Success Patterns

(No patterns detected yet)
```

Write `memory/session-log.md`:
```markdown
# SUDD2 Session Log

Health reports from the monitor agent. Most recent first.

---

(No sessions yet)
```

Create directory `memory/stuck-history/` and write `memory/stuck-history/.gitkeep`:
```
# Stuck task histories are saved here by /sudd:done for STUCK changes.
# Each file: {change-id}.md with full feedback history and rollback commands.
```

### Global Learning Directory (cross-repo)

Check if `~/.sudd/learning/` exists. If not, create it:
```bash
mkdir -p ~/.sudd/learning
```

Write `~/.sudd/learning/patterns.md` (only if it doesn't already exist):
```markdown
# SUDD Global Patterns

Patterns shared across all SUDD-managed repositories.
Each pattern includes a **Source:** tag identifying the originating repo.

---

(No global patterns yet)
```

Log: "Global learning directory: ~/.sudd/learning/ (patterns shared across repos)"

### MemPalace Setup (v3.6 — optional)

Check if `sudd.yaml → mempalace.enabled` is true:

```
If mempalace.enabled:
  1. Check if mempalace CLI is installed:
     which mempalace || mempalace --version

  2. If NOT installed:
     Log: "⚠ MemPalace not installed. Semantic learning disabled."
     Log: "  Install: pip install mempalace"
     Log: "  Then re-run /sudd:init to complete setup."
     (Continue init — MemPalace is optional)

  3. If installed:
     mempalace init {cwd}/sudd/memory/
     Log: "✓ MemPalace initialized for project {basename}"

  4. Display MCP configuration instructions:
     Log: "To enable semantic search in Claude Code, add to settings.json → mcpServers:"
     Log: '  "mempalace": {'
     Log: '    "command": "mempalace",'
     Log: '    "args": ["mcp"]'
     Log: '  }'
     Log: ""
     Log: "Or for other CLI tools, start the MCP server: mempalace mcp"

If NOT mempalace.enabled:
  Log: "ℹ MemPalace disabled. Enable in sudd.yaml for semantic learning."
  Log: "  (Optional — tag-based learning works without it)"
```

---

## Step 5: Create default persona

Write `personas/default.md`:
```markdown
# Persona: Default End-User

This is the FALLBACK persona used when no specific consumer is detected. In practice, the persona-detector and persona-researcher agents construct task-specific consumer personas dynamically.

**Role:** Technical Lead / Project Owner
**Context:** Uses AI coding agents to build software autonomously. Returns expecting completed, documented, working code.

## Goals
1. Every task produces working code with clear documentation
2. The system runs autonomously without asking questions
3. When something fails, it retries with escalation — not a dead stop
4. Clear visibility into what was accomplished and what's still pending

## Frustrations
1. AI writes code that compiles but doesn't actually do anything useful
2. Systems that ask "what should I do?" instead of trying harder
3. Hours of compute time with nothing to show for it
4. Over-engineered solutions when something simple would work

## Success Criteria
> "I came back and the task is completed. The code works, it's documented, and I can see exactly what happened."

## Deal-Breakers
1. Empty/mock data in outputs — if the API returns `[]`, that's a fail
2. Code that doesn't run — syntax errors, missing imports
3. No tests — untested code is unfinished code
```

If the user provided a project description, customize the persona's Role and Context to match.

---

## Step 6: Create example change

Write `changes/active/example_getting-started_01/proposal.md`:
```markdown
# Change: example_getting-started_01

## Status
active

## What
This is a placeholder change. Delete this directory and create real changes with `/sudd:new`, or let the task-discoverer agent generate them.

## Why
Example for getting started with SUDD.

## Size: S
```

Write `changes/active/example_getting-started_01/tasks.md`:
```markdown
# Tasks: example_getting-started_01

- [ ] Replace this example with a real task
```

---

## Step 7: Create AGENTS.md (if it doesn't exist)

If `AGENTS.md` does not already exist, create it with the SUDD integration block below.
If `AGENTS.md` already exists, append the SUDD section (between markers) only if not already present.

**Do NOT overwrite project-specific content** in AGENTS.md, CLAUDE.md, or GEMINI.md.

Add this block:
```markdown
<!-- SUDD:START -->
## SUDD — Simulated User-Driven Development

This project uses SUDD for autonomous AI-driven development.

**Commands:** `/sudd:run`, `/sudd:new`, `/sudd:plan`, `/sudd:apply`, `/sudd:test`, `/sudd:gate`, `/sudd:done`, `/sudd:status`, `/sudd:chat`

**Key paths:** `sudd/vision.md` (what we build), `sudd/agents/` (agent instructions), `sudd/personas/` (who we build for), `sudd/standards.md` (rules + schemas)

The CLI agent is the orchestrator. Agents are markdown instructions. Code is only "done" when validated from the user's perspective.
<!-- SUDD:END -->
```

---

## Step 8: Install persona-browser-agent (REQUIRED for browser testing)

persona-browser-agent provides real browser-based persona testing. Without it, gate
validation falls back to static code analysis which misses real UX issues.

```bash
# Check if already installed:
persona-test --help 2>/dev/null && echo "INSTALLED" || echo "NOT_INSTALLED"

# If NOT_INSTALLED:
# Option 1: Install from sibling repo (if cloned alongside this project)
pip install -e ../persona-browser-agent && playwright install chromium

# Option 2: Install from git
pip install git+https://github.com/stefanoallima/persona-browser-agent.git
playwright install chromium

# Verify:
persona-test --help
# Should show: "Persona Browser Agent — AI-driven browser testing as simulated personas"

# Set API key for browser testing LLM (Gemini Flash via OpenRouter):
# Add to your shell profile (~/.bashrc, ~/.zshrc, or Windows env vars):
export OPENROUTER_API_KEY="sk-or-..."
```

If the Go CLI (`sudd init`) is used, it will auto-detect and install persona-browser-agent
from a sibling directory automatically.

---

## Step 9: Initialize git (if not already)

If `.git/` doesn't exist: `git init`

Create `.gitignore` if it doesn't exist, add:
```
memory/context-cache/
```

---

## Step 10: Verify and report

Count files created. Print:

```
SUDD2 INITIALIZED
══════════════════
Agents:    20 (in agents/)
Personas:  1 default (in personas/)
Changes:   1 example (in changes/active/)
Memory:    3 files (lessons, patterns, session-log)
Commands:  /sudd:run, /sudd:add-task, /sudd:status

Next steps:
  1. Add tasks:     /sudd:add-task
  2. Run session:   /sudd:run
  3. Check status:  /sudd:status
══════════════════
```
