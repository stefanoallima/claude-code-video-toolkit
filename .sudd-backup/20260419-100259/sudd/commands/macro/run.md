---
name: sudd:run
description: Full autonomous SUDD workflow — from vision to done
phase: all
macro: true
---

Full autonomous SUDD workflow. Runs the complete loop from vision to done.

**Input**: 
- `/sudd:run` — continue with current state
- `/sudd:run green "description"` — start fresh from vision (heavy research)
- `/sudd:run brown` — continue existing work (light discovery)
- `/sudd:run {change-id}` — work on specific change

---

Agent invocation follows `sudd/standards.md` → Agent Invocation.

---

## ORCHESTRATOR STARTUP

1. **Load state**: Read `sudd/state.json`
2. **Determine mode**:
   - If `green` in args → mode = green, extensive research
   - If `brown` in args → mode = brown, continue existing
   - If change-id provided → focus on that change
   - Else use existing state
3. **Check for port**: If `imported_from` set, validate port completed
4. **Display status**:
   ```
   SUDD AUTONOMOUS SESSION
   ════════════════════════
   Mode: green | brown
   Active: {change-id} | none
   Phase: {phase}
   Tasks: N active | M completed
   ```
5. **Read config**: Read `sudd/sudd.yaml` for agent tiers, escalation ladder, cost_mode
   - If missing: warn "No sudd.yaml found, defaulting all agents to free tier"
5b. **Detect CLI**: Read `sudd.yaml -> cli`
   - Determines dispatch syntax for all agent invocations this session
   - Reference: `sudd/cli-adapter.md` for CLI-specific syntax
   - If missing: infer from environment (which CLI am I running inside?)
   - Skill invocation format: claude/crush use `/sudd:run`, opencode uses `/sudd-run`
5c. **Check for checkpoint**: If `sudd/changes/active/{id}/checkpoint.json` exists:
   → Load checkpoint state
   → Skip completed tasks
   → Resume from checkpoint's current_task and current_step
   → If checkpointed mid-squad: pass cached squad_results_so_far to next subagent
   → Log: "Resuming from checkpoint: {task} at {step}"
   → Delete checkpoint.json after successful completion

---

## MODE: GREEN (Vision → Implementation)

Used when starting from an idea/vision with minimal existing structure.

### Step 1: Discovery
```
Read: sudd/vision.md
Read: sudd/personas/*.md (if exist)
Search: codebase for related patterns

If vision.md is empty or vague:
  → Ask user for clarification (ONE question, then proceed)
  → Or use /sudd:chat to explore first
```

### Step 2: Discovery-Driven Change Generation (v3.4)

Before creating a single change, run the discovery pipeline to find ALL
work that needs doing. This replaces the old single-change approach.

```
DISCOVERY CHECK:
  Invoke /sudd:discover (follows staleness rules — may skip if recent)

  If discovery ran and generated proposals:
    → Multiple discovered_* proposals now exist in changes/active/
    → Pick the highest-priority proposal as active change
    → Continue to Step 3 with that change

  If discovery skipped (recent + no changes):
    → Check if any proposals exist in changes/active/ with status: proposed
    → If yes: pick highest-priority, continue to Step 3
    → If no: fall through to legacy single-change creation below

  LEGACY FALLBACK (no discovery results, no existing proposals):
    Generate change-id: {NNN}_green_{name}_{seq:02d}
      - NNN: count all dirs in changes/active/ + changes/archive/ + changes/stuck/, then +1, zero-pad to 3 digits
      - name: kebab-case from vision content
      - seq: next available number for this mode

    Create: sudd/changes/active/{change-id}/
      - proposal.md (from vision)
      - specs.md (discovered requirements)
      - design.md (architecture)
      - tasks.md (implementation checklist)
      - log.md (execution log)

Update: sudd/state.json
  - active_change = {selected change-id}
  - phase = "planning"
  <!-- Phase transition: none → planning (valid) -->
```

NOTE: When running inside /sudd:auto, the remaining discovered proposals
stay in the queue. After this change completes, auto processes the next one.

### Step 3: Research Agents (parallel)
```
For each major component in vision:
  Dispatch(agent=researcher): Investigate technology, patterns
  Dispatch(agent=persona-detector): Discover consumers
  Dispatch(agent=persona-researcher): Deep-research each consumer

Aggregate findings into specs.md

Dispatch(agent=persona-detector, scope=change): Discover change-level consumers
Dispatch(agent=persona-researcher, scope=change): Deep-research change consumers
  Write to: sudd/changes/active/{id}/personas/
```

### Step 3b: Persona Early Validation (v3.7 — catch shallow personas before coding)

**PREREQUISITE**: Step 3 MUST complete first (personas written to disk).
Step 3b is SEQUENTIAL after Step 3, never parallel.

Personas are the foundation of everything SUDD does. If they're vague, every
subsequent step (design, code, testing, gate) builds on a bad foundation.
Validate them NOW, before any code is written.

```
Ensure log.md exists (create if missing):
  If sudd/changes/active/{id}/log.md does NOT exist:
    Create it with header: "# Log: {change-id}\n\n"

Verify personas exist: ls sudd/changes/active/{id}/personas/*.md
If no personas found: SKIP Step 3b (Step 4 planning will still work, gate will catch gaps later)

FOR EACH persona in sudd/changes/active/{id}/personas/:
  Dispatch(agent=persona-validator, mode=persona-quality):

    Read the persona file. Check ALL of these:

    REQUIRED (fail if missing):
    □ ## Identity section with: name, role, tech comfort, context
    □ ## Objectives section with at least 1 concrete objective
    □ Each objective has specific success criteria (not vague "works well")
    □ ## Deal-Breakers section with at least 1 deal-breaker

    QUALITY (flag if weak):
    □ Objectives are MEASURABLE (can be verified by browser testing)
    □ Deal-breakers are SPECIFIC (not "bad UX" — what specifically?)
    □ Identity has enough detail for an LLM to act AS this person
    □ No placeholder text ("TBD", "TODO", "fill in later")
    □ ## Form Data section exists if persona will fill forms

    Result:
      PASS → persona is ready for design and coding
      WEAK → specific feedback on what to strengthen
      FAIL → missing required sections, cannot proceed

  If ANY persona is FAIL:
    Dispatch(agent=persona-researcher, mode=enrich):
      Input: the persona file path AND the validation output from above
      (pass the "Missing sections" and "Suggested enrichments" text from
       persona-validator's output directly in the dispatch prompt)
      Re-research the persona, fill missing sections, write updated file
    Re-validate (max 2 enrichment attempts)

  If ANY persona is WEAK after enrichment:
    Log warning but continue — weak personas produce weak gates

  OUTPUT: Write results to log.md under ## Persona Early Validation:
    ### {persona_name}: PASS | WEAK | FAIL
    {validation details}
  
  Update state.json: personas_validated = true
```

This step typically takes < 30 seconds. It prevents hours of wasted coding
against poorly-defined personas.

---

### Step 4: Planning
<!-- Phase transition: inception → planning (valid) -->
```
Dispatch(agent=antigravity): Back-plan from outcome
Dispatch(agent=deep-think): Align with vision
Dispatch(agent=architect): Design solution

Dispatch(agent=qa, mode=testability-review):
  - Read design.md acceptance criteria
  - Check testability of each criterion
  - Append ## Testability Notes to design.md

Write: design.md with architecture
Write: tasks.md with implementation tasks

If change involves UI (detected from proposal/vision keywords: UI, frontend, dashboard, form, page, web interface):
  Dispatch(agent=ux-architect):
    Read: proposal.md, specs.md, design.md, existing UI patterns
    Write: ## UI Specification section in design.md

  Dispatch(agent=ux-designer):
    Read ## UI Specification from design.md
    Run ui-ux-pro-max scripts to generate design-system/MASTER.md
    Generate per-page overrides in design-system/pages/
    Append ## Design Tokens to design.md

Dispatch(agent=micro-persona-generator):
  Read: tasks.md, design.md, specs.md, codebase
  Write: sudd/changes/active/{id}/tasks/{task-id}/micro-persona.md (one per task)
  Process in reverse dependency order (leaf tasks first)
```

---

### Step 4b: Architecture Review Loop (v3.7 — catch design flaws before coding)

Before writing any code, the design must survive peer review. This catches
flawed architecture BEFORE burning retries on implementation.

```
ARCHITECTURE REVIEW (max 2 rounds):

  Round 1:
    Dispatch(agent=peer-reviewer, mode=design-review):
      Input: design.md, specs.md, tasks.md, personas/*.md, codebase (existing patterns)
      (The agent's design-review mode in peer-reviewer.md defines the full
       10-point checklist. Do NOT duplicate the checklist here — the agent
       file is the single source of truth for what to check.)

      Output: ## Architecture Review section in log.md
        - APPROVED: design is ready for implementation
        - REVISE: specific issues with suggested fixes (max 5 items)

  If REVISE:
    Dispatch(agent=architect, mode=revision):
      Input: design.md, log.md ## Architecture Review feedback
      Action: revise design.md and tasks.md to address feedback
      Note: do NOT add scope — only fix the identified issues

    Round 2:
      Dispatch(agent=peer-reviewer, mode=design-review):
        Re-review revised design against original feedback
        Output: APPROVED or REVISE

    If still REVISE after Round 2:
      Log: "⚠ Architecture review concerns remain. Proceeding with noted risks."
      Append unresolved concerns to log.md ## Known Risks
      Continue to Step 4c (don't block forever on design perfection)

  If APPROVED:
    Log: "✓ Architecture review passed"

  Update state.json: architecture_reviewed = true

  OUTPUT: All results go to log.md under ## Architecture Review:
    ### Round 1: APPROVED | REVISE
    {reviewer output}
    ### Round 2 (if needed): APPROVED | REVISE
    {reviewer output}
    ### Known Risks (if unresolved after 2 rounds)
    {unresolved concerns}
```

---

### Step 4c: Design-Gate (v3.7 — lightweight persona check before coding)

The design-gate is a FAST persona check on the design itself (not code).
It catches misalignment between what personas need and what the design provides.

```
DESIGN-GATE:

  FOR EACH persona in sudd/changes/active/{id}/personas/:
    Dispatch(agent=persona-validator, mode=design-gate):
      Input: persona file, design.md, specs.md, tasks.md

      You are this persona. Walk through the DESIGN (not code — it doesn't exist yet).

      For each of your objectives:
        1. Is there a page/route/component designed for this objective?
        2. Is there a task in tasks.md that implements this objective?
        3. Does the API design support the data this objective needs?
        4. Are your deal-breakers addressed in the design?
        5. Would you be able to accomplish this objective with this design?

      Score: 0-100 (design readiness, not code quality)
        90+   → Design serves this persona well
        70-89 → Design has gaps but can proceed (log gaps)
        <70   → Design fundamentally misses this persona's needs

      Output: ## Design-Gate section in log.md

  If ANY persona < 70:
    → Dispatch(agent=architect, mode=revision) with design-gate gaps
    → If architect revised tasks.md:
        Regenerate micro-personas for changed tasks:
        Dispatch(agent=micro-persona-generator): only for tasks that changed
    → Re-run design-gate (max 1 revision — don't loop forever)

  If ALL personas >= 70:
    → Log: "✓ Design-gate passed (min: {score}/100)"
    → Proceed to build

  OUTPUT: Write to log.md under ## Design-Gate:
    ### {persona_name}: {score}/100 — PASS | FAIL
    {objective coverage table}
    {gaps found}

  Update state.json:
    design_gate_passed = true
    design_gate_score = {min score across personas}
    phase = "build"
  <!-- Phase transition: planning → build (valid) -->
```

**IMPORTANT**: If Step 4b or 4c caused architect to revise tasks.md, micro-personas
for affected tasks MUST be regenerated before proceeding to build. Stale
micro-personas that don't match the revised design will cause false gate failures.

This entire step (3b + 4b + 4c) adds ~2-5 minutes to the planning phase
but saves hours of wasted coding against bad designs or weak personas.

### Step 5: Build Loop

#### 5a. Dependency Analysis
```
Read tasks.md. For each pending task, extract:
  - Dependencies: field (list of task IDs)
  - Files: field (list of file paths)
  - SharedFiles: field (lock files, configs, routers — files multiple tasks may touch)

Build batches:
  - Tasks are INDEPENDENT if ALL of:
    1. Neither lists the other in Dependencies:
    2. Their Files: lists have no overlap
    3. Their SharedFiles: lists have no overlap
  - Group independent tasks into ordered batches
  - Dependent tasks go into later batches

SharedFiles examples (architect should declare these):
  - package.json, go.mod, requirements.txt (dependency files)
  - database migrations with sequence numbers
  - router/route config files, index.ts barrel exports
  - .env.example, shared config files

Example:
  T1 (no deps, files: a.go) ─┐
  T2 (no deps, files: b.go) ─┼─ Batch 1
  T4 (no deps, files: d.go) ─┘
  T3 (deps: T1, files: a.go, c.go) → Batch 2 (after T1 completes)
```

#### 5a-bis. Environment Smoke Test (v3.2)

Before the first task dispatch, verify the environment works:

```
Dispatch(agent=coder, tier=low, prompt="Smoke test"):
  "Read package.json / go.mod / requirements.txt.
   Run the install command. Run the test command.
   Report: dependencies OK? tests runnable? environment issues?"
  Returns: {environment_ok: bool, issues: [string], test_command: string}

If environment_ok == false:
  Check if user_input_required (missing env var, missing tool)
  If fixable: fix and re-test (max 2 attempts)
  If not fixable: park ALL tasks as user_input_required
```

#### 5b. Model Tier Selection (v3.2)
```
Read sudd.yaml → agents[agent].tier for default tier.
Read sudd.yaml → escalation.ladder[retry_count] for floor tier.
effective_tier = max(default_tier, floor_tier)
For code-reviewer: effective_tier = tier_escalation[coder_effective_tier]
Resolve tiers[effective_tier] → (model, provider, endpoint, cli)

Effort-based initial tier (overrides default if higher):
  task.effort == "S" AND task.files.length <= 2  → coder: low, code-reviewer: mid
  task.effort == "M" OR task.files.length <= 4   → coder: mid, code-reviewer: top
  task.effort == "L" OR files > 4                → coder: top, code-reviewer: top
```

#### 5c. Execute Batches
```
Read sudd.yaml → parallelization.mode (default: "sequential")

DEFAULT MODE: SEQUENTIAL
  STEP 1b: Inject top-5 items from memory/patterns.md + ~/.sudd/learning/patterns.md + memory/lessons.md (per apply.md STEP 1b)

  CANARY (v3.1 — before first batch):
    If no tasks completed yet:
      Run full pipeline on first task as canary (see apply.md STEP 2.5)
      If systemic failure: STOP, fix root cause, then continue

  For each batch, run tasks one at a time in main workspace:
    For each task in batch:
      Idempotency check: skip if [x] + commit exists (per apply.md 3-pre-a)
      3a.  Load micro-persona for this task (generate on-demand if missing)
      3b.  Dispatch(agent=qa): Write tests from rubric (TDD — first attempt only)
      3c.  Dispatch(agent=coder): Implement task (curated context)
      3d.  Dispatch(agent=code-reviewer): Round 1 review (curated context, tier+1)
      3e.  Dispatch(agent=coder): Fix run 1 (reads review-1.md)
      3f.  Dispatch(agent=code-reviewer): Round 2 review (FULL context, tier+1)
      3g.  Dispatch(agent=coder): Fix run 2 (reads review-2.md)
      3h.  VALIDATION SQUAD:
           i.   Dispatch(agent=contract-verifier)
           ii.  Dispatch(agent=wiring-checker)
           iii. Dispatch(agent=integration-reviewer, scope=task)
           iv.  [UI only] Dispatch(agent=ux-reviewer)
           v.   Dispatch(agent=micro-persona-validator)
      3i.  [UI only] Dispatch(agent=ux-tester): Browser validation
      If squad FAIL (3h):
        → retry 1-3: feedback → coder fix → re-run from 3d (code-reviewer → fix → squad)
        → retry 4-5: architect escalation → revised design → coder retry from 3c
        → retry 6+: mark blocked_failed, skip to next independent task
      Else: mark task validated, commit

      Change-level budget check:
        total = sum(state.json.task_progress.*.tokens_used)
        Update state.json.total_tokens_used = total
        If total > sudd.yaml.token_budget.per_change_max → archive as STUCK
        If total_elapsed > sudd.yaml.time_budget.per_change_max → archive as STUCK

  CHECKPOINT (v3.1):
    After each task completes (or between batches):
      If monitor detects context window >= 80% capacity:
        Save checkpoint to sudd/changes/active/{id}/checkpoint.json:
          sudd_version, timestamp, phase, task_progress, current_task,
          squad_results_so_far, retry_counts, lessons_injected,
          accumulated_feedback, canary_passed, resume_instruction
        Log: "Checkpoint saved. Session can resume with /sudd:run"

  After all tasks in batch:
    Dispatch(agent=integration-reviewer, scope=change): cross-task integration check

  Stagnation detection:
    If score delta < 5 across 2 consecutive retries → skip to architect escalation
    If 3+ tasks blocked_failed → pause, architect reviews entire design

OPT-IN MODE: WORKTREE (sudd.yaml parallelization.mode: worktree)
  For each batch:
    If batch.size == 1 or skip conditions met:
      → Run in main workspace (same as sequential above)

    If batch.size > 1:
      → Create worktree per task (via context-manager Worktree Management)
      → Dispatch each task in parallel:
          3a.  Load micro-persona
          3b.  Dispatch(agent=qa): Write tests (TDD)
          3c.  Dispatch(agent=coder, tier={from 5b}): Implement task
          3d.  VALIDATION SQUAD (runs INSIDE worktree before merge):
               NOTE: This worktree pipeline is INCOMPLETE — missing 3d-3g (code-reviewer rounds).
               Do NOT re-enable worktree mode until this pipeline is updated to match the full 3c-3i sequential pipeline.
               i-iv. Same as sequential mode
      → After all tasks complete, merge sequentially:
          - Before each merge: rebase worktree branch against current base
          - If rebase/merge conflicts: abort, mark task for sequential re-run
          - After each successful merge: run integration-reviewer on merged result
          - If integration fails post-merge: git revert the merge commit, mark for sequential re-run
          - Cleanup all worktrees
      → Re-run any conflict/failed tasks sequentially in main workspace
      → All lifecycle events logged to log.md

    After batch completes (all tasks merged or re-run):
      Dispatch(agent=integration-reviewer, scope=change): cross-task integration check

    Skip worktrees even in worktree mode if:
      - batch.size == 1
      - All tasks have Effort: S (overhead exceeds benefit)
      - Not in a git repo
      - git worktree add fails mid-batch → log warning, cleanup, fall back to sequential
```

#### 5d. Per-Task Retry Tracking
```
Track retry counts per task in state.json.task_progress:
  task_progress: { "T01": { "retries": 0, ... }, "T02": { "retries": 3, ... } }

Benefits:
  - Task that passed doesn't get re-run at higher tier unnecessarily
  - Escalation ladder applies per-task: T01 at free, T02 at sonnet (retry 3)
  - STUCK determination is per-task: T02 can be STUCK while T01 continues
```

### Step 6: Validate & Complete (AUTONOMOUS — no user intervention)
<!-- Phase transition: build → validate (valid) -->

This step runs as a **continuous loop** until PASS or STUCK. Do NOT stop and tell the user to run commands manually.

```
VALIDATION LOOP:
  6a. TEST PHASE (inline /sudd:test logic):
      - Detect test command (sudd.yaml or auto-detect)
      - Run all tests (unit, integration, coverage)
      - If tests fail:
          → Dispatch(agent=blocker-detector): classify failure
          → Dispatch(agent=coder): fix bugs
          → Re-run tests (max 3 quick-fix attempts)
          → If still failing after 3 attempts: increment retry, escalate tier, go to 5c
      - Update state.json: tests_passed = true

  6a-bis. MACRO-WIRING CHECK (v3.0):
      Dispatch(agent=macro-wiring-checker):
        - Git diff against base branch → all new artifacts
        - Trace from entry point to each artifact
        - Check DEFERRED resolutions from per-task wiring reports
        - Any DEAD END/ORPHANED/DEFERRED_UNRESOLVED → FAIL → route to coder to fix wiring

  6b. REVIEW PHASE:
      Dispatch(agent=peer-reviewer): Final code review

  6c. GATE PHASE (v3.4 — FULL gate.md, including browser testing):

      **EXECUTE THE FULL gate.md WORKFLOW. DO NOT USE A SIMPLIFIED VERSION.**
      The gate includes browser testing with persona-browser-agent — this is mandatory.

      Follow gate.md steps IN ORDER:
        Step 0:  Macro-wiring check
        Step 1:  Identify consumers
        Step 2a: Code intelligence extraction (code-analyzer pipeline + adversarial rubric)
        Step 2b: BROWSER TESTING — run persona-test for each persona
                 MANDATORY when personas exist AND a dev_server.url or deployed app is available.
                 This launches a real browser, navigates the app AS each persona,
                 and produces JSON reports + screenshots. DO NOT SKIP THIS STEP.
                 DO NOT substitute it with LLM-based "persona simulation".
        Step 2c: Persona-validator reads the browser reports (not code — the actual reports)
        Step 2d: UX-tester spot-checks browser reports against screenshots
        Step 2e: Unified scoring with formula from sudd.yaml
        Step 3:  Aggregate scores
        Step 3b: Critical assessment (mandatory second pass)

      If ALL consumers EXEMPLARY (>= 98/100):
        → GATE PASSED
        → Continue to 6d
      Else (ANY consumer below EXEMPLARY):
        → Log feedback to log.md (## Accumulated Feedback)
        → retry_count++ (per-task)
        → If gate feedback indicates DESIGN FLAW (not just code bug):
            Clear state.json: design_gate_passed = false
            (Next retry or resume will re-run design-gate before coding)
        → If retry < 8: escalate tier per ladder, GO BACK TO Step 5c (re-apply with feedback)
        → If retry >= 8: mark STUCK, continue to 6d

  6d. ARCHIVE PHASE (inline /sudd:done logic):
      - If PASSED:
          → Step 2a: Dispatch(agent=learning-engine, mode=1): extract lessons to memory/lessons.md
          → Step 2b: Dispatch(agent=learning-engine, mode=3): PATTERN PROMOTION (MANDATORY)
            - Scan ALL lessons, build tag frequency map
            - Promote patterns (3+ occurrences from different changes)
            - Write to memory/patterns.md AND ~/.sudd/learning/patterns.md (if enabled)
            - This step MUST run — see done.md Step 2b for full algorithm
          → Step 2c: INDEX SESSION IN MEMPALACE (if mempalace.enabled)
            - Index full log.md into sessions room for rich context preservation
            - Index lesson + new patterns into respective rooms
            - See done.md Step 2c for details
          → Move to sudd/changes/archive/{change-id}_DONE/
          → Create SUMMARY.md
      - If STUCK:
          → Step 2a: Dispatch(agent=learning-engine, mode=1): extract lessons (failures too)
          → Step 2b: Dispatch(agent=learning-engine, mode=3): PATTERN PROMOTION (still runs)
          → Step 2c: INDEX SESSION IN MEMPALACE (if mempalace.enabled)
          → Move to sudd/changes/archive/{change-id}_STUCK/
          → Create STUCK.md with rollback commands
          → Copy to sudd/memory/stuck-history/
      - Update state.json: clear active_change, reset phase to inception
      - Git commit and merge to main (if DONE)
      <!-- Phase transition: validate → complete (valid) -->
```

#### 6e. Post-Completion Verification (v3.2)

After archiving as DONE:

```
FINAL VERIFICATION:
  1. Start the application (detect start command from sudd.yaml or package.json)
  2. Wait for startup (health check endpoint or port listen, timeout 30s)
  3. If UI change: Dispatch(agent=ux-tester, scope=final):
       Screenshot main routes, verify renders, no console errors
  4. If API change: curl key endpoints, verify 200 responses
  5. Write: sudd/changes/archive/{id}_DONE/verification.md

If verification FAILS:
  → Do NOT un-archive (code passed all gates)
  → Log failure details in verification.md
  → User decides whether to fix or ship
```

**CRITICAL**: This entire step is autonomous. The orchestrator MUST NOT stop after tests pass and say "run /sudd:gate". It MUST NOT stop after gate passes and say "run /sudd:done". The loop runs continuously until the change is archived as DONE or STUCK.

---

## MODE: BROWN (Continue Existing)

Used when specs/code already exist.

### Step 1: Assess State
```
Read: sudd/state.json
Read: sudd/changes/active/{active_change}/*.md
Read: codebase for context

If no active change:
  → List available changes
  → Auto-select if only one
  → Else ask user
```

### Step 2: Continue from Phase
```
Switch on phase:
  case "inception": → run planning   <!-- Phase transition: inception → planning (valid) -->
  case "planning":
    → Check state.json flags:
      If personas_validated != true AND personas exist → run Step 3b
      If architecture_reviewed != true AND design.md exists → run Step 4b
      If design_gate_passed != true AND design.md + personas exist → run Step 4c
    → Then proceed to build
  case "build":     → continue tasks  <!-- Phase transition: build → validate (valid) -->
  case "validate":  → run validation  <!-- Phase transition: validate → complete (valid) -->
  case "complete":  → archive

Note: State flags (personas_validated, architecture_reviewed, design_gate_passed)
prevent re-running loops that already passed on resume. If a loop was interrupted,
its flag won't be set and the loop re-runs safely.
```

### Step 3: Build Loop
```
Same as green mode Step 5 (dependency analysis → per-task validation squad), including:
  - Per-task validation squad: contract-verifier → wiring-checker → integration-reviewer → micro-persona-validator
  - Micro-persona loading and on-demand generation
  - Task retry budget (3 coder + 2 architect = 5 max)
  - Stagnation detection
  - Cross-task integration check after each batch
  - SharedFiles: overlap check for dependency analysis
  - Per-task retry tracking and escalation
  - Worktree parallelization if opted in via sudd.yaml
But:
  - Skip research phase (already done)
  - Use existing specs/design
  - Only run missing validations
```

---

## ESCALATION (v3.2 — floor-based)

```
The escalation ladder sets per-role FLOOR tiers. Never downgrades.
Retry 0-1: floor=low   (all agents use default tiers)
Retry 2-3: coder stays low, squad+code-reviewer floor=mid
Retry 4-5: default floor=mid, code-reviewer floor=top
Retry 6-7: floor=top   (all agents at top)
After 8:   STUCK → sudd/memory/stuck-history/{change-id}.md
```

---

## ERROR HANDLING

```
On any error:
  Dispatch(agent=blocker-detector):
    - Classify: RETRY | BLOCKED | STUCK
    - Root Cause: LOGIC_ERROR | SPEC_ERROR | DESIGN_FLAW | CONTEXT_DRIFT | EXTERNAL_DEPENDENCY
    - Route To: coder | architect | context-manager | BLOCKED

  Route based on "Route To" field:
    "coder":           increment retry, escalate tier per ladder, restart from 3a
    "architect":       invoke architect to revise specs/design, restart with retry reset to 0
    "context-manager": re-read vision + specs, clear stale context, restart from 3a
    "BLOCKED":         log to sudd/results/{change-id}_BLOCKED.md, skip task

  STUCK: log to sudd/memory/stuck-history/, move on
```

---

## SESSION END

```
Update: sudd/state.json
  - last_run = now
  - stats updated

Output:
  ═══════════════════════════════════════
  SUDD SESSION COMPLETE
  ═══════════════════════════════════════
  Mode: green | brown
  Tasks completed: N
  Tasks stuck: N
  Tasks blocked: N
  Lessons learned: M new
  ═══════════════════════════════════════
```

---

## GUARDRAILS

1. **Never ask user** unless scope is unclear or major decision needed
2. **Never skip validation squad** — every task gets contract → wiring → integration → micro-persona check
3. **Never skip persona gate** — mandatory for completion
4. **Always escalate on retry** — same tier won't magically succeed (per-task retry count)
5. **Always write files to disk** — no in-memory only
6. **Always read actual files for validation** — not summaries
7. **Budget conscious** — use free models when possible, select model tier by task complexity
8. **Sequential by default** — worktree parallelization is opt-in via `sudd.yaml` → `parallelization.mode: worktree`. Default is sequential: reliable, no merge risk
9. **Spec compliance before code quality** — always run contract-verifier before peer-reviewer (fix what's wrong before polishing)
10. **SharedFiles must be declared** — architect must list lock files, configs, routers in `SharedFiles:` per task. Tasks sharing any `SharedFiles:` entry are DEPENDENT
11. **Worktree mode only**: cleanup is mandatory — always remove worktrees after merge or conflict. Rebase before merge. Revert on post-merge validation failure
12. **Per-task validation before proceeding** — validation squad (contract → wiring → integration → micro-persona) runs after every task. No task is "done" until PASS (100/100).
13. **Context window management** — validation squad agents are lightweight (narrow scope). After each task, compress validation history to one line in state.json. If context window reaches 80% capacity, save state and continue in fresh session.
14. **Never skip persona early validation** (Step 3b) — weak personas produce weak gates. Validate BEFORE design.
15. **Never skip architecture review** (Step 4b) — catch design flaws before burning retries on bad architecture.
16. **Never skip design-gate** (Step 4c) — if the design doesn't serve the personas, coding is wasted effort.
