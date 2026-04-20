---
name: sudd:apply
description: Implement tasks from the task list
phase: build
micro: true
prereq: sudd:plan (specs.md, design.md, tasks.md)
creates: code files
---

Implement tasks from the change’s task list.

**Input**:
- `/sudd:apply` — implement next pending tasks
- `/sudd:apply {task-id}` — implement specific task
- `/sudd:apply all` — implement all pending tasks

---

Agent invocation follows `sudd/standards.md` → Agent Invocation.

---

## ORCHESTRATOR CHECK

## PHASE GUARD
<!-- Phase guard: requires phase >= "build" -->
If phase < "build": STOP. "Run /sudd:plan first."
If specs.md does not exist: STOP. "Run /sudd:plan first — specs.md is required."

```bash
cat sudd/state.json
```

If phase < "build":
- "Planning not complete. Run `/sudd:plan` first."
- Or auto-run if autonomous

If no active change:
- Find available changes
- Auto-select or ask

---

## STEP 1: READ CONTEXT + VALIDATE STATE

Read state.json and validate per `sudd/standards.md` → State Validation.

Read:
- `sudd/sudd.yaml` (agent tiers, cost_mode)
- `sudd/changes/active/{id}/proposal.md`
- `sudd/changes/active/{id}/specs.md`
- `sudd/changes/active/{id}/design.md`
- `sudd/changes/active/{id}/tasks.md`
- `sudd/memory/lessons.md`

---

## STEP 1b: LESSON INJECTION (MANDATORY)

Read `sudd/memory/lessons.md`. For current task, extract tags from:
- Task technology (from design.md file extensions / frameworks)
- Task domain (from proposal.md / specs.md)
- Prior failure patterns (from log.md if retry)

Match lessons by tag overlap. Select top-3 by: tag match count > confidence > recency.

If matches found, include in ALL agent prompts for this task:
```
## Lessons (DO NOT repeat these mistakes)
1. {lesson} (from: {change-id}, confidence: {level})
2. {lesson}
3. {lesson}
```

Log: "Injected {N} lessons for tags: {tags}"
If no matches: Log: "No matching lessons for tags: {tags}"

---

## STEP 1c: DISPATCH MODE (v3.1)

Read `sudd/sudd.yaml` → agents → each agent's `execution` field.
Read `sudd/sudd.yaml` → `model_mapping` for tier-to-model translation.

For agents with `execution: subagent`:
  Use `Subagent(agent=name)` dispatch — isolated context, structured return.
  The orchestrator constructs the context bundle and receives only the return schema.
  The subagent’s internal reasoning NEVER enters the orchestrator’s context.

For agents with `execution: inline`:
  Use `Task(agent=name)` dispatch — runs in orchestrator’s context (unchanged from v3.0).

Model selection for subagents:
  model = sudd.yaml.model_mapping[agent.tier]
  Override by escalation ladder if retry_count > 0

---

## STEP 2: SHOW PROGRESS

```
Tasks: {change-id}

  ✓ T1: Setup database schema
  ✓ T2: Create model classes
  ○ T3: Implement API endpoints
  ○ T4: Add validation
  ○ T5: Write tests

Progress: 2/5 complete
```


## STEP 2.5: CANARY VALIDATION (v3.1)

If this is the first task in the change (no tasks completed yet):
  Run the full pipeline on T1 as a canary:
    Subagent(coder) → Subagent(qa) → parallel(Subagent(cv), Subagent(wc)) → Subagent(ir) → [Subagent(ux-r)] → Subagent(mpv)

  If T1 PASSES cleanly (all rubric criteria met, HIGH confidence):
    → Proceed with remaining tasks normally

  If T1 FAILS on TASK-SPECIFIC issue (bug in T1's code):
    → Normal retry for T1, then proceed

  If T1 FAILS on SYSTEMIC issue:
    Systemic indicators:
    - Multiple rubric categories fail simultaneously
    - Rubric criteria reference specs that are ambiguous/wrong
    - Micro-persona contract doesn't match actual codebase patterns
    - Wiring fails because design assumed wrong file structure
    → STOP. Fix systemic root cause FIRST:
      - Spec issue → architect revises specs
      - Persona issue → re-run micro-persona-generator
      - Design issue → architect revises design
    → THEN proceed with remaining tasks
---

## RETRY PROTOCOL (if retry_count > 0)

### For retry 1-2: Full Feedback
1. Read `## Accumulated Feedback` from log.md
2. Read latest critique dispositions from log.md
3. Lessons already injected by STEP 1b
4. Include in coder's prompt:

```
RETRY BRIEFING (attempt {retry_count} of 8):
  Previous level: {gate_level}
  Tier: {current tier from sudd.yaml escalation ladder}
  Failures:
    {list from accumulated feedback}
  Key lessons:
    {top-3 from STEP 1b}

  FIX THESE SPECIFIC ISSUES. Do not rewrite from scratch.
```

### For retry 3+: Compressed Feedback (MANDATORY)
1. Read ALL `## Accumulated Feedback` entries from log.md
2. Compress into:
```
## Compressed Feedback (retry {N})
### STILL OPEN (fix these):
1. {issue} — first seen retry {N}, still failing
### RESOLVED (don't regress):
1. {issue} — fixed in retry {N}
### PATTERN (recurring blocker):
{the issue that keeps coming back}
```
3. Include ONLY compressed version in coder prompt (discard raw entries)
4. Context budget: task + design + compressed feedback + lessons ≤ 6000 tokens
5. Log: "Feedback compressed: {N} raw entries → {M} open issues"

---

## STEP 3: IMPLEMENT TASKS

For each pending task (or specified task):

### 3-pre. Task Ordering & Dispatch

When `/sudd:apply all` or multiple tasks are pending:

1. **Analyze dependencies**: Read each task's `Dependencies:`, `Files:`, and `SharedFiles:` fields
2. **Order tasks**:
   - Tasks are INDEPENDENT if: neither depends on the other AND their `Files:` AND `SharedFiles:` lists don't overlap
   - Group independent tasks into batches; dependent tasks go into later batches
   - Within each batch, execute tasks **sequentially** (default) or in parallel (opt-in)
3. **Default: Sequential execution** (one task at a time in main workspace):
   - Run tasks in dependency order within each batch
   - No worktree overhead, no merge risk, no implicit dependency issues
   - This is the default and recommended mode
4. **Opt-in: Worktree parallelization** (if `sudd.yaml` → `parallelization.mode: worktree`):
   - Only when batch size > 1 AND all conditions met (see `sudd/agents/context-manager.md` → Worktree Management)
   - Create worktree per task, dispatch in parallel, merge back sequentially
   - IMPORTANT: validation squad runs INSIDE the worktree before merge
   - Before each merge: rebase worktree branch against current base to reduce conflicts
   - On merge conflict: abort, re-run that task sequentially in main workspace
   - On post-merge validation failure: `git revert` the merge commit, re-run task sequentially
   - Cleanup all worktrees after merge or conflict
   - **Skip worktrees even in worktree mode** if: only 1 task in batch, all Effort: S, not in a git repo, or `git worktree add` fails mid-batch

5. **Model tier selection** (matches run.md Step 5b):
   - `Effort: S` AND ≤2 files → free tier (opencode/MiniMax)
   - `Effort: M` OR ≤4 files → standard tier (sonnet)
   - `Effort: L` OR >4 files → capable tier (opus)
   - Retry escalation (applies to ALL agents in the task):
     - retry 0-1: free tier for all
     - retry 2-3: free for coder, sonnet for validation agents only
     - retry 4-5: sonnet for all
     - retry 6-7: opus for all
     - retry 8+: STUCK

For single task (`/sudd:apply {task-id}`): always run in main workspace.

### 3-pre-a. Idempotency Check
For each task about to execute:
1. Read tasks.md — is this task marked `[x]`?
2. If `[x]`: check git log for commit message containing this task ID
3. If both `[x]` AND commit exists → **Skip.** Log: "Task {id} already completed (commit: {sha})"
4. If `[x]` but NO commit → WARNING: "Task marked complete but no commit found. Re-running."

### 3a. Load Micro-Persona (v3.0)
```
Read: sudd/changes/active/{id}/tasks/{task-id}/micro-persona.md

If micro-persona missing:
  → Run micro-persona-generator for this task
  → Log: "Generated micro-persona for {task-id} on-demand"
```

### 3b. Task(agent=qa) — TDD
```
Read: agents/qa.md

For NEW tasks (retry_count == 0):
  QA writes tests BEFORE coder implements (TDD)
  → Step order for first attempt: 3a → 3b → 3c → 3d
  NOTE: This is an intentional change from v2 (where coder ran before QA).

For RETRIES (retry_count > 0):
  Coder fixes first, then tests re-run
  → Step order for retries: 3a → 3c → 3b → 3d
```

### 3c. Subagent(agent=coder) (v3.1)
```
Subagent(agent=coder, model={model_mapping[tier]}):
  Context:
    - Micro-persona (with verification rubric)
    - Task description from tasks.md
    - Design section from design.md
    - Specs for interfaces from specs.md
    - Lesson injection (top-3 from STEP 1b)
  Returns:
    - files_changed: [list of file paths]
    - commit_sha: string
    - self_review: string
    - micro_persona_refined: bool
    - confidence: HIGH/MEDIUM/LOW
```

### 3d. VALIDATION SQUAD (v3.1 — subagent dispatch)

**Dispatch pattern (v3.1 — parallel where safe):**

PARALLEL (independent — dispatch simultaneously):
  i.  Subagent(agent=contract-verifier)
  ii. Subagent(agent=wiring-checker)

WAIT for both to complete, then SEQUENTIAL:
  iii. Subagent(agent=integration-reviewer)  # needs cv + wc results
  iv.  [UI only] Subagent(agent=ux-reviewer)
  v.   Subagent(agent=micro-persona-validator) # needs all results

```
i.  Subagent(agent=contract-verifier, model={model_mapping[tier]}):
    Context: micro-persona contract + specs.md contracts + code output
    Returns: {verdict, contracts_checked, violations, rubric_contract_results, confidence}

ii. Subagent(agent=wiring-checker, model={model_mapping[tier]}):
    Context: new/modified files from task, codebase import summary
    Returns: {verdict, files_checked, dead_ends, orphaned, deferred, confidence}

iii. Subagent(agent=integration-reviewer, model={model_mapping[tier]}, scope=task):
     Context: contract-verifier results + wiring-checker results + micro-persona + code
     Returns: {verdict, data_flows_checked, issues, fix_suggestions, confidence}

iv.  Subagent(agent=ux-reviewer, model={model_mapping[tier]}):  # UI tasks only
     Context: UI spec from design.md + code + micro-persona
     Returns: {verdict, patterns_checked, violations, suggestions, confidence}

v.   Subagent(agent=micro-persona-validator, model={model_mapping[tier]}):
     Context: micro-persona (full with rubric) + code + all squad results
     Returns: {verdict, score, rubric_results, feedback_for_coder, confidence}
```

**Any squad member FAIL → coder retries with that squad member's feedback.**

### 3d-bis. SELECTIVE RE-VALIDATION (v3.1 — on retries only)

When retry_count > 0, not all squad members need to re-run:

```
1. Diff the coder's changes (what files/functions changed?)
2. For each squad member:
   contract-verifier:      ALWAYS re-run (contract is usually what failed)
   wiring-checker:         SKIP if no new files/imports/routes changed
   integration-reviewer:   ALWAYS re-run (data flow may have changed)
   ux-reviewer:            SKIP if no UI files changed
   micro-persona-validator: ALWAYS re-run (final verdict)
3. Use cached results for skipped agents
4. Log: "Selective re-validation: skipped {agents}, used cached results"
```

### 3d-ter. CONFIDENCE HANDLING (v3.1)

After squad completes:
```
For each squad member's return:
  If verdict == PASS AND confidence == LOW:
    → Re-dispatch that agent with higher-tier model (sonnet or opus)
    → Use the higher-tier verdict
    → Log: "Low confidence override: {agent} re-dispatched as {model}"
  If verdict == PASS AND confidence == MEDIUM:
    → Proceed, log for gate awareness
```

### 3e. Task Retry Budget (v3.0)

```
If validation squad FAIL:
  retry_count++ for this task

  retry 1-3: Inject feedback → coder fixes → re-run squad
  retry 4:   Escalate to architect → revise task design → coder retries
  retry 5:   Architect + coder one more attempt
  retry 6+:  Mark task as blocked_failed
             Log: "Task {id} BLOCKED after {retries} attempts: {last failure reason}"
             Move to next independent task

Stagnation detection:
  If score delta < 5 across 2 consecutive retries → skip to architect escalation
```

### 3f. Mark Complete

Update `tasks.md`:
```markdown
- [x] T3: Implement API endpoints
  - Completed: {timestamp}
  - Validated: micro-persona PASS (100/100)
  - Files: api/endpoints.py, api/routes.py
```

Append to `log.md`:
```markdown
## {timestamp}
- Completed T3: Implement API endpoints
- Micro-persona: PASS (100/100) — consumer: {consumer name}
- Validation squad: contract ✓ wiring ✓ integration ✓
- Files created/modified: api/endpoints.py
- Retries: {N}
```

### 3f-bis. SQUAD DISAGREEMENT DETECTION (v3.1)

After marking task complete or failed, log squad verdicts with artifact names:

```markdown
## Squad Tracking: {task-id}
| Retry | Agent | Artifact Flagged | Reason |
|-------|-------|-----------------|--------|
| {N} | {agent} | {artifact} | {reason} |
```

Check for patterns:
1. Same artifact flagged by 2+ squad members for DIFFERENT reasons
   → Systemic issue → route to architect (not coder)
2. Same artifact fails 3+ retries across different squad members
   → BLOCKED → don't waste more retries, escalate immediately
3. Recurring field across tasks (T3, T5, T8 all fail on same issue)
   → Systemic → fix at design level, not per-task

### 3g. Track Files Modified
Append to `## Files Modified` in log.md:
```markdown
## Files Modified
- `{file_path}` — {task_id}: {description}
```

---

## STEP 4: CHECKPOINT

After each task or batch:
- Commit: `git add . && git commit -m "feat({change-id}): complete {task}"`
- Update state if phase change needed
  <!-- Phase transition: build → validate (valid, only when all tasks complete) -->

### Post-Batch Cross-Task Integration Check (v3.0)

After all tasks in a batch complete:
```
Task(agent=integration-reviewer, scope=change):
  Input: all micro-persona contracts, all task integration reports, SharedFiles conflicts
  Verdict: PASS / FAIL
  If FAIL: identify conflicting tasks, route to coder with both task contexts
```

---

## OUTPUT

```
Applied: {change-id}

  ✓ T3: Implement API endpoints
    Files: api/endpoints.py, api/routes.py
    Micro-persona: PASS (100/100)
    Squad: contract ✓ wiring ✓ integration ✓

  ✗ T5: Add payment webhooks
    Status: blocked_failed (5 retries)
    Last failure: wiring-checker — PaymentWebhook handler not registered in router

Progress: 4/5 complete, 1 blocked

If running autonomously (from /sudd:run): proceed directly to test phase. Do NOT stop.
If running standalone: Next → /sudd:test
```

---

## ERROR HANDLING (after validation squad failure)

```
Task(agent=blocker-detector): Classify error from squad feedback

Read blocker-detector output → "Route To" field:
  - "coder":           increment retry, escalate tier per ladder, restart from 3c
  - "architect":       invoke architect to revise design, restart from 3c with retry reset
  - "context-manager": re-read context, clear stale state, restart from 3c
  - "BLOCKED":         log blocker, mark task blocked_failed, skip to next task
```

Root-cause routing prevents wasting retries. SPEC_ERROR and DESIGN_FLAW go to architect, not coder with bigger model.

---

## SUBAGENT ERROR PROTOCOL (v3.1)

```
If subagent returns unstructured narrative (not the expected schema):
  -> Retry with: "Return ONLY this JSON schema: {schema}. No prose."
  -> Max 2 retries

If subagent times out:
  -> Retry with reduced context (drop lessons, keep essential)
  -> Max 1 retry

If subagent returns wrong schema (missing fields):
  -> Retry with: "Missing fields: {list}. Return complete schema."
  -> Max 1 retry

If 3 consecutive failures from same subagent:
  -> Escalate model tier (haiku -> sonnet -> opus)
  -> If already opus -> mark agent BLOCKED, orchestrator handles manually
```

---

## GUARDRAILS

- Always read design before implementing
- Follow specs for interfaces exactly
- Run full validation squad after each task (contract → wiring → integration → micro-persona)
- Peer-reviewer runs at gate level only (removed from per-task loop in v3.0)
- Commit after each task
- Update tasks.md checkboxes immediately
- Log progress to log.md
- Context window management: validation squad agents are lightweight (narrow scope). After each task, compress validation history to one line in state.json. If context window reaches 80% capacity, save state and continue in fresh session.
