---
name: sudd-auto
description: Fully autonomous mode — process all queued changes
phase: all
macro: true
---

Fully autonomous mode. Processes all proposed changes in sequence,
each in a fresh CLI session.

## EXECUTION

When this command is invoked, run the following via the Bash tool:

```bash
sudd auto
```

If `sudd` is not on PATH, try:

```bash
sudd-go/bin/sudd auto
```

If the binary doesn't exist, build it first:

```bash
cd sudd-go && make build && cd .. && sudd-go/bin/sudd auto
```

The binary handles everything from here — queue building, subprocess
launching, budget enforcement, crash recovery, and morning report.
This CLI session can end after launching the binary.

## CONFIGURATION

Set in sudd.yaml under `auto:`:

    auto:
      max_hours: 8                    # session time limit
      max_changes: 5                  # max changes per session
      per_change_timeout_hours: 4     # kill runaway changes
      stop_on_stuck: false            # continue after STUCK changes
      priority_order: "oldest_first"  # oldest_first | newest_first
      vision_last: true               # vision.md runs last
      cli_override: ""                # auto-detect from tiers.mid.cli
      cli_flags: "--max-turns 200"    # flags for CLI subprocess
      max_report_days: 30             # auto-delete reports older than this

## CLI FLAGS NOTE

The default `cli_flags: "--max-turns 200"` works with `claude`. If using `opencode`
or another CLI, verify the flags are compatible and update `auto.cli_flags` accordingly.
Set to empty string `""` to pass no extra flags.

## WHAT IT DOES

1. Cleans old reports (older than max_report_days)
2. Scans changes/active/ for proposals with status: proposed
3. Resumes any in-progress change first
4. Launches a fresh CLI session per change (claude or opencode)
5. Each change follows /sudd:run workflow: plan -> apply -> test -> gate -> done
6. After each change: increments discovery.changes_since_last counter
7. After each change: checks time/count budgets
8. **After green:vision completes**: re-scans queue (discovery may have created new proposals)
9. **On empty queue**: runs discovery pipeline if auto_on_empty_queue is enabled (v3.4)
   - Launches CLI subprocess with "/sudd:discover"
   - Re-scans queue after discovery completes
   - If new proposals found: continues processing
   - If still empty: truly done
10. Writes morning report to sudd/auto-reports/{date}/summary.md
11. Crash-recoverable: restart `sudd auto` to resume from where it stopped

## DISCOVERY INTEGRATION (v3.4)

The auto loop triggers discovery in two scenarios:

### Scenario 1: After green:vision
When the green:vision entry completes, /sudd:run's Step 2 may have invoked
/sudd:discover internally. The auto binary re-scans the queue to pick up
any proposals created during that subprocess.

### Scenario 2: Empty queue
When the queue is empty (all proposals processed), the binary checks:
- Is `discovery.auto_on_empty_queue` true in sudd.yaml?
- Does the staleness check pass? (changes_since_last >= run_every_n_changes
  OR last_git_sha differs from current HEAD)

If both: launches a discovery subprocess, then re-scans once. If still
empty after discovery, the session ends normally.

### Changes Counter
Every time a change is archived (DONE or STUCK), the binary increments
`state.json → discovery.changes_since_last`. This feeds the staleness
check so discovery runs periodically based on work completed.
