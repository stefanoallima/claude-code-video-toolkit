---
name: sudd:discover
description: Run discovery pipeline — explore codebase, find gaps, generate proposals
phase: inception
macro: false
---

Discovery pipeline. Compares code reality against SUDD docs to find gaps and
generate change proposals. Smart enough to skip when recent and nothing changed.

## STALENESS CHECK (run first, before any agent dispatch)

Before running discovery, check if it's actually needed:

```
Read sudd/state.json → discovery section:
  last_run_at:          timestamp of last discovery
  changes_since_last:   count of changes archived since last discovery
  last_git_sha:         git SHA at last discovery

Read sudd/sudd.yaml → discovery section:
  run_every_n_changes:    3     (default)
  min_interval_minutes:   5     (default)
  auto_on_empty_queue:    true  (default)
  auto_on_port:           true  (default)

SKIP discovery if ALL of:
  1. last_run_at exists AND (now - last_run_at) < min_interval_minutes
  2. changes_since_last < run_every_n_changes
  3. last_git_sha == current HEAD (no code changes)

FORCE discovery if ANY of:
  - User explicitly invoked /sudd:discover
  - Called with --force flag
  - No previous discovery (last_run_at is empty)
  - Called from port.md (auto_on_port context)

If skipped:
  Output: "Discovery skipped — last ran {N}m ago, {M} changes since. Next run after {K} more changes or code push."
  RETURN (do not run agents)
```

## EXECUTION

### STEP 1: Codebase Exploration

```
Dispatch(agent=codebase-explorer, tier=low):
  Input: entire project source tree
  Output: sudd/codebase-manifest.json

If codebase-manifest.json already exists AND git SHA matches:
  Skip re-generation. Use cached manifest.
  Log: "Using cached manifest (SHA: {sha})"
```

### STEP 2: Alignment Review

```
Dispatch(agent=alignment-reviewer, tier=mid):
  Input: sudd/codebase-manifest.json + vision.md + personas/ + changes/
  Output: sudd/alignment-report.md

If alignment-report.md shows 0 gaps:
  Log: "No gaps found. Code and docs are aligned."
  Update state.json → discovery section
  RETURN
```

### STEP 3: Proposal Generation

```
Read sudd/alignment-report.md
Count actionable gaps (Critical + Important only — skip Minor for now)

If 0 actionable gaps:
  Log: "Only minor gaps found. No proposals generated."
  Update state.json → discovery section
  RETURN

Dispatch(agent=task-discoverer, tier=top):
  Input: alignment-report.md + personas/ + vision.md
  Enhanced instruction: "Generate proposals from the alignment report gaps.
    Each GAP entry in the report should become a proposal if:
    - It has Priority 1 or 2
    - It serves a persona need
    - It's not already covered by an active change
    Use the GAP-ID as reference in the proposal's ## Why section.
    Prefer S-size. Split L-size gaps into multiple S/M proposals."
  Output: sudd/changes/active/discovered_*/ directories

Log: "Discovery complete. {N} proposals generated from {M} gaps."
```

### STEP 4: Update State

**ALWAYS update state.** The Go binary may also update these fields after this
subprocess exits, but that only happens when invoked via `sudd auto`. When
invoked from `/sudd:run green` or standalone, this is the ONLY update path.
Writing these fields is idempotent — double-writing is safe.

```
Read sudd/state.json
Update discovery section:
  last_run_at: now (ISO-8601)
  changes_since_last: 0
  last_git_sha: output of `git rev-parse HEAD`
Write sudd/state.json (preserve all other fields)
```

## CONFIGURATION

In `sudd/sudd.yaml`:

```yaml
discovery:
  run_every_n_changes: 3        # run after every N archived changes
  min_interval_minutes: 5       # minimum minutes between discovery runs
  auto_on_empty_queue: true     # auto-trigger when sudd:auto queue is empty
  auto_on_port: true            # auto-trigger after sudd:port completes
```

## INTEGRATION POINTS

This command is called from three places:

1. **`/sudd:auto`** — when queue is empty and `discovery.auto_on_empty_queue` is true
2. **`/sudd:port`** — after port completes and `discovery.auto_on_port` is true
3. **`/sudd:run green`** — before creating the first change (replaces the single-change Step 2)
4. **Manual** — user runs `/sudd:discover` directly

## INCREMENTAL CHANGES COUNTER

The `changes_since_last` counter is incremented by `/sudd:done` (or the done-phase logic
inside `/sudd:run`). Every time a change is archived (DONE or STUCK), the counter goes up by 1.
When discovery runs, the counter resets to 0.

This means discovery triggers based on work completed, not time elapsed.
Example with `run_every_n_changes: 3`:
- Change 1 archived → counter = 1 → no discovery
- Change 2 archived → counter = 2 → no discovery
- Change 3 archived → counter = 3 → discovery triggers → counter resets to 0

## OUTPUT

```
═══════════════════════════════════════
  SUDD DISCOVERY
═══════════════════════════════════════
  Manifest:  {cached|generated} (SHA: {sha})
  Gaps:      {N} critical, {M} important, {K} minor
  Proposals: {P} generated
  Skipped:   {S} (already active/done)
═══════════════════════════════════════
```
