# Auto Report — 2026-04-19

## Session Info

- **Start**: 23:14 CEST
- **End**: 02:38 CEST
- **Elapsed**: 3h 23m
- **CLI**: claude
- **Stop reason**: queue_empty

## Changes Processed

| # | Change | Outcome | Time | Tasks |
|---|--------|---------|------|-------|
| 1 | discovered_audit_stats-rollup-deadfield-fix_01 | STUCK | 9m 33s | 0/10 |
| 2 | discovered_audit_current-state-tldr-filesystem-truth_01 | DONE | 10m 21s | 7/7 |
| 3 | discovered_audit_lesson-heading-matches-outcome_01 | STUCK | 9m 53s | 1/1 |
| 4 | discovered_audit_runner-stuck-requires-reason_01 | DONE_DIRTY | 12m 57s | 9/9 |
| 5 | discovered_audit_archive-clears-zombie-stuck-dirs_01 | STUCK | 7m 6s | 6/6 |

## Action Items

- discovered_audit_stats-rollup-deadfield-fix_01: # Stuck: discovered_audit_stats-rollup-deadfield-fix_01
- discovered_audit_lesson-heading-matches-outcome_01: # Stuck: discovered_audit_lesson-heading-matches-outcome_01
- discovered_audit_archive-clears-zombie-stuck-dirs_01: # Stuck: discovered_audit_archive-clears-zombie-stuck-dirs_01

## Quarantine

3 change(s) quarantined in `sudd/changes/stuck/`:

- **discovered_audit_archive-clears-zombie-stuck-dirs_01**
- **discovered_audit_stats-rollup-deadfield-fix_01**
- **discovered_audit_lesson-heading-matches-outcome_01**

Use `sudd auto --retry-stuck` to restore them to the active queue.

## Dirty (shipped, needs cleanup)

1 change(s) in `sudd/changes/dirty/` — code landed, hygiene follow-up needed:

- **discovered_audit_runner-stuck-requires-reason_01** — Code shipped at 2026-04-19T21:59:15Z; pre-archive hygiene check failed. The change landed in `sudd/changes/dirty/` instead of `sudd/changes/archive/` because the subprocess committed code AND recorded its lesson, but one or more cosmetic checks flagged the archive artifacts. Fix the issues listed below, then manually move the directory to `sudd/changes/archive/discovered_audit_runner-stuck-requires-reason_01_DONE/`.

Open each `FOLLOWUP.md` for the specific hygiene fix needed.

## Pre-archive checks

- Registered: 3
- Ran: 9
- Failures: 4

Failing checks:
- discovered_audit_stats-rollup-deadfield-fix_01: LessonRecorded — no canonical '### [DONE|STUCK|FAILURE] discovered_audit_stats-rollup-deadfield-fix_01' or '## Lesson: discovered_audit_stats-rollup-deadfield-fix_01' heading with ≥ 3 body lines in sudd/memory/lessons.md
- discovered_audit_stats-rollup-deadfield-fix_01: TasksAllChecked — tasks.md has unchecked '- [ ]' boxes (or is missing)
- discovered_audit_stats-rollup-deadfield-fix_01: SummaryHasCanonicalHeadings — archive/discovered_audit_stats-rollup-deadfield-fix_01_DONE/SUMMARY.md missing canonical headings: ## What Changed, ## Why, ## Validation
- discovered_audit_runner-stuck-requires-reason_01: SummaryHasCanonicalHeadings — archive/discovered_audit_runner-stuck-requires-reason_01_DONE/SUMMARY.md missing canonical headings: ## Lessons

