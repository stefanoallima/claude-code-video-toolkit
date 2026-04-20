---
name: "sudd-done"
description: "Archive completed or stuck change. Use when implementation is complete."
license: MIT
metadata:
  author: sudd
  version: "3.8.25"
---

Archive the change. Update memory. Clean up.

**Input**:
- `/sudd:done` — archive active change
- `/sudd:done {change-id}` — archive specific change

---

## ORCHESTRATOR CHECK

## PHASE GUARD
Read sudd/state.json
If gate_passed != true AND retry_count < 8: STOP. "Run /sudd:gate first."

```bash
cat sudd/state.json
```

Check if gate passed or stuck:
- Passed: archive as DONE
- Stuck (retry >= 8): archive as STUCK
- Neither: "Gate not passed. Run `/sudd:gate` first."

---

## STEP 1: DETERMINE OUTCOME

Read final state:
- `sudd/changes/active/{id}/log.md` — execution history
- `sudd/state.json` — retry count

Outcome:
- `DONE` — gate passed, all consumers satisfied
- `STUCK` — max retries, couldn't pass gate
- `BLOCKED` — external dependency missing

---

## STEP 2a: EXTRACT LESSONS (MANDATORY — DO NOT SKIP)

This step runs EVERY time. Silent-skipping it is the bug this assertion
exists to prevent — five 2026-04-19 DONEs shipped without lessons because
Step 2a used to be prose-only. It is no longer.

```
Dispatch(agent=learning-engine, mode=1):

change-id: {id}               ← pass the active change-id explicitly so
                                 the lesson heading includes it verbatim

Read: sudd/changes/active/{id}/log.md
Read: All feedback from retries

Extract:
1. What worked well?
2. What didn't work?
3. Patterns to remember
4. Patterns to avoid

Write: sudd/memory/lessons.md
  Use the SUCCESS / FAILURE / STUCK template from learning-engine.md Mode 1.
  The heading line MUST include the literal `{change-id}` string so the
  pre-archive assertion below can grep for it.
  Tags MUST be specific (e.g., "go-testing", "cross-file-consistency") not generic ("code", "testing").
```

### Pre-Archive Assertion (MANDATORY — DO NOT SKIP)

Lesson recording is enforced by the Go binary after the subprocess exits
via `auto.RunPreArchiveChecks` (see `sudd-go/internal/auto/checks.go`),
which invokes `auto.LessonRecorded` from `learning.go` as a registered
check. The bash assertion below runs as non-authoritative fast-feedback
inside the subprocess — the Go binary is canonical; skipping the bash
block is harmless (the Go check still runs post-exit and downgrades a
DONE outcome to STUCK on failure). Skipping the Go check is impossible
unless `SUDD_PRE_ARCHIVE_CHECKS=off` is set in the environment.

AFTER dispatching learning-engine and BEFORE proceeding to Step 2b, the
orchestrator MUST run this shell assertion via the Bash tool:

```bash
count=$(grep -c "{change-id}" sudd/memory/lessons.md 2>/dev/null || echo 0)
if [ "$count" -lt 1 ]; then
  echo "✗ Learning pipeline failure: no lesson entry written for {change-id}"
  echo "   Re-dispatching learning-engine Mode 1 (attempt $attempt of 2)..."
  # loop: re-dispatch Step 2a, re-run grep. Max 2 retries.
else
  echo "✓ Lesson recorded for {change-id} (count=$count)"
fi
```

If the count is still `0` after 2 re-dispatches, STOP the archive:
- Do NOT run `mv sudd/changes/active/{id} sudd/changes/archive/{id}_DONE`.
- Instead, set state.json to `retry_count >= 8` and archive as STUCK with
  `STUCK.md` reason = `learning-pipeline-failure`.
- Flag this in log.md for human investigation — learning-engine produced
  no output and the problem is not recoverable by retry alone.

The canonical Go form of this assertion is
`auto.LessonRecorded(projectDir, changeID)` in
`sudd-go/internal/auto/learning.go`. The Go test enforces the rule
cannot be quietly removed.

---

## STEP 2b: PATTERN PROMOTION (MANDATORY — DO NOT SKIP)

This step runs EVERY time, even if you think there are no new patterns.

```
Dispatch(agent=learning-engine, mode=3):

1. Read ALL entries in sudd/memory/lessons.md
2. For each entry, extract the **Tags:** line → split into individual tags
3. Build a frequency table: for each tag, list which change-ids use it
4. For each tag that appears in 3+ DIFFERENT change-ids:
   a. Check sudd/memory/patterns.md — does a pattern with this tag already exist?
   b. If NO:  Create a new pattern entry (format from learning-engine.md Mode 3)
   c. If YES: Update the occurrence count and add new evidence
5. Also check tag PAIRS (e.g., "framework" + "agents") — same 3+ threshold
6. Log: "Pattern scan: {N} tags checked, {M} new patterns promoted, {K} patterns updated"
```

Also write promoted patterns to global learning (if enabled):
```
If ~/.sudd/learning/ exists:
  Append new patterns to ~/.sudd/learning/patterns.md
  (Do NOT overwrite — append only, with repo identifier prefix)
```

Verify: `memory/patterns.md` was updated OR the log shows "0 new patterns promoted" with the scan count.
If the scan count is 0: STOP. You skipped the scan. Re-read lessons.md and actually count tags.

---

## STEP 2c: INDEX SESSION IN MEMPALACE (v3.6 — optional)

This step only runs when `sudd.yaml → mempalace.enabled: true` AND `mempalace_add_drawer` MCP tool is available.
If MemPalace is not configured, skip to Step 3.

```
Read: sudd/changes/active/{id}/log.md (FULL content — not just lessons)

mempalace_add_drawer(
  content: {full log.md content},
  wing: {project-name from sudd.yaml or cwd basename},
  room: "sessions",
  tags: "{change-id}, {outcome: DONE|STUCK}, {date}"
)

Log: "Session indexed in mempalace: {change-id} ({N} chars)"
```

**Why this matters**: The lesson extracted in Step 2a is a 2-3 line summary. The full log.md contains:
- Every agent dispatch and its result
- All retry feedback and accumulated errors
- Exact file changes and commit SHAs
- Validation squad scores and critiques
- Timing and cost data

This rich context is searchable via `mempalace_search(room="sessions")` and surfaces during Mode 2 injection when a similar task is being attempted in the future.

Also index the lesson and any new patterns in MemPalace:
```
If Step 2a wrote a new lesson:
  mempalace_add_drawer(content: {lesson text}, wing: {project}, room: "lessons", tags: {tags})

If Step 2b promoted new patterns:
  For each new pattern:
    mempalace_add_drawer(content: {pattern text}, wing: {project}, room: "patterns", tags: {pattern tags})
```

---

## STEP 2d: ENFORCE TASKS.MD CHECKBOX CLOSURE (MANDATORY — DO NOT SKIP)

Tasks-closure is enforced by the Go binary via `auto.RunPreArchiveChecks`
→ `auto.TasksAllChecked` in `sudd-go/internal/auto/tasks.go` — registered
alongside `LessonRecorded` and `SummaryHasCanonicalHeadings`. The bash
`grep` block below remains as fast-feedback inside the subprocess; the
Go binary is canonical.

Only DONE archives are gated here. STUCK goes through regardless — a
partial-completion STUCK archive is expected to carry unchecked boxes.

```bash
if [ "{outcome}" = "DONE" ]; then
  unchecked=$(grep -c '^- \[ \]' sudd/changes/active/{id}/tasks.md 2>/dev/null || echo 0)
  if [ "$unchecked" -gt 0 ]; then
    echo "✗ Tasks-closure failure: $unchecked unchecked box(es) in tasks.md"
    echo "   Unchecked lines:"
    grep -n '^- \[ \]' sudd/changes/active/{id}/tasks.md
    echo "   The orchestrator must either:"
    echo "     (a) Flip these boxes to [x] via the Edit tool (work actually done), OR"
    echo "     (b) Archive as STUCK (work actually incomplete)."
    echo "   Do NOT run 'mv ... archive/{id}_DONE' while unchecked boxes remain."
    exit 1
  fi
  echo "✓ Tasks.md closed: 0 unchecked boxes"
fi
```

The canonical Go form of this assertion is
`auto.TasksAllChecked(projectDir, changeID)` in
`sudd-go/internal/auto/tasks.go`. The Go test
`TestDoneMdContainsTasksAssertion` enforces that this Step 2d block
cannot be silently removed — any future edit that drops the `STEP 2d`
marker or the `- [ ]` grep pattern fails CI.

**Why this exists**: `brown_v3816-cross-repo-hygiene_01_DONE/tasks.md`
shipped with 22 unchecked boxes despite DONE gate score 98/100. The
persona's success criterion "I can see exactly what happened" fails
when the DONE archive contradicts itself. Step 2d is the mechanical
gate that makes that class of regression impossible.

---

## STEP 2e: ENFORCE SUMMARY.md CANONICAL HEADINGS (MANDATORY — DO NOT SKIP)

SUMMARY.md canonical-heading enforcement is delivered by the Go binary
via `auto.RunPreArchiveChecks` → `auto.SummaryHasCanonicalHeadings` in
`sudd-go/internal/auto/summary.go`. The check runs against
`active/{id}/SUMMARY.md` BEFORE the `mv` (the pre-archive registry sees
the file in active first, then falls back to `archive/{id}_DONE/`). The
bash block below is non-authoritative fast-feedback.

Only DONE archives are gated here. STUCK archives use STUCK.md, which has
its own schema.

BEFORE running `mv sudd/changes/active/{id} sudd/changes/archive/{id}_DONE`,
the orchestrator MUST emit SUMMARY.md using the canonical template (see
Step 3 "### If DONE") and verify it contains all four canonical `##`
headings. The file is still in `active/{id}/` at this point — the
assertion runs pre-move, against the just-emitted file.

```bash
summary=sudd/changes/active/{id}/SUMMARY.md
if [ ! -f "$summary" ]; then
  echo "✗ SUMMARY.md not yet written; emit it from the Step 3 template first"
  exit 1
fi
missing=""
grep -q '^## What Changed' "$summary" || missing="$missing ## What Changed"
grep -q '^## Why' "$summary"          || missing="$missing ## Why"
grep -qE '^## Validation( Results)?' "$summary" || missing="$missing ## Validation"
grep -qE '^## Lessons( Learned)?' "$summary"    || missing="$missing ## Lessons"
if [ -n "$missing" ]; then
  echo "✗ SUMMARY.md missing canonical headings:$missing"
  echo "   Re-emit from the canonical template in Step 3."
  exit 1
fi
echo "✓ SUMMARY.md has all canonical headings"
```

If the assertion fails: re-emit SUMMARY.md from the canonical template.
Do NOT silently `mv` an archive whose SUMMARY.md is non-canonical.

The canonical Go form of this assertion is
`auto.SummaryHasCanonicalHeadings(body)` in
`sudd-go/internal/auto/summary.go`. The Go test
`TestDoneMdContainsSummaryAssertion` enforces that this Step 2e block
cannot be silently removed — any future edit that drops the `STEP 2e`
marker or the canonical heading literals fails CI. The companion live-repo
test `TestAllArchivesHaveCanonicalHeadings` enforces that every
`archive/*_DONE/SUMMARY.md` on the current repo is canonical at all times.

**Why this exists**: Audit 2026-04-19 found 0 of 19 archived DONEs matched
the rubric's canonical headings — every change invented its own structure
(`## What shipped / Files touched / Verification` vs `## Summary / Consumers
Validated / Files Changed / Lessons Learned`, etc.). Content was fine; the
shape drifted, which breaks any grep-based downstream consumer
(stakeholder dashboard, cross-repo analyzer, audit tooling). Step 2e is
the mechanical gate that makes that class of drift impossible.

---

## STEP 3: ARCHIVE

### If DONE

**Emit SUMMARY.md FIRST (into `active/{id}/`, pre-move), then run Step 2e
assertion, then `mv` to archive.**

Create `sudd/changes/active/{id}/SUMMARY.md` using the canonical template
below. The four `##` headings (What Changed, Why, Validation, Lessons) are
mandatory — Step 2e blocks the archive if any are missing. Supplementary
sections (`## Files Changed`, `## Cost Summary`, etc.) remain permitted.

```markdown
# Archive: {change-id}

## Outcome: DONE

## What Changed

{1-2 sentences: what actually shipped. Shape-level, not exhaustive file list.}

## Why

{Motivation from proposal.md. Why this change existed. Who it serves.}

## Validation

{How this was verified. Tests run, consumers/personas validated with
scores, browser reports if UI. Evidence of gate PASS.}

## Lessons

{Key lessons — mirrors the lesson recorded in memory/lessons.md for this
change. 1-3 bullet points.}

## Files Changed

- `path/to/file.ext` — description

## Completed: {YYYY-MM-DD}
```

After emitting, run the Step 2e grep assertion. If it passes, proceed:

```bash
mv sudd/changes/active/{id} sudd/changes/archive/{id}_DONE
```

### If STUCK
```bash
mv sudd/changes/active/{id} sudd/changes/archive/{id}_STUCK
```

Create: `sudd/changes/archive/{id}_STUCK/STUCK.md`
```markdown
# Stuck: {change-id}

## Why Stuck
{reason from final feedback}

## All Feedback History
{accumulated feedback from all retries}

## What Was Tried
- Attempt 1: ...
- Attempt 2: ...

## Suggested Human Actions
- Action 1
- Action 2

## Files Partially Complete
- path/to/file.py — X% complete
```

Copy to: `sudd/memory/stuck-history/{id}.md`

### Rollback Generation (STUCK changes only)

Read `## Files Modified` from log.md and generate a rollback script.

Add a "## Rollback Command" section to STUCK.md with the following format:

    ## Rollback Command
    # Rollback for {change-id} (STUCK at task {last_task})
    git checkout main -- {file1} {file2} {file3}

Where {file1}, {file2}, etc. are every file listed under "## Files Modified"
in log.md.

Include this rollback section in the STUCK.md archive file so humans can
quickly undo partial work.

### Cost Summary (ALL changes — DONE or STUCK)

**Phase transition: complete → inception — valid**

Read `## Cost Log` from log.md (if present) and display a summary:

```
Cost Summary:
  Total retries: {retry_count}
  Escalation tier reached: {tier}
  Tasks completed: {N}
  Tasks remaining: {M} (STUCK only)
```

Include this in the OUTPUT section and in the archive SUMMARY.md / STUCK.md.

### Rollback Instructions
1. List all files modified during this change (from log.md)
2. Include command: `git checkout main -- {list of modified files}`
3. Note: Branch sudd/{change-id} is preserved for human review

---

## STEP 4: UPDATE STATE

Update `sudd/state.json`:
```json
{
  "active_change": null,
  "phase": "inception",
  "retry_count": 0,
  "stats": {
    "tasks_completed": N+1 or N,
    "tasks_stuck": M or M+1
  },
  "tests_passed": false,
  "gate_score": 0,
  "gate_passed": false,
  "last_command": "sudd:done"
}
```

### Discovery + Audit Counter Increment (v3.4)

After updating state.json, increment both change counters:

```
Read state.json → discovery.changes_since_last (default 0 if missing)
Write state.json → discovery.changes_since_last = previous + 1

Read state.json → audit.changes_since_last_audit (default 0 if missing)
Write state.json → audit.changes_since_last_audit = previous + 1
```

These feed the staleness checks:
- `/sudd:discover` triggers after `discovery.run_every_n_changes` (default 3)
- `/sudd:audit` triggers after `audit.auto_after_n_changes` (default 5)

**NOTE**: When running inside `sudd auto`, the Go binary handles these
increments automatically. Only update manually when running `/sudd:done`
standalone outside of the auto pipeline.

---

## STEP 5: GIT CLEANUP

```bash
git add sudd/
git commit -m "chore: archive {change-id} as {DONE|STUCK}"
git checkout main
git merge sudd/{change-id}
```

---

## OUTPUT

### DONE
```
Archived: {change-id} ✓

  Outcome: DONE
  Consumers: all validated (min: 98/100 EXEMPLARY)
  Lessons: 3 captured
  
  sudd/changes/archive/{id}_DONE/

Session stats updated.
Ready for next change. Run /sudd:new
```

### STUCK
```
Archived: {change-id} ⚠

  Outcome: STUCK
  Retries: 8
  Reason: {final blocker}
  
  Stuck history saved to: sudd/memory/stuck-history/
  
  Human action needed. See archive for details.
```

---

## GUARDRAILS

- Always extract lessons before archiving
- Preserve full history for stuck changes
- Update stats accurately
- Clean git state after archive
- Clear active_change in state
