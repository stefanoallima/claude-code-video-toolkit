# Persona Validation Result — default (Stefano)
**Mode**: audit
**Git SHA**: 678360e
**Date**: 2026-04-19

## Score: 52/100 (NEEDS_WORK)

Stefano's four objectives are each partially met, but two deal-breakers fire:
(1) a just-shipped feature (`state.json.stats` rollup) ships zero — literally dead
data where real data was promised; (2) the operational handoff (`CURRENT_STATE.md`)
under-reports the stuck pile by ~40% (claims 4, reality is 7). The framework
continues to make autonomous progress, but the surfaces Stefano relies on to
verify and unblock are self-contradictory.

## Objectives

- [~] **Obj 1: Verify working code** — 50/100 — Code compiles, 49 test files vs 73 source files (0.67 ratio, acceptable), lessons detail that unit tests for new features pass (e.g., 7 tests for stats rollup, 4 variants for stuck report). BUT the stats rollup ships as empty/zero data: `state.json.stats = {tasks_completed: 0, tasks_stuck: 0, tasks_blocked: 0, total_retries: 0}` despite `auto_session.changes_processed` containing 2 DONE and 3 STUCK. This is Stefano's deal-breaker #1 ("Empty/mock data in outputs — if the API returns `[]`, that's a fail"). Either `RollupSessionStats` (state.go:467) was never invoked on session end, or the session never reached its end-of-session finalization branch (`auto.go:483`) — `auto_session.stop_reason` is `""` which supports the latter reading. From a persona perspective: the feature's visible output is a lie.

- [~] **Obj 2: Autonomous progress** — 70/100 — Last auto_session processed 5 changes end-to-end without asking questions, 2 DONE (stuck-report-rendering-gaps_01 with 16/16 tasks, state-json-stats-rollup_01 with 6/6 tasks). No BLOCKED outcomes. But the 60% STUCK rate (3 of 5) is above Stefano's tolerance for "autonomous progress without intervention" — and two of those STUCKs are on pre-archive hygiene failures (LessonRecorded, SummaryHasCanonicalHeadings), which means the system is doing the work correctly then failing its own gate. `retry_count: 0` in state.json is either correct-for-this-run or a dead field — ambiguous from state alone. `discovered_audit_done-dirty-outcome-tier_01` STUCK with no `timeout_reason` recorded — violates the "pre-archive check failures always render a reason" contract that `stuck-report-rendering-gaps_01` just shipped. So the newest shipped feature has a hole in it.

- [~] **Obj 3: Understand archive** — 65/100 — 30 DONE archives with rich SUMMARY.md and structured lessons.md entries (verified: last 5 lessons for this session are present with Tags/Confidence/What worked/What failed/Lesson — high-quality, under-2-minutes-to-scan). Archive is searchable and self-describing. BUT two STUCK changes (`vision-known-open-work-stale_01` and `done-dirty-outcome-tier_01`) have `### [DONE]` headings in lessons.md despite STUCK status in state.json — the lesson labels contradict the actual outcome, which breaks the "understand what happened" contract. The learning pipeline is capturing work done correctly, but labeling it wrong relative to ground truth, so a human reading lessons.md alone would believe these changes shipped when they are in `sudd/changes/stuck/`.

- [~] **Obj 4: Diagnose stuck items** — 40/100 — 7 stuck directories exist, and `discovered_audit_stuck-report-rendering-gaps_01` just shipped the fix so every STUCK_REPORT.md has a canonical `## Pre-Archive Check Failures` section. Spot-check of `stuck/discovered_audit_done-dirty-outcome-tier_01/STUCK_REPORT.md`: it exists and logs the subprocess tail, but the "Last Error" section embeds a DONE success message from inside the subprocess rather than the real failure reason — confusing for a human triager. `CURRENT_STATE.md` TL;DR claims "**4 stuck** awaiting human review" when filesystem truth is 7 — this is the very document Stefano reads after a context reset, and it's off by 75%. Obj 4 success criterion is "each stuck item has actionable human steps" — partial for the 2 new STUCKs with `pre_archive_check_failed:X` reasons (actionable: fix the SUMMARY headings or lessons heading), weak for the older 5 (browser-use-yaml-config, prearchive-checks-in-report, session-start-handoff-sync, state-json-session-fields which already shipped as archive entries but are still in stuck/ — possible zombie stuck dirs).

## Gaps (ranked by severity)

1. **Stats rollup feature ships all zeros — dead field, broken contract** — CRITICAL
   - Evidence: `sudd/state.json` `stats: {tasks_completed: 0, tasks_stuck: 0, tasks_blocked: 0, total_retries: 0}` with no `stats_seeded` sentinel, while `auto_session.changes_processed` has 5 entries (2 DONE, 3 STUCK) and `auto_session.stop_reason` is empty string. Implementation at `sudd-go/internal/auto/state.go:467` (RollupSessionStats) and call site `sudd-go/cmd/sudd/auto.go:483` are correct code but the write never landed in the persisted state.json — most likely because the session was interrupted before line 484 (`MarkSessionEnd`) completed, OR the auto orchestrator exited before session finalization. Stefano's deal-breaker #1 explicitly names this class of failure.
   - Suggested fix: Add a `RollupSessionStats` call inside each change's post-processing loop (after `session.ChangesProcessed = append(...)` in `runner.go`/`auto.go`) instead of only at session end, so per-change increments survive crashes. Alternatively, run `MaybeBackfillSessionStats` once on next `sudd auto` start — the sentinel-guard was designed for exactly this recovery case, but state.json shows it has never run either. Confirm `auto.go:185` is reached on cold start.

2. **CURRENT_STATE.md stale and understates the stuck backlog by ~40%** — HIGH
   - Evidence: `sudd/CURRENT_STATE.md` line 6 TL;DR reads "6 active changes in flight with 4 stuck awaiting human review". Filesystem: 1 active (`discovered_audit_handoff-validator-template-cleanup_01`), 7 stuck. `refreshed-at` is 2026-04-19T19:31:12Z but subsequent session at 20:55 added 3 new STUCK entries and the refresh never re-ran. The same Stuck section lists all 7 correctly — so the TL;DR is derived from stale data even while the body is accurate.
   - Suggested fix: `internal/state/render.go` TL;DR generator should recount from filesystem at render time, not from a cached count embedded upstream. Trigger CURRENT_STATE.md refresh at session end (same place `MarkSessionEnd` runs, `auto.go:484`) not only on archive. Also consider a self-check: if TL;DR counts and body counts disagree, block render with an error.

3. **Lessons.md labels two STUCK changes as `### [DONE]`** — HIGH
   - Evidence: `sudd/memory/lessons.md` line 214 `### [DONE] discovered_audit_vision-known-open-work-stale_01 — 2026-04-19` and line 229 `### [DONE] discovered_audit_done-dirty-outcome-tier_01 — 2026-04-19`; both changes are present in `sudd/changes/stuck/` and both have `outcome: STUCK` in `state.json.auto_session.changes_processed`. The learning-engine wrote a lesson for work the runner then rejected at the pre-archive gate.
   - Suggested fix: learning-engine's canonical heading format should derive from the actual archival outcome (DONE/DONE_DIRTY/STUCK/FAILURE), not from whether the implementation subprocess self-declared success. Best insertion point: `done.md` step 2a already calls learning-engine Mode 1 — that step must not run until after the pre-archive check passes. Given the DONE_DIRTY feature just shipped, extend the outcome vocabulary in lesson headings to match the archival tier (`### [DONE_DIRTY]` for the shipped-but-hygiene-imperfect tier).

4. **`done-dirty-outcome-tier_01` STUCK with no timeout_reason recorded** — MEDIUM
   - Evidence: `state.json.auto_session.changes_processed[3]` — `outcome: STUCK, exit_code: 0, tasks_completed: 36, tasks_total: 36` but no `timeout_reason` and no `check_failures`. The change that literally introduced this outcome tier has a STUCK_REPORT.md embedding a DONE subprocess-tail as "Last Error", which is misleading. Either this should have been the new DONE_DIRTY tier (lesson was recorded, code was committed per log.md), or the pre-archive gate fired silently.
   - Suggested fix: Runner should require `TimeoutReason` to be non-empty on every STUCK branch (already the contract per `stuck-report-rendering-gaps_01` lesson at lessons.md:225 — "the populated variant must win"). Add `TestRunnerAlwaysPopulatesStuckReason` to `runner_test.go`. Investigate whether the DONE_DIRTY downgrade logic (`decideOutcome`) was active for this run and why it didn't fire.

5. **Older stuck/ entries appear alongside archive/ DONE entries — possible zombies** — MEDIUM
   - Evidence: `sudd/changes/stuck/discovered_audit_browser-use-yaml-config_01`, `session-start-handoff-sync_01`, and others have corresponding archive entries (confirmed: `browser-use-yaml-config` and `session-start-handoff-sync` both show `### [DONE]` lessons and the CURRENT_STATE "Just Shipped" list confirms archival). If they shipped, the stuck/ copy should have been removed at archive time, or was back-filled by the stuck-report-rendering-gaps_01 retrofit but never cleaned.
   - Suggested fix: Add a cleanup step in `performArchival` — if a change id reaches DONE archive status, remove any matching `sudd/changes/stuck/{id}/` directory. Add an integrity test: no id appears simultaneously in archive/ and stuck/.

6. **Session completed but `stop_reason` remains empty string** — MEDIUM
   - Evidence: `state.json.auto_session.stop_reason: ""` while `changes_processed` lists 5 items and `queue_remaining: []`. Either the session is still live (but no CLI is running — the git SHA moved past), or the session-end hook never wrote a stop_reason. Combined with gap #1 (zero stats), the strong read is: session finalization at `auto.go:474-489` was skipped entirely.
   - Suggested fix: Make session finalization defensive — wrap in deferred function at top of `sudd auto`, so an early return/panic still flushes `RollupSessionStats`, `MarkSessionEnd`, and clears `AutoSession`. Add a signal handler for SIGINT/SIGTERM that runs the same finalization.

7. **`handoff-validator` still referenced in 3 shipped templates** — LOW (known, active change in flight)
   - Evidence: `sudd-go/cmd/sudd/templates/.claude/commands/sudd/{apply,init,run}.md` all grep-match `handoff-validator`. The active change `discovered_audit_handoff-validator-template-cleanup_01` is addressing exactly this.
   - Suggested fix: none needed beyond completing the active change; this is a known item.

## Recommendations

1. **Priority 1 — fix the stats rollup dead-field** (gap #1). The feature's entire value is observability; shipping zeros is worse than not shipping it. Needs a per-change increment path, not only a session-end one. Also fix gap #6 (session finalization skipped) because they share a root cause.

2. **Priority 2 — wire CURRENT_STATE.md TL;DR to filesystem, not cached upstream state** (gap #2). This is the single highest-leverage fix for Obj 4 — Stefano reads this file first after a context reset, and a wrong number there poisons every downstream decision.

3. **Priority 3 — block learning-engine lesson writes when pre-archive gate will fail** (gap #3). The DONE_DIRTY tier created the correct framework for this — lessons for DONE_DIRTY should be labeled as such; lessons for STUCK should not say DONE.

4. **Priority 4 — runner contract: every STUCK carries a TimeoutReason** (gap #4). Simple Go-level invariant, one test guards it forever, closes the STUCK_REPORT misrender the stuck-report-rendering-gaps_01 change was supposed to prevent.

5. **Priority 5 — zombie-stuck cleanup** (gap #5). Consider proposing an integrity test that fails the build if any change id exists in both `archive/` and `stuck/`. Cheap, permanent.

6. **Generate change proposals: YES** — gaps 1, 2, 3, 4, and 5 are each concrete, actionable, and bounded. Gap #1 is urgent. Generate 3-5 proposals from the top gaps.
