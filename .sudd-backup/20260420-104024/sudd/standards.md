# SUDD Standards
**SUDD Version: 3.3**

Shared definitions referenced by all agents. Loaded by context-manager per agent.

## Activation Protocol

Every agent follows this sequence:
1. Check PREREQUISITES — halt if unmet
2. Load context via context-manager
3. Execute process steps
4. Write output to OUTPUTS location
5. Hand off to NEXT agent

## Scoring

All validation uses named rubric levels. Agents select a level and justify with evidence.

| Level | Score | Gate | Criteria |
|-------|-------|------|----------|
| EXEMPLARY | 98-100 | PASS | All requirements met. No gaps. Consumer would use immediately. |
| STRONG | 80-97 | FAIL | Good but has gaps. Consumer needs refinements. |
| ACCEPTABLE | 60-79 | FAIL | Functional but significant issues. Consumer struggles. |
| WEAK | 30-59 | FAIL | Major problems. Consumer cannot use effectively. |
| BROKEN | 0-29 | FAIL | Non-functional or empty. Consumer rejects outright. |

Only EXEMPLARY passes the gate. Every level choice must cite evidence (file:line or specific output).
Do NOT pick a numeric score first then map to level. Pick the level first, then assign a score within that range.

## Task-Level Scoring (v3.1 — Rubric-Based)

Task micro-personas use rubric-based PASS/FAIL (not the named rubric):

### Rubric Categories and Thresholds
| Category | Threshold | Rationale |
|----------|-----------|----------|
| CONTRACT | 100% (all must pass) | Schema mismatch = consumer crashes |
| ERROR HANDLING | 100% (all must pass) | Unhandled errors = production failures |
| EDGE CASES | 100% (all must pass) | Edge cases are where bugs hide |
| BEHAVIORAL | 95%+ (near-perfect) | Slight flexibility for large behavioral sets |

Any CONTRACT, ERROR HANDLING, or EDGE CASES failure = automatic FAIL.
BEHAVIORAL allows missing at most 1 in 20 criteria.

### Confidence Scores (v3.1)

Every subagent return includes a confidence field:

| Confidence | Meaning |
|-----------|--------|
| HIGH | Thoroughly checked, certain of verdict |
| MEDIUM | Main paths checked, some aspects unverifiable |
| LOW | Uncertain — dynamic imports, complex logic, ambiguous spec |

**Orchestrator rules:**
- PASS + HIGH: proceed normally
- PASS + MEDIUM: proceed, log "MEDIUM confidence from {agent}: {reason}" for gate awareness
- PASS + LOW: re-dispatch with higher-tier model for second opinion
- FAIL + any: always FAIL (fail-safe)

## Subagent Return Schemas (v3.1)

Every subagent MUST return a structured result matching these schemas. The orchestrator validates the return and retries if malformed.

### Common fields (all subagents):
- `confidence`: LOW | MEDIUM | HIGH

### Per-agent schemas:

**coder**: `{files_changed: [string], commit_sha: string, self_review: string, micro_persona_refined: bool, confidence}`

**qa**: `{tests_written: [string], test_count: int, rubric_criteria_covered: [string], confidence}`

**contract-verifier**: `{verdict: PASS|FAIL, contracts_checked: int, violations: [{severity, field, expected, got, file_line}], confidence}`

**wiring-checker**: `{verdict: PASS|FAIL, connected: int, dead_ends: [{artifact, type, suggested_fix}], deferred: [{artifact, responsible_task}], confidence}`

**integration-reviewer**: `{verdict: PASS|FAIL, data_flow_trace: string, checks: [{check, status, detail}], confidence}`

**ux-reviewer**: `{verdict: PASS|FAIL, structural: [{check, status, detail}], design_quality: [{check, status, detail}], feedback_for_coder: [string], confidence}`

**micro-persona-validator**: `{verdict: PASS|FAIL, consumer: string, rubric_results: {contract, error_handling, edge_cases, behavioral}, squad_results: {}, feedback_for_coder: [string], confidence}`

**persona-validator**: `{score: int, level: string, consumer: string, objectives_met: [{objective, met, detail}], critical_assessment: string, confidence}`

**peer-reviewer**: `{verdict: APPROVE|REQUEST_CHANGES|REJECT, score: int, issues: [{severity, description, file_line}], confidence}`

**code-reviewer**: `{issues: [{severity, description, file_line, fix}], design_adherence: bool, design_issue_detected: bool, contract_revision_detected: bool, confidence}`

**macro-wiring-checker**: `{verdict: PASS|FAIL, connected: int, dead_ends: [{artifact, source_task, fix}], orphaned: [{artifact, broken_by_task}], confidence}`

**architect**: `{design_md_path: string, components: [string], critique_rounds: int, open_concerns: [string], confidence}`

**solution-explorer**: `{selected: string, candidates: [{name, score, rationale}], trade_offs: string, confidence}`

**ux-tester**: `{verdict: PASS|FAIL, score: int, scenarios_tested: [{objective, result, screenshots}], issues: [{severity, description}], confidence}`

### Subagent Error Protocol

1. Unstructured return → retry with "Return ONLY this JSON schema: {schema}" (max 2 retries)
2. Timeout → retry with reduced context (max 1 retry)
3. Wrong schema (missing fields) → retry with "Missing: {fields}" (max 1 retry)
4. 3 consecutive failures → escalate model tier (low → mid → top)
5. BLOCKED → surface to orchestrator with reason

## Handoff Contracts

Every boundary between producers and consumers requires:
- **Format**: exact output structure (JSON, markdown, file, etc.)
- **Schema**: required fields with types
- **Encoding**: UTF-8, URL-encoded, ISO 8601 dates, etc.
- **Completeness**: expected item count or "all"
- **Validation**: how to verify correctness

Silent handoff failures (wrong encoding, missing fields, partial data) are the #1 cause of false "success."

## Agent Invocation (v3.2 — Process Dispatch)

"Dispatch(agent=X)" means:
1. Read `sudd/sudd.yaml` → `agents.X.tier` → `tiers[tier]` → (model, provider, endpoint, cli)
   If agent has `cli_override` in sudd.yaml: override `cli` with the specified value (e.g., ux-tester requires claude-code for Playwright MCP tools)
2. If `tier == inline`: execute in orchestrator context (read `agents/X.md`, follow instructions)
3. If cli == opencode | crush | claude-code:
   a. Prepare context (curated file or full file list, per agent's `context` field in sudd.yaml)
   b. Construct dispatch prompt (~8-15 lines):
      - "Read sudd/agents/X.md below the --- separator for instructions"
      - Curated: "Read tasks/{task-id}/context-{agent}.md for your context"
      - Full: list raw file paths (design.md, specs.md, micro-persona.md, etc.)
   c. Guard against unbounded execution:
      - claude-code: use `--max-turns {max_turns}` (from sudd.yaml dispatch.max_turns[tier]) as primary guard
      - opencode/crush: rely on per-task time budget checks between dispatches (sudd.yaml time_budget.per_task_max)
      - On Unix/macOS: optionally wrap with `timeout {seconds} {command}` for hard kill
      - On Windows: `timeout` is not available; use `--max-turns` and time budget checks instead
   d. Execute via Bash
   e. Parse return (stdout JSON for opencode --format json, text for crush/claude-code)
   f. Update `state.json.task_progress.{task-id}.tokens_used` with tokens consumed by this dispatch
   g. Run anti-spinning checks (see Anti-Spinning Rules below)
4. On tier escalation (retry): resolve `escalation.ladder[retry_count]` — use `{agent_role}_floor` if defined, else `default_floor` as the floor tier. Apply `tier_escalation` for tier+1 agents.
5. On subprocess crash/timeout: retry once at same tier, then escalate

Dispatch command syntax varies by CLI. Read `sudd.yaml -> cli` to determine the active CLI, then see `sudd/cli-adapter.md -> dispatch-agent` for the exact invocation syntax.

Key differences:
- claude: uses `--bare --max-turns` for subprocess guard
- crush: uses `-y` (YOLO mode), timeout via Go binary
- opencode: uses `--format json`, timeout via Go binary

Note: For claude subprocesses, `--bare` is correct (file tools only, not skills). The orchestrator watchdog must NOT use `--bare`.

Independent agents may be dispatched in parallel via background Bash processes. Sequential agents wait for predecessor output files on disk.

## Persona Browser Agent Integration (v3.2)

For UI tasks, SUDD agents invoke `persona-browser-agent` — an external tool that uses browser-use + Gemini Flash (OpenRouter) to navigate the app as a simulated persona. It complements Playwright (technical checks) with AI-driven persona simulation (natural navigation, form filling, intuitiveness).

**Prerequisites:** `pip install -e persona-browser-agent && playwright install chromium && export OPENROUTER_API_KEY=...`

**Invocation** (via Bash from ux-tester or persona-validator agent):
```
python -m persona_browser.cli \
  --persona {persona_file_path} \
  --url {dev_server_url} \
  --objectives "{comma-separated objectives from persona}" \
  --scope {task|gate} \
  [--task-id {task-id}] \
  [--output {report_path.json}] \
  [--config persona-browser-agent/config.yaml] \
  [--screenshots-dir {screenshots_path}]
```

**JSON output to stdout:**
```json
{"status": "DONE|SKIP|ERROR", "elapsed_seconds": N, "agent_result": "...", "error": "..."}
```

**Routing by status:**
- `DONE` → parse `agent_result`, incorporate into agent verdict
- `SKIP` → log warning, continue with Playwright-only (not blocking)
- `ERROR` → log error, -5 score penalty, continue

**When it runs:**
- Per-task (step 3i): `--scope task` — narrow, tests only this task's UI changes
- Gate (step 6c): `--scope gate` — full app walkthrough as the change persona

**Config:** `sudd.yaml → browser_use` section controls provider, model, and `run_on` flags.
If `browser_use.enabled: false` or not configured, agents skip browser-use entirely.

## Anti-Spinning Rules (v3.2)

After each subprocess dispatch returns, the orchestrator runs these checks in priority order. If ANY check fires, the task is routed to `blocker-detector` for classification.

1. **Repetition detection**: Last 3 dispatches produced identical or near-identical output (diff < 5 lines changed). → BLOCKED: "Stuck in loop"
2. **Zero-diff guard**: Coder dispatch returned 0 files changed and no test results. → BLOCKED: "No progress"
3. **Token budget**: `task_progress.{task-id}.tokens_used > token_budget.per_task_max`. → blocked_failed
4. **Time budget**: `elapsed > time_budget.per_task_max`. → blocked_failed
5. **Oscillation detection**: Issue fixed in dispatch N, reintroduced in dispatch N+2 (ping-pong). → Escalate to architect (not coder)
6. **User input required**: Subprocess reports missing API key, credentials, or external dependency. → Park as `user_input_required`, write `tasks/{task-id}/user_input_required.md`

See `sudd/agents/blocker-detector.md` → "Anti-Spinning Detection (v3.2)" for full classification logic.

## State Validation

Every command that reads state.json must validate:
1. Valid JSON — if corrupt, restore: `git show HEAD:sudd/state.json > sudd/state.json`
2. `phase` ∈ {inception, planning, build, validate, complete}
3. If `active_change` set → `sudd/changes/active/{active_change}/` exists
4. If active change has tasks.md → `tasks_completed` matches `[x]` count
5. Mismatch → log WARNING, auto-correct from source of truth (tasks.md, git)

## State Schema (v3.2)

```json
{
  "sudd_version": "3.3",
  "mode": "green|brown",
  "active_change": "green_auth_01",
  "phase": "inception|planning|build|validate|complete",
  "last_command": "sudd:apply",
  "retry_count": 0,
  "tests_passed": false,
  "task_progress": {
    "T1": {
      "status": "validated",
      "micro_verdict": "PASS",
      "rubric_results": {
        "contract": "5/5",
        "error_handling": "3/3",
        "edge_cases": "4/4",
        "behavioral": "3/3"
      },
      "retries": 0,
      "confidence": "HIGH",
      "tokens_used": 0,
      "start_time": "2026-03-28T00:00:00Z",
      "user_input_file": ""
    }
  }
}
```

**Task status values:**
- `pending` — not yet started
- `in_progress` — coder is working on it
- `validated` — micro-persona PASS with rubric results and confidence
- `blocked_dependency` — waiting for another task
- `blocked_failed` — exhausted retry budget (5 attempts)
- `user_input_required` — blocked on human input (missing API key, credentials, external account). Parked with `tasks/{task-id}/user_input_required.md`. Auto-retried on orchestrator restart if condition resolved.

## Golden Rules

1. **EXEMPLARY is the threshold.** Only EXEMPLARY passes. No charity, no rounding up.
2. **Empty data = automatic fail.** Mock/placeholder output is never acceptable.
3. **Be specific.** File paths, line numbers, exact field names. No vague feedback.
4. **Handoffs must be explicit.** Define format, encoding, schema at every boundary.
5. **Retry must change approach.** Same approach twice = wasted compute.
