# Platform Audit Report

**Date**: 2026-04-19
**Git SHA**: 678360e
**Personas evaluated**: 1 (default — Stefano, Framework Owner)
**Browser testing**: SKIPPED — repo is CLI+markdown framework, no HTTP surface
**Code-intel pipeline**: SKIPPED — `api_surface.backend_endpoints = []`, `frontend_routes = []`
**Overall health**: **NEEDS_WORK** (regressed from GOOD/82)

## Persona Scores

| Persona | Score | Level | Objectives Met | Gaps |
|---------|-------|-------|---------------|------|
| default (Stefano) | 52/100 | NEEDS_WORK | 0/4 full, 4/4 partial | 7 (1 critical, 2 high, 3 medium, 1 known) |

## Overall Health Criteria

- EXCELLENT: All personas >= 98, no critical gaps
- GOOD: All personas >= 80, no critical gaps
- NEEDS_WORK: Any persona 50–79, or important gaps ← **current**
- CRITICAL: Any persona < 50, or critical gaps

Note: one **CRITICAL** gap (GAP-1, dead-field stats rollup) is present. Overall
stays NEEDS_WORK rather than CRITICAL because the score floor (52) holds and the
critical gap has a bounded fix path with a proposal already written.

## Per-Persona Details

### default (Stefano) — 52/100 (NEEDS_WORK)

#### Objectives

- [~] **Obj 1: Verify working code** — 50/100 — Code compiles, 49 test files vs 73 source, tests for new features pass. BUT `state.json.stats` ships `{0,0,0,0}` despite 5 changes processed — Stefano's deal-breaker #1 ("empty/mock data in outputs") fires.
- [~] **Obj 2: Autonomous progress** — 70/100 — 5 changes processed end-to-end without intervention, but 60% STUCK rate (3/5) on pre-archive hygiene, and one STUCK has no `timeout_reason`.
- [~] **Obj 3: Understand archive** — 65/100 — 30 DONE archives with rich SUMMARY.md and structured lessons.md. BUT two STUCK changes are labeled `### [DONE]` in lessons.md — the outcome-label contract is broken.
- [~] **Obj 4: Diagnose stuck items** — 40/100 — 7 stuck dirs, but `CURRENT_STATE.md` TL;DR says "4 stuck" (off by 75%). STUCK_REPORT for `done-dirty-outcome-tier_01` embeds a DONE success tail as "Last Error".

#### Gaps Found

1. **Stats rollup ships all zeros — dead-field, broken contract** — CRITICAL
   - Evidence: `state.json.stats: {0,0,0,0}`; `auto_session.stop_reason: ""`; session finalization at `cmd/sudd/auto.go:474–489` never ran. `RollupSessionStats` at `internal/auto/state.go:467` is correct code but uncalled.
   - Suggested proposal: `discovered_audit_stats-rollup-deadfield-fix_01` ✅ written

2. **CURRENT_STATE.md TL;DR stale, understates stuck backlog by ~40%** — HIGH
   - Evidence: `sudd/CURRENT_STATE.md:6` claims "6 active, 4 stuck"; filesystem has 1 active, 7 stuck. `refreshed-at: 19:31:12Z` but session at 20:55 added STUCKs without re-rendering.
   - Suggested proposal: `discovered_audit_current-state-tldr-filesystem-truth_01` ✅ written

3. **Lessons.md labels STUCK changes as `### [DONE]`** — HIGH
   - Evidence: `sudd/memory/lessons.md:214,229` — DONE heading on changes that are STUCK in state.json and in `sudd/changes/stuck/`.
   - Suggested proposal: `discovered_audit_lesson-heading-matches-outcome_01` ✅ written

4. **Runner missing `timeout_reason` on `done-dirty-outcome-tier_01` STUCK** — MEDIUM
   - Evidence: `state.json.auto_session.changes_processed[3]` — STUCK, exit 0, 36/36 tasks — but no reason and no check_failures. STUCK_REPORT.md embeds a DONE success tail as "Last Error".
   - Suggested proposal: `discovered_audit_runner-stuck-requires-reason_01` ✅ written

5. **Zombie stuck/ directories alongside archived DONEs** — MEDIUM
   - Evidence: `sudd/changes/stuck/{browser-use-yaml-config,session-start-handoff-sync}_01` have DONE archives and DONE lessons. stuck/ copies never cleaned at archival.
   - Suggested proposal: `discovered_audit_archive-clears-zombie-stuck-dirs_01` ✅ written

6. **Session finalization skipped — stop_reason empty** — MEDIUM
   - Evidence: `auto_session.stop_reason: ""` with `queue_remaining: []` and 5 changes processed; shares root cause with GAP-1.
   - Suggested proposal: covered by `stats-rollup-deadfield-fix_01` (same fix path)

7. **`handoff-validator` still in 3 shipped templates** — LOW (known)
   - Evidence: grep matches in `templates/.claude/commands/sudd/{apply,init,run}.md`.
   - Active change: `discovered_audit_handoff-validator-template-cleanup_01`

#### UX Issues
N/A (no UI surface).

## Proposals Generated

| # | Proposal | Persona | Gap | Size | Priority |
|---|----------|---------|-----|------|----------|
| 1 | discovered_audit_stats-rollup-deadfield-fix_01 | stefano | GAP-1 (CRITICAL) | S | 1 |
| 2 | discovered_audit_current-state-tldr-filesystem-truth_01 | stefano | GAP-2 (HIGH) | S | 1 |
| 3 | discovered_audit_lesson-heading-matches-outcome_01 | stefano | GAP-3 (HIGH) | S | 2 |
| 4 | discovered_audit_runner-stuck-requires-reason_01 | stefano | GAP-4 (MEDIUM) | M | 2 |
| 5 | discovered_audit_archive-clears-zombie-stuck-dirs_01 | stefano | GAP-5 (MEDIUM) | S | 3 |

5 proposals from 5 gaps. GAP-6 folded into proposal #1 (same root cause). GAP-7 already in flight.

## Recommendations

1. **P1 — Fix the stats rollup dead-field** (proposal #1). Feature shipped zero data — Stefano's deal-breaker #1. Also resolves GAP-6 (missing stop_reason) since both stem from skipped session finalization.
2. **P1 — Wire `CURRENT_STATE.md` TL;DR to filesystem truth** (proposal #2). Highest leverage on Obj 4 — wrong count in the context-reset handoff poisons every downstream decision.
3. **P2 — Block lesson writes before pre-archive gate passes** (proposal #3). Extend the DONE_DIRTY tier to lesson headings too.
4. **P2 — Enforce runner TimeoutReason invariant** (proposal #4). Simple Go-level contract + test.
5. **P3 — Zombie-stuck cleanup + integrity test** (proposal #5). Cheap, permanent.

## Previous Audit Comparison

Previous audit (`sudd/audit/report-previous.md`): 82/100 GOOD, 3 gaps.
This audit: 52/100 NEEDS_WORK, 7 gaps (1 CRITICAL new), 5 proposals generated.

**Regression of –30 points in 4 hours.** Between audits:

- 5 change session ran (`stuck-report-rendering-gaps_01` DONE, `done-dirty-outcome-tier_01` STUCK, `state-json-stats-rollup_01` DONE but dead-field, 2 others STUCK on pre-archive hygiene).
- Two DONE archives landed with broken contracts: the stats-rollup feature ships zero data, and the pre-archive gate fires but lessons are still labeled `[DONE]`.
- `CURRENT_STATE.md` went stale (last refreshed 19:31; session at 20:55 added STUCKs without re-render).

**Interpretation:** The v3.8.24 session shipped *code* but the code's *contract* isn't holding in live state. The gap between "tests pass" and "field populates in production" is the whole point of this persona's objective #1 — and it's now the top finding.

## Audit Pipeline Notes

- **Step 2 (code-intel)**: skipped; manifest shows no FE/BE surface (CLI tool).
- **Step 3 (browser testing)**: skipped; no HTTP surface.
- **Step 4**: run against manifest + vision + state.json + CURRENT_STATE + lessons.md + archive/stuck/active listings.
- **Evidence source**: filesystem ground truth cross-referenced against persisted state and orchestrator documents.
