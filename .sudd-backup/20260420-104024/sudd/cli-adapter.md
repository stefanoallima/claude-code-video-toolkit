# CLI Adapter Reference

SUDD supports three CLI agents. Read `sudd.yaml -> cli` to determine which is active.
All agents receive the same SUDD commands and agent instructions — only invocation syntax differs.

## detect-cli

The orchestrator determines its CLI from:
1. `sudd.yaml -> cli` field (set during `sudd init`)
2. If missing: infer from environment — check which CLI you are running inside

## dispatch-agent

Run an agent as a subprocess. Primary operation for coder, qa, reviewer, etc.

**claude:**
```
claude -p --bare --model {model} --dangerously-skip-permissions --max-turns {max_turns} "{prompt}"
```
- `--bare` for subprocesses (file tools only, no skills)
- `--max-turns` is the primary runaway guard

**crush:**
```
crush run -m "{provider}/{model}" -y "{prompt}"
```
- `-y` enables YOLO mode (no confirmation prompts)
- No built-in turn limit — use timeout from Go binary or `timeout` command

**opencode:**
```
opencode run -m "{provider}/{model}" --format json --dir "{project_dir}" "{prompt}"
```
- `--format json` for structured output parsing
- No built-in turn limit — use timeout from Go binary or `timeout` command

## invoke-skill

Call a SUDD skill/command from within the CLI session.

**claude:** `/sudd:run {args}` — skills in `.claude/skills/sudd-*/SKILL.md`

**crush:** `/sudd:run {args}` — skills in `.crush/skills/sudd-*/SKILL.md`

**opencode:** `/sudd-run {args}` — commands in `.opencode/command/sudd-*.md` (hyphens, not colons)

## orchestrator-entry

How `sudd auto` (Go binary) starts a CLI session for a change.

**claude:**
```
claude -p "/sudd:run brown {change-id}" --max-turns 200
```

**crush:**
```
crush run -y "/sudd:run brown {change-id}"
```

**opencode:**
```
opencode run --dir "{project_dir}" "/sudd-run brown {change-id}"
```

## default-cli-flags

Applied by Go binary when `auto.cli_flags` is not set in sudd.yaml.

| CLI | Default flags |
|-----|--------------|
| claude | `--max-turns 200` |
| crush | _(none)_ |
| opencode | _(none)_ |

## parse-output

**claude:** Text on stdout. Parse for JSON blocks if structured return expected.

**crush:** Text on stdout. Same parsing as claude.

**opencode:** JSON on stdout (`--format json`). Parse directly.

## max-turns-guard

| CLI | Primary guard | Fallback |
|-----|--------------|----------|
| claude | `--max-turns {N}` | Go binary timeout |
| crush | Go binary timeout | `timeout {seconds} crush run ...` |
| opencode | Go binary timeout | `timeout {seconds} opencode run ...` |

## model-selection

SUDD does not dictate which model each CLI uses. If `sudd.yaml -> tiers` specifies a model/provider, the dispatch command includes `-m` or `--model`. If tiers are not configured, the CLI uses whatever model the user has configured in their CLI settings.

This means a Crush user with Gemini, an OpenCode user with GPT-4o, and a Claude Code user all run the same SUDD workflow — only the underlying model differs.
