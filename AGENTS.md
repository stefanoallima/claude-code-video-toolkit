# SUDD Integration

This project uses **SUDD** (Simulated User-Driven Development) for autonomous AI-driven development. The CLI agent is the orchestrator. Everything else is markdown.

## Commands

| Command | Purpose |
|---------|---------|
| `/sudd:run green "..."` | Full autonomous workflow |
| `/sudd:new` | Create a change proposal |
| `/sudd:plan` | Generate specs, design, tasks |
| `/sudd:apply` | Implement tasks |
| `/sudd:test` | Run tests |
| `/sudd:gate` | Persona validation gate |
| `/sudd:done` | Archive completed change |
| `/sudd:status` | Show current state |
| `/sudd:chat` | Thinking partner mode |

## Key Paths

- `sudd/vision.md` — what we're building
- `sudd/state.json` — orchestrator state
- `sudd/agents/` — agent instruction files
- `sudd/personas/` — who we're building for
- `sudd/changes/active/` — in-progress changes
- `sudd/standards.md` — scoring, schemas, rules
- `sudd/sudd.yaml` — model tiers, dispatch config

## How It Works

Code is only "done" when validated from the actual user's perspective. The workflow (Ralph Loop) cycles: new -> plan -> apply -> test -> gate. Only EXEMPLARY (98-100) passes the gate. Failures retry with model escalation.

For full details, read `sudd/standards.md`.
