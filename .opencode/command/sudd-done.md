---
name: sudd-done
description: Archive completed (or stuck) change
phase: complete
micro: true
prereq: sudd:gate (passed or stuck)
creates: archive entry, lessons learned
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

## STEP 2a: EXTRACT LESSONS

```
Dispatch(agent=learning-engine, mode=1):

Read: sudd/changes/active/{id}/log.md
Read: All feedback from retries

Extract:
1. What worked well?
2. What didn't work?
3. Patterns to remember
4. Patterns to avoid

Write: sudd/memory/lessons.md
  Use the SUCCESS / FAILURE / STUCK template from learning-engine.md Mode 1.
  Tags MUST be specific (e.g., "go-testing", "cross-file-consistency") not generic ("code", "testing").
```

Verify: the new lesson entry exists at the bottom of `memory/lessons.md`.
If NOT present: STOP. Re-run this step. Lessons are required before archiving.

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

## STEP 3: ARCHIVE

### If DONE
```bash
mv sudd/changes/active/{id} sudd/changes/archive/{id}_DONE
```

Create summary: `sudd/changes/archive/{id}_DONE/SUMMARY.md`
```markdown
# Archive: {change-id}

## Outcome: DONE

## Summary
{1-2 sentences}

## Consumers Validated
- Consumer 1: score
- Consumer 2: score

## Files Changed
- path/to/file.py — description

## Lessons Learned
- Lesson 1
- Lesson 2

## Completed: {timestamp}
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
