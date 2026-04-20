# Auto Report — 2026-04-19

## Session Info

- **Start**: 20:07 CEST
- **End**: 20:52 CEST
- **Elapsed**: 45m 21s
- **CLI**: claude
- **Stop reason**: change_limit

## Changes Processed

| # | Change | Outcome | Time | Tasks |
|---|--------|---------|------|-------|
| 1 | discovered_audit_session-log-cleanup_01 | DONE | 9m 10s | 6/6 |
| 2 | discovered_audit_prearchive-checks-in-report_01 | STUCK | 7m 43s | 13/13 |
| 3 | discovered_audit_state-json-session-fields_01 | STUCK | 6m 31s | 6/6 |
| 4 | discovered_audit_browser-use-yaml-config_01 | STUCK | 5m 33s | 1/1 |
| 5 | discovered_audit_session-start-handoff-sync_01 | STUCK | 4m 32s | 1/1 |

## Remaining Queue

1. **discovered_audit_claude-md-architecture-refresh_01** (mode: brown, source: proposal)
2. **discovered_audit_vision-known-open-work-stale_01** (mode: brown, source: proposal)
3. **discovered_audit_handoff-validator-template-cleanup_01** (mode: brown, source: proposal)

## Action Items

- discovered_audit_prearchive-checks-in-report_01: # Stuck: discovered_audit_prearchive-checks-in-report_01
- discovered_audit_state-json-session-fields_01: # Stuck: discovered_audit_state-json-session-fields_01
- discovered_audit_browser-use-yaml-config_01: # Stuck: discovered_audit_browser-use-yaml-config_01
- discovered_audit_session-start-handoff-sync_01: # Stuck: discovered_audit_session-start-handoff-sync_01

## Quarantine

4 change(s) quarantined in `sudd/changes/stuck/`:

- **discovered_audit_session-start-handoff-sync_01**
- **discovered_audit_browser-use-yaml-config_01**
- **discovered_audit_state-json-session-fields_01**
- **discovered_audit_prearchive-checks-in-report_01**

Use `sudd auto --retry-stuck` to restore them to the active queue.

## Detected Failure Patterns

- `══════════════════════════�…` — appears in 4 of 4 recent stuck reports
- `SUDD SESSION COMPLETE` — appears in 4 of 4 recent stuck reports

