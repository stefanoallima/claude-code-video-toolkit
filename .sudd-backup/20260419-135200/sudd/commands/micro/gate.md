---
name: sudd:gate
description: Persona validation gate — does this deliver value?
phase: validate
micro: true
prereq: sudd:test (tests passing)
creates: validation score
---

Persona validation gate. The critical check: does this deliver actual value?

**Input**:
- `/sudd:gate` — validate active change
- `/sudd:gate {change-id}` — validate specific change
- `/sudd:gate {persona}` — validate as specific persona

---

## ORCHESTRATOR CHECK

## PHASE GUARD
Read sudd/state.json. If tests_passed != true: STOP. "Run /sudd:test first."

---

## STEP 0: MACRO-WIRING CHECK (v3.0)

Dispatch(agent=macro-wiring-checker): verify all new code is reachable via git diff + full codebase.
If ANY dead end, orphaned, or deferred-unresolved → FAIL, log to log.md, route to coder to fix wiring.

---

## STEP 1: IDENTIFY CONSUMERS

Read `sudd/changes/active/{id}/specs.md`. Identify all consumers: immediate, downstream, end user, AI agents.

---

## STEP 1b: BROWSER TEST PRE-GATE CHECK (v3.7)

**YOU MUST EXECUTE THESE BASH COMMANDS NOW. Not later. Not optionally. NOW.**

First, resolve the change ID. Read `sudd/state.json` → `active_change` field.
Or use the change-id argument if provided via `/sudd:gate {change-id}`.
Substitute `{id}` below with the actual change ID.

```bash
# Check 1: persona-test installed?
persona-test --help >/dev/null 2>&1 && echo "BT_CHECK_1=PASS" || echo "BT_CHECK_1=FAIL: persona-test not installed"

# Check 2: API key set?
[ -n "$OPENROUTER_API_KEY" ] && echo "BT_CHECK_2=PASS" || echo "BT_CHECK_2=FAIL: OPENROUTER_API_KEY not set"

# Check 3: personas exist for this change? (replace {id} with actual change ID)
PERSONA_COUNT=$(ls sudd/changes/active/{id}/personas/*.md 2>/dev/null | wc -l)
[ "$PERSONA_COUNT" -gt 0 ] && echo "BT_CHECK_3=PASS ($PERSONA_COUNT personas)" || echo "BT_CHECK_3=FAIL: no personas"
```

**Read the output.** If ALL three say PASS: browser testing is possible. Continue.
If ANY says FAIL: log the failure. Browser testing will be skipped for this change.
Gate score is CAPPED AT 90 (cannot reach EXEMPLARY without browser evidence).

---

## STEP 2a: CODE INTELLIGENCE EXTRACTION (v3.7)

**WHEN TO RUN**: Steps 2a-2e run when ANY of these are true:
- The change touches frontend files (JSX, TSX, HTML, CSS, Vue, Svelte, etc.)
- The change has personas with `## Objectives` that reference user-facing features
- `sudd.yaml → dev_server.url` is set (a deployed app exists to test against)
- `sudd.yaml → browser_use.enabled` is true AND personas exist

**WHEN TO SKIP**: Only skip Steps 2a-2e if ALL of these are true:
- The change is purely backend/infrastructure (no user-facing routes)
- No personas exist in `changes/{id}/personas/`
- No deployed URL is configured

When in doubt, RUN browser testing. A false positive (testing a backend change
against the UI) wastes 2 minutes. A false negative (skipping browser testing
for a change that affects UX) misses real user-facing bugs.

```
  Pre-flight (EXECUTE THESE BASH COMMANDS — do not skip):

  1. Verify persona-browser-agent is installed:
     Run via Bash: persona-test --help 2>/dev/null && echo "PB_INSTALLED=true" || echo "PB_INSTALLED=false"
     If PB_INSTALLED=false:
       Try fallback: python -m persona_browser.cli --help 2>/dev/null && echo "PB_INSTALLED=true" || echo "PB_INSTALLED=false"
     If STILL false:
       Log: "⚠ persona-browser-agent not installed. Installing from sibling repo..."
       Run via Bash: pip install -e ../persona-browser-agent 2>/dev/null && playwright install chromium 2>/dev/null
       Re-check: persona-test --help 2>/dev/null && echo "PB_INSTALLED=true" || echo "PB_INSTALLED=false"
       If STILL false: FAIL — "persona-browser-agent not available. Run: cd ../persona-browser-agent && pip install -e . && playwright install chromium"

  2. Verify API key:
     Run via Bash: [ -n "$OPENROUTER_API_KEY" ] && echo "API_KEY=set" || echo "API_KEY=missing"
     If API_KEY=missing: FAIL — "Set OPENROUTER_API_KEY environment variable"

  3. Verify personas exist:
     Run via Bash: ls sudd/changes/active/{id}/personas/*.md 2>/dev/null | wc -l
     If 0: FAIL — "No persona files in changes/{id}/personas/"

  ALL THREE must pass before continuing. Do NOT fall through to code-analysis-only.

  Sequential dispatch:

  1. Dispatch(agent=code-analyzer-fe): Haiku → fe_codeintel.json
  2. Dispatch(agent=code-analyzer-be): Haiku → be_codeintel.json
     (1 and 2 run IN PARALLEL. Skip be if no backend.)

  3. Dispatch(agent=code-analyzer-reviewer): Sonnet
     Input: fe/be_codeintel.json, specs.md, design.md, personas/*.md
     Output: codeintel.json, manifest.json, rubric.md (DRAFT)

  4a. Dispatch(agent=rubric-adversary): Haiku → critique of draft rubric
  4b. Dispatch(agent=code-analyzer-reviewer, mode=revision) → rubric.md (v2)
  4c. Dispatch(agent=rubric-adversary): Haiku → critique of v2
  4d. Dispatch(agent=code-analyzer-reviewer, mode=revision) → rubric.md (FINAL)

  Re-runs on retry if code changed (git SHA check).

  Post-flight (VERIFY WITH BASH — do not skip):
  Run via Bash:
    [ -f "sudd/changes/active/{id}/codeintel.json" ] && echo "CODEINTEL=ok" || echo "CODEINTEL=missing"
    [ -f "sudd/changes/active/{id}/manifest.json" ] && echo "MANIFEST=ok" || echo "MANIFEST=missing"
    [ -f "sudd/changes/active/{id}/rubric.md" ] && echo "RUBRIC=ok" || echo "RUBRIC=missing"

  If ANY is missing: FAIL — "Code-analyzer pipeline incomplete. Missing: {list}"
  Do NOT proceed to Step 2b without these files.
  Do NOT fall back to code-analysis-only scoring.
```

---

## STEP 2b: BROWSER TESTING — MANDATORY (v3.7)

**THIS STEP IS NOT OPTIONAL. YOU MUST EXECUTE THESE BASH COMMANDS.**
Browser testing is the core of SUDD's persona validation. Without it, gate scores
are fabricated from static code analysis — which is NOT what SUDD does.

### 2b-1. Determine Dev Server URL

Read `sudd/sudd.yaml` and determine the dev server URL using this priority:

1. `sudd.yaml → dev_server.url` — if set and non-empty, use it (pre-deployed app)
2. `sudd.yaml → audit.url` — if set and non-empty, use it (legacy config)
3. Otherwise, you must start a local dev server (see 2b-2)

Save the URL as `DEV_URL` for all subsequent steps. If neither config field is set,
default to `http://localhost:{dev_server.port}` (default port: 3000).

### 2b-2. Start Dev Server (skip if URL already reachable)

First, check if `DEV_URL` is already reachable. For deployed apps (Render, Vercel, etc.),
the first request may wake a sleeping service — retry up to 60 seconds:

```bash
DEV_URL="..."  # from 2b-1
READY=false
for i in $(seq 1 60); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DEV_URL" 2>/dev/null)
  if echo "$STATUS" | grep -qE "200|301|302"; then
    READY=true
    break
  fi
  sleep 1
done
echo "ALREADY_RUNNING=$READY"
```

**If ALREADY_RUNNING=true**: Skip server startup, go to 2b-3.

**If ALREADY_RUNNING=false AND dev_server.url is set**: The deployed app is unreachable.
Log: "⚠ Deployed app at {DEV_URL} not responding after 60s. Browser testing will be skipped."
Cap gate score at 90. Continue to Step 2c WITHOUT browser reports.

**If ALREADY_RUNNING=false AND dev_server.url is NOT set**: Start a local dev server:

1. Read `sudd/sudd.yaml → dev_server.start_command` — if non-empty, use it
2. Else read `package.json → scripts.dev` or `scripts.start` — use `npm run dev` or `npm start`
3. Else check for `Makefile` with `dev` target — use `make dev`
4. Else check for `manage.py` — use `python manage.py runserver`
5. Else check for `main.py` or `app.py` — use `python -m uvicorn main:app --port {port}`

**Run the server so it survives across Bash tool calls**:

```bash
# Replace DEV_CMD and DEV_URL with detected values
DEV_CMD="npm run dev"
DEV_URL="http://localhost:3000"
TIMEOUT=30

# Use nohup (Unix) or start (Windows) to keep process alive after Bash returns.
if command -v nohup &>/dev/null; then
  nohup $DEV_CMD > .sudd_dev_server.log 2>&1 &
else
  # Windows Git Bash fallback — start in background without nohup
  $DEV_CMD > .sudd_dev_server.log 2>&1 &
fi
echo $! > .sudd_dev_server.pid
echo "Dev server started (PID: $(cat .sudd_dev_server.pid))"

# Wait for server to be ready
for i in $(seq 1 $TIMEOUT); do
  if curl -s -o /dev/null -w "%{http_code}" "$DEV_URL" 2>/dev/null | grep -qE "200|301|302"; then
    echo "SERVER_READY=true"
    break
  fi
  sleep 1
done
```

If server is NOT ready after timeout: FAIL — "Dev server not running at $DEV_URL after {timeout}s.
Check .sudd_dev_server.log for errors."

### 2b-3. Extract Objectives and Run persona-test

For EACH `.md` file in `sudd/changes/active/{id}/personas/`:

**Step A — Extract objectives**: Read the persona file using the Read tool. Look for:
- A `## Objectives` section → extract all text under it until the next `##` heading
- If no `## Objectives`, look for `## Goals` or `## Contract`
- If none found, use the full persona description as objectives

**Step B — Run persona-test**: Execute this Bash command (substitute all `{variables}`):

```bash
persona-test \
  --persona "sudd/changes/active/{id}/personas/{persona_name}.md" \
  --url "{DEV_URL}" \
  --objectives "{extracted objectives text}" \
  --manifest "sudd/changes/active/{id}/manifest.json" \
  --rubric "sudd/changes/active/{id}/rubric.md" \
  --codeintel "sudd/changes/active/{id}/codeintel.json" \
  --scope gate \
  --max-steps 50 \
  --timeout 120 \
  --screenshots-dir "sudd/changes/active/{id}/screenshots/gate/{persona_name}/" \
  --output "sudd/changes/active/{id}/browser-reports/{persona_name}.json"
```

If `persona-test` is not on PATH, use: `python -m persona_browser.cli` with the same flags.

**Handle each status** (read from the `status` field in the JSON output):
- `DONE` or `PARTIAL` → Report saved. Continue to next persona.
- `SKIP` → Log warning. Cap this persona's score at 90. Continue.
- `ERROR` → Log error. Apply -5 penalty. Continue to next persona.

Personas CAN run in parallel (separate browser instances). Each gets its own
browser-reports JSON and screenshots directory.

### 2b-4. Verify Reports Exist

After all persona-test runs complete, check that reports were created:

```bash
ls sudd/changes/active/{id}/browser-reports/*.json 2>/dev/null | wc -l
```

If count is 0: FAIL — "No browser reports generated. persona-test did not produce output."
If count < number of personas: Log warning, continue with available reports.

### 2b-5. Kill Dev Server

Only if YOU started the server in 2b-2 (skip if the URL was already running):

```bash
# Read PID from file (persists across bash calls)
if [ -f .sudd_dev_server.pid ]; then
  DEV_PID=$(cat .sudd_dev_server.pid)
  kill $DEV_PID 2>/dev/null || true
  rm -f .sudd_dev_server.pid
fi
# Clean up orphaned Chrome/Chromium instances (cross-platform)
if command -v pkill &>/dev/null; then
  pkill -f "chromium.*--remote-debugging" 2>/dev/null || true
elif command -v taskkill &>/dev/null; then
  taskkill /F /IM "chrome.exe" /FI "COMMANDLINE eq *remote-debugging*" 2>nul || true
fi
```

---

## STEP 2b-POST: BROWSER TEST POST-GATE AUDIT (v3.7)

```
Dispatch(agent=browser-test-auditor, mode=post-gate):
  Tier: low (cheap, fast — file existence checks only)
  Input: change ID

  Checks: browser-reports/ directory exists? At least 1 .json report?
          Each persona has a matching report? Reports have status=DONE?

  If FAILED → FAIL the gate. Score = 0.
    "Browser testing did not produce reports. Gate cannot pass without
     browser evidence. Check: did persona-test run? Did it error?"
  If VERIFIED → continue to Step 2c with the browser reports.
```

This agent is the LAST LINE OF DEFENSE. If the LLM skipped Step 2b (for any
reason — wrong judgment, context overflow, max-turns), this catches it.

---

## STEP 2c: PERSONA VALIDATION (v3.7 — reads browser-reports, no browser)

**REQUIRES**: Browser reports from Step 2b at `sudd/changes/active/{id}/browser-reports/{persona}.json`

```
PARALLEL dispatch per persona:
  Dispatch(agent=persona-validator):
    Input:
      - browser_report: READ the file at sudd/changes/active/{id}/browser-reports/{persona}.json
      - screenshots: LIST files in sudd/changes/active/{id}/screenshots/gate/{persona}/
      - change persona research, micro-persona results
      - macro-wiring report, specs.md, design.md, tasks.md
    Target: 98/100 EXEMPLARY
    Returns: {score, level, objectives_met, critical_assessment, confidence}
    Note: reads PB report + screenshots only. No browser, no PB calls, no dev server.
    cli_override: claude-code

  REPORT FORMAT: The browser-reports JSON contains a FULL pipeline report because
  gate.md passes --codeintel and --rubric to persona-test. Key fields to read:
    - status: "DONE" | "PARTIAL" | "SKIP" | "ERROR"
    - agent_result: natural-language persona experience (always present)
    - pages[]: per-page observations, pb_criteria, consumer_criteria (if pipeline ran)
    - summary: aggregate pass/fail counts (if pipeline ran)
    - network_verification: API contract verification results (if pipeline ran)
    - verification_tasks[]: data persistence, auth checks (if pipeline ran)
    - experience: navigator's subjective experience (if available)

  If a field is missing, the pipeline may have fallen back to navigator-only mode.
  In that case, use agent_result as primary evidence and note reduced confidence.

  IMPORTANT: If browser-reports/{persona}.json does NOT exist, this persona
  was not browser-tested. The persona-validator MUST note this — score is
  capped at 90 and the report must say "browser testing skipped".
```

---

## STEP 2d: UX TESTING — SPOT CHECK + TECHNICAL (v3.4)

```
  [If UI] Dispatch(agent=ux-tester):
    Input:
      - browser_report: READ sudd/changes/active/{id}/browser-reports/{persona}.json
      - screenshots: VIEW files in sudd/changes/active/{id}/screenshots/gate/{persona}/
      - design-system/MASTER.md (if exists)
    Returns: {verdict, score, spot_check_results[], technical_issues[], confidence}
    Note: Reads PB report + screenshots. Cross-checks PB findings against visual evidence.
    cli_override: claude-code

  Steps 2c and 2d run IN PARALLEL.
```

WAIT for all to complete.

---

## STEP 2e: UNIFIED SCORING (v3.7)

```
FOR EACH persona:
  Read: browser-reports/{name}.json, persona-validator output, ux-tester output

  JSON FIELD PATHS (browser-reports JSON structure):
    report.summary.pb_criteria_passed       — count of PB criteria that passed
    report.summary.pb_criteria_total        — total PB criteria evaluated
    report.summary.consumer_criteria_passed — count of consumer criteria passed
    report.summary.consumer_criteria_total  — total consumer criteria
    report.summary.verification_tasks_passed / verification_tasks_total
    report.summary.deal_breakers_triggered  — array of triggered deal-breakers
    report.network_verification.deal_breakers — API-level deal-breakers
    report.network_verification.issues      — API contract issues
    report.manifest_coverage.visited / not_visited — page coverage arrays
    report.pages[].pb_criteria[]            — per-page PASS/FAIL with evidence
    report.pages[].consumer_criteria[]      — per-page consumer criteria

  Compute scores (weights from sudd.yaml → browser_use.scoring):
    pb_score = summary.pb_criteria_passed / summary.pb_criteria_total * 100
      deal-breaker at HIGH confidence → instant 0
    consumer_score = weighted criteria score
      "Must Pass" failures × must_pass_weight (1.0)
      "Should Pass" failures × should_pass_weight (0.5)
      deal-breaker → instant 0
    verification_score = summary.verification_tasks_passed / summary.verification_tasks_total * 100
    penalties:
      network: -network_error_penalty per network_verification.issues count
      manifest: -manifest_missing_penalty per manifest_coverage.not_visited count; empty visited → FAIL
      spot_check: -spot_check_mismatch_penalty per mismatch
    informational (included in report, does NOT affect numerical score):
      experience: navigator satisfaction + "would recommend" (LLM-generated, approximate)
      NOT used for pass/fail decisions — trust objective criteria (pb_criteria, consumer_criteria)

  CHECK ALL (must ALL pass):
    □ pb_score >= rubric_threshold.pb (default 98)
    □ consumer_score >= rubric_threshold.consumer (default 98)
    □ verification_score >= rubric_threshold.verification (default 100)
    □ No deal-breakers triggered at HIGH confidence
    □ No API 500 errors during normal user flow
    □ Auth flow verified (token set, persists, sent on protected requests)
    □ Manifest coverage = 100% (all pages visited)
    □ persona-validator level == EXEMPLARY
    □ ux-tester spot check passed (no critical mismatches)

  ALL pass → GATE PASS | ANY fail → GATE FAIL with reasons + action items

ALL personas pass → Step 3 | ANY fails → GATE FAIL + targeted feedback

Failure report (append to log.md):
  ## Gate: FAILED
  ### Persona: {name}
  **PB Criteria**: {passed}/{total} ({score}%) — per-page breakdown:
    Page /{page}: ✓/✗ {criterion} — {evidence from PB report}
  **Consumer Criteria**: {passed}/{total} ({score}%)
  **Verification Tasks**: {passed}/{total}
  **Network Verification**: {issues count} — {specific API errors or auth failures}
  **Spot Check**: {ALL_MATCH/PARTIAL_MISMATCH/...} — {mismatched criterion_ids}
  **Navigator Experience**: {score}/10

  ### Action Items for Coder (priority order):
  1. [WIRING] {fix description — e.g., "settings page not reading name from API"}
  2. [FRONTEND] {fix description — e.g., "add confirm_password field"}
  3. [BACKEND] {fix description — e.g., "add created_at to GET /api/user/me"}
  4. [AUTH] {fix description — e.g., "session cookie not persisting after refresh"}

  ### Do NOT Touch:
  - {pages/endpoints that passed all criteria}
```

---

## DEV SERVER CLEANUP

After Step 2e (or any gate exit): kill dev server PID, kill Chrome instances, ensure no orphaned processes.

---

## STEP 3: AGGREGATE SCORES

```
Gate: {change-id}
  Consumer: {name} — Level: EXEMPLARY ({score}/100)
  ...per consumer...
  Lowest Level: {level}
  Result: PASS/FAIL
```

---

## STEP 3b: CRITICAL ASSESSMENT (MANDATORY — even when all EXEMPLARY)

```
For each EXEMPLARY consumer:
  Dispatch(agent=persona-validator, mode=critical-assessment):

  Review PB report evidence — specifically check these fields:
  - network_verification.issues — any API contract violations, even minor?
  - verification_tasks — any that barely passed or had ambiguous evidence?
  - discrepancies[] — where text scorer and visual scorer disagreed
  - experience.hesitation_points — where did the navigator struggle?
  - pb_criteria with confidence "medium" — uncertain assessments

  1. WEAKNESSES: Top 3 from the PB evidence above
  2. WOW FACTOR: 3 concrete improvements
  3. GUT CHECK: One honest sentence

  If ANY weakness would cause hesitation recommending,
  or a Score Reconciler discrepancy was resolved with medium confidence,
  or a verification task barely passed → DOWNGRADE to STRONG, RETRY.

  Only maintain EXEMPLARY if "I would use this RIGHT NOW and recommend without caveats."
```

Log to log.md under `## Critical Assessment`.

---

## STEP 4: PASS/FAIL

### PASS (all EXEMPLARY after critical assessment)
Update log.md with score + timestamp. Update state.json: gate_passed=true, gate_score={min}, phase="complete".
If autonomous → proceed to archive. If standalone → /sudd:done.

### FAIL (any consumer below EXEMPLARY)
Append to log.md `## Accumulated Feedback` → `### Retry {N} — Gate Score: {min}/100` with per-persona scores + issues. Never overwrite previous feedback.

retry_count++. If < 8 → escalate tier, return to /sudd:apply. If >= 8 → STUCK, run /sudd:done.

---

## ESCALATION

Follow `sudd/sudd.yaml` → `escalation.ladder` (floor-based, never downgrades). See run.md for full ladder semantics.

---

## OUTPUT

### Pass
```
Gate: PASSED ✓
  All consumers validated
  Minimum score: {min}/100 (must be >= 98)
If autonomous: archiving now...
If standalone: Run /sudd:done to archive
```

### Fail
```
Gate: FAILED ✗
  Lowest: {consumer} ({score}/100)
  Issues: {list}
  Retry: {N}/8 — Escalating to {tier}...
  Returning to /sudd:apply with feedback
```

---

## GUARDRAILS

- ALL consumers must be EXEMPLARY level
- Read ACTUAL code, not summaries
- Check for placeholders, not just functionality
- Accumulate ALL feedback across retries
- Always escalate on retry
