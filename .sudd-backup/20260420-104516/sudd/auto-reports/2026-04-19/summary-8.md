# Auto Report — 2026-04-19

## Session Info

- **Start**: 20:55 CEST
- **End**: 21:59 CEST
- **Elapsed**: 1h 4m
- **CLI**: claude
- **Stop reason**: queue_empty

## Changes Processed

| # | Change | Outcome | Time | Tasks |
|---|--------|---------|------|-------|
| 1 | discovered_audit_claude-md-architecture-refresh_01 | STUCK | 5m 56s | 1/1 |
| 2 | discovered_audit_vision-known-open-work-stale_01 | STUCK | 3m 44s | 1/1 |
| 3 | discovered_audit_stuck-report-rendering-gaps_01 | DONE | 7m 42s | 16/16 |
| 4 | discovered_audit_done-dirty-outcome-tier_01 | STUCK | 16m 32s | 36/36 |
| 5 | discovered_audit_state-json-stats-rollup_01 | DONE | 7m 42s | 6/6 |

## Action Items

- discovered_audit_claude-md-architecture-refresh_01: # Stuck: discovered_audit_claude-md-architecture-refresh_01
- discovered_audit_vision-known-open-work-stale_01: # Stuck: discovered_audit_vision-known-open-work-stale_01
- discovered_audit_done-dirty-outcome-tier_01: # Stuck: discovered_audit_done-dirty-outcome-tier_01

## Quarantine

7 change(s) quarantined in `sudd/changes/stuck/`:

- **discovered_audit_done-dirty-outcome-tier_01**
- **discovered_audit_session-start-handoff-sync_01**
- **discovered_audit_browser-use-yaml-config_01**
- **discovered_audit_vision-known-open-work-stale_01**
- **discovered_audit_claude-md-architecture-refresh_01**
- **discovered_audit_state-json-session-fields_01**
- **discovered_audit_prearchive-checks-in-report_01**

Use `sudd auto --retry-stuck` to restore them to the active queue.

## Detected Failure Patterns

- `══════════════════════════�…` — appears in 5 of 7 recent stuck reports
- `SUDD SESSION COMPLETE` — appears in 5 of 7 recent stuck reports
- `**Mode:** brown` — appears in 3 of 7 recent stuck reports

## Pre-archive checks

- Registered: 3
- Ran: 12
- Failures: 3

Failing checks:
- discovered_audit_claude-md-architecture-refresh_01: LessonRecorded — no canonical '### [DONE|STUCK|FAILURE] discovered_audit_claude-md-architecture-refresh_01' or '## Lesson: discovered_audit_claude-md-architecture-refresh_01' heading with ≥ 3 body lines in sudd/memory/lessons.md
- discovered_audit_claude-md-architecture-refresh_01: SummaryHasCanonicalHeadings — archive/discovered_audit_claude-md-architecture-refresh_01_DONE/SUMMARY.md missing canonical headings: ## What Changed, ## Validation, ## Lessons
- discovered_audit_vision-known-open-work-stale_01: SummaryHasCanonicalHeadings — archive/discovered_audit_vision-known-open-work-stale_01_DONE/SUMMARY.md missing canonical headings: ## Why

