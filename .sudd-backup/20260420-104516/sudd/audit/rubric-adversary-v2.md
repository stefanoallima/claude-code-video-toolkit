# Rubric Adversary Critique v2 (audit scope, iteration 2)

## Verdict
**FINAL** (with 3 MINOR nits — none blocking)

The revision addressed all CRITICAL and all IMPORTANT issues from v1. The rubric is now well-structured: criteria state neutral thresholds, today's verdicts live in a dedicated `## Current Scoring` table, the band algorithm is ordered and unambiguous, and the new DB-S1 (atomic-write Instant FAIL) correctly pin-points the invariant whose failure would make Stefano say "this is broken, stop." The 3 remaining nits are polish-level, not scoring-quality issues.

## v1 Issue Resolution Check

| v1 # | Sev | Resolution |
|------|-----|------------|
| 1 | CRITICAL | Fixed — all `Fail (CURRENT)` moved to `## Current Scoring` table; criteria bodies are now neutral. |
| 2 | CRITICAL | Fixed — old DB-AU1 removed, replaced with a band-override clamp in the algorithm (max NEEDS_WORK if MP-G4 or DB-S1 fails). |
| 3 | CRITICAL | Fixed — old DB-S1 demoted to MP-S4; new DB-S1 pins the real deal-breaker (non-atomic SaveState). |
| 4 | IMPORTANT | Fixed — MP-F2 now runs `find` + `ls` counts, executable without an external test. |
| 5 | IMPORTANT | Fixed — SP-C1 uses three observable proxies. |
| 6 | IMPORTANT | Fixed — SP-C2 scoped to post-commit-7678260 with explicit grep rule. |
| 7 | IMPORTANT | Fixed — SP-G3 relaxed to 5s/15s. |
| 8 | IMPORTANT | Fixed — SP-L1 now N/A-aware; MP-L1 accepts zero counts. |
| 9 | IMPORTANT | Fixed — MP-G7 added for `sudd doctor` supplier. |
| 10 | MINOR | Fixed — substring cites replace line numbers. |
| 11 | MINOR | Fixed — "Format version 1.0" removed. |
| 12 | MINOR | Fixed — Summary Score Bucket is now an ordered algorithm with override clamp. |

All 12 v1 issues dispositioned "Accepted" in the rubric's Revision Log; spot-check confirms the rubric text matches the dispositions.

## New Issues Introduced by the Revision

### MINOR (polish, not blocking)

1. **[Tally arithmetic typo]** The "Tallies" section under `## Current Scoring` reads: "Should Pass fails: 1 hard (SP-AU1) + 3 partials (SP-G1, SP-A2, SP-S1, SP-C2, MP-L2 partial) — treat partials as 0.5 each" — the parenthetical enumerates 5 items, not 3, and MP-L2 is a Must Pass not a Should Pass (shouldn't be counted in SP tally).
   Suggested fix: "Should Pass fails: 1 hard (SP-AU1) + 4 partials (SP-G1, SP-A2, SP-S1, SP-C2); plus MP-L2 partial counted against Must Pass. Treat partials as 0.5."
   Impact: cosmetic — the CRITICAL band assignment is driven by DB-S1 Instant FAIL, so the SP tally does not change the band.

2. **[Redundant criterion pair]** MP-G4 (atomic state writes) and DB-S1 (atomic SaveState Instant FAIL) now both check the same thing at different severities. That's intentional-by-design (v1 issue #3 asked for it), but the rubric should explicitly note this so a scorer doesn't think they're two separate observations. A single `state.go:178` being `os.WriteFile` will register as both "MP-G4 Fail" and "DB-S1 Instant FAIL".
   Suggested fix: Add a parenthetical under DB-S1: `(Note: same signal as MP-G4; atomic-write failure counts once against Must Pass AND triggers the Deal-Breaker band override — this is intentional.)`
   Impact: documentation only.

3. **[Missing live-URL arg handling]** `sudd audit` accepts `--url URL` (per manifest.json cli_routes). MP-AU1/AU2/AU3 do not distinguish "audit against this repo with no frontend" (`--skip-browser`) vs "audit against a downstream URL" (with `--url`). Today the rubric implicitly assumes the `--skip-browser` path. A scorer running `sudd audit --url https://example.com` against a future consumer repo would find the Must Pass thresholds still valid, but LIVE-1 (browser validation) would suddenly become scorable. The rubric does not say what happens to LIVE-1 when a URL is provided.
   Suggested fix: Add a one-liner under `## Live-Only Criteria`: "When `sudd audit --url <url>` is invoked, LIVE-1 becomes scorable via persona-browser-agent; criteria remain TBD and are elaborated in the downstream repo's own rubric."
   Impact: forward-compatibility note; not a today-scoring issue since this repo has no URL.

## Deal-Breaker Changes (net)

- **Removed**: DB-AU1 (unfalsifiable self-reference); old DB-S1 (regression guard for a behaviour nobody claimed).
- **Added**: new DB-S1 (atomic SaveState Instant FAIL) — directly captures the UC-1 defect that bricks the next auto session.
- **Unchanged**: DB-G1 (sacred files), DB-G2 (snapshot before modify), DB-G3 (shrink gate), DB-A1 (auto preflight gate), DB-A2 (deferred finalize stop_reason), DB-F1 (no 0-byte agents), DB-N1 (retention safety), DB-C1 (no empty archives).

Net: Deal-Breaker count went from 10 to 9, but severity alignment improved — DB-S1 now pin-points the single most user-breaking defect in the current repo instead of chasing a hypothetical silent-reset regression.

## Wrong-Surface Check

The rubric is CLI + markdown framework, no browser. Scanned for accidental browser-shaped criteria:
- No `viewport`, `click`, `form field`, `screenshot` criteria present.
- LIVE-1..4 correctly carved out as non-scored for this repo.
- Audit criteria (MP-AU1-3) check file artefacts and subprocess exit classification — correct surface.

**No wrong-surface criteria found.**

## BE-style vs User-Surface Balance Check

Counted criteria by surface:
- User-visible CLI behaviour: MP-G1, MP-G3, MP-G6, MP-G7, SP-G1-3, MP-A1-4, SP-A1-2, DB-A1-2, MP-AU1-3, SP-AU1, MP-L1, MP-N1-2, DB-G1-3, DB-N1 (~22)
- Data-file artefacts (state.json, lessons.md, changes dirs): MP-S1-4, SP-S1, DB-S1, MP-C1-4, SP-C1-2, DB-C1, MP-L2, SP-L1 (~13)
- Framework integrity (agents, commands): MP-G2, MP-F1-3, SP-F1, DB-F1 (~6)
- Pure code-style/structure: MP-G4 (Go atomic-write pattern) is the only one, and it is grounded in a user-visible failure mode (crash → bricked session), not stylistic preference.

Balance looks right — the rubric tracks the user workflow (auto → audit → changes lifecycle → learning → snapshots) and uses code-level signals only where they are the cleanest observation point for a user-facing invariant.

## Falsifiability Check

Scanned for unfalsifiable criteria (cannot possibly fail OR cannot possibly pass):
- Previously had one: old DB-AU1. Now removed.
- SP-L1 is explicitly marked N/A-aware, not unfalsifiable.
- Every remaining criterion has a concrete Pass / Fail distinction observable from files, command output, or test results.

**No unfalsifiable criteria found.**

## Final Verdict

**FINAL.** The rubric is ready for use by `persona-validator (mode=audit)`. Remaining 3 MINOR nits can be addressed in a follow-up revision or left as known-polish items — they do not change any band assignment and do not weaken scoring quality.

Remaining items left for optional human cleanup:
1. Tallies-section arithmetic typo (cosmetic).
2. Cross-reference note between MP-G4 and DB-S1 (documentation clarity).
3. Forward-compat note about LIVE-1 becoming scorable when `sudd audit --url` is used against a downstream repo (not applicable to this repo).
