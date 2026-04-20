# Rubric Adversary Critique v1 (audit scope, iteration 1)

## Verdict
NEEDS_REVISION

The rubric is very well-grounded — nearly every criterion cites a file:line or a specific Go test, and the LIVE_ONLY carve-out correctly prevents false fails against a repo with no frontend. The main defects are (a) two criteria that mix the adversary's role with the scorer's — they already encode a "CURRENT" pass/fail verdict instead of a neutral threshold, which means a scorer running the rubric later against a fixed repo would still mark them "Fail (CURRENT)"; (b) one genuinely unfalsifiable criterion and one tautology; (c) a Deal-Breaker that isn't really a deal-breaker; and (d) two criteria that quietly depend on artefacts the scorer cannot observe in this audit scope. Once these are neutralised the rubric is ready.

## Summary
- Total criteria reviewed: 45 (Must Pass 24 + Should Pass 11 + Deal-Breakers 10) across 8 sections
- Issues found: 11 (3 CRITICAL, 5 IMPORTANT, 3 MINOR)

## Issues

### CRITICAL (will cause false passes or false fails)

1. **[Pre-baked verdict]** Section: Global / Must Pass, criteria **MP-G4 / MP-G5 / MP-G6**, and Changes Workflow **MP-C4**, and State File **MP-S1**, and Audit **MP-AU3**, and Audit Should Pass **SP-AU1**.
   Problem: Each of these bakes "**Fail (CURRENT)**: …" into the criterion body itself. That's an adversary/codeintel finding, not a rubric threshold. A scorer running this rubric against a future commit where UC-1/UC-2/UC-3/UC-4/UC-5 are fixed will still read the "Fail (CURRENT)" label and mis-score. The rubric's job is to state the threshold; whether today's repo meets it is the scorer's output.
   Suggested fix: Keep only the Pass / Partial / Fail threshold rows for each criterion. Move the "CURRENT" status into a new section `## Current Scoring (git 2eb9211)` at the bottom — that's the right place for today's observations. Example for MP-G4:
   ```
   - **MP-G4 [obj#2 — crash recovery]**: `sudd/state.json` writes are atomic (tmp + fsync + rename).
     - Signal: sudd-go/internal/auto/state.go SaveState function.
     - Pass: uses writeAtomic / atomicWrite pattern (tmp file + fsync + rename).
     - Partial: at least tmp+rename but no fsync.
     - Fail: direct os.WriteFile or equivalent non-atomic.
   ```
   Then, separately: `## Current Scoring (git 2eb9211)` table listing MP-G4 = Fail, evidence = state.go:178 os.WriteFile.

2. **[Unfalsifiable]** Section: Audit / Deal-Breakers, **DB-AU1** "Audit MUST NOT declare EXCELLENT on a repo where MP-G4 (atomic state writes) fails."
   Problem: This is a self-referential contract against the rubric itself, not against the code under audit. The "Signal" says "rubric consistency — the audit's own integrity rubric should catch this." The "Instant FAIL" clause refers to a hypothetical past report. There is no observable signal *right now* that can pass or fail this. It's unfalsifiable at scoring time.
   Suggested fix: Either (a) delete it, or (b) convert to a real rule in the summary bucket: "If MP-G4 = Fail, the maximum band achievable is NEEDS_WORK regardless of other scores." That's an algorithmic rule for the health-score section, not a Deal-Breaker criterion. Move it to `## Summary Score Bucket` as an overriding clamp.

3. **[Wrong surface / not a deal-breaker]** Section: State File / Deal-Breakers, **DB-S1** "On any LoadState error, `sudd auto` must NOT silently seed a fresh state.json overwriting the broken one."
   Problem: The Pass threshold says `LoadState error → os.Exit(1)` and marks current behaviour as passing. The Instant-FAIL clause ("silent reset that loses history") is the *inverse* of current behaviour — i.e. this Deal-Breaker checks that the code does NOT do a thing that nobody has claimed it does. It's a regression guard, fine — but as a Deal-Breaker it over-weights something that would require a future regression. A stronger Deal-Breaker in this area is UC-1 itself: the non-atomic write that bricks the next session's LoadState.
   Suggested fix: Demote DB-S1 to a Must Pass regression guard (MP-S4). Add a real Deal-Breaker DB-S2: "State.json write must be atomic — any non-atomic write that can leave unparseable JSON bricks the autonomous loop (vision.md 'fail loud at session start'). Signal: SaveState uses tmp+fsync+rename. Instant FAIL: direct os.WriteFile." That aligns Deal-Breaker severity with the persona's actual "this is broken, stop" reaction.

### IMPORTANT (weakens scoring quality)

4. **[Tautology]** Section: Markdown Framework / **MP-F2** "Embedded template … contains >= live count (no template drift below live)."
   Problem: The body says `live==templates==35 at this commit, BUT no regression test asserts the equality, so the v3.8.x drift scenario is still reachable on future changes (UC-7).` If the threshold is "templates >= live" and both are 35, this passes; it can only fail at scoring time if a human happens to notice drift between `ls sudd/agents` and `fs.WalkDir templateFS`. At scoring time with no test, the scorer has to either execute the comparison themselves (fine, say so) or assume both match (useless).
   Suggested fix: Rename to **MP-F2**: `ls sudd/agents/*.md | wc -l == find sudd-go/cmd/sudd/templates/sudd/agents -name '*.md' | wc -l`. Pass if counts match. Partial if templates > live. Fail if templates < live. Make the comparison executable by the scorer, not contingent on a test that may not exist.

5. **[Hand-wavy]** Section: Changes Workflow / Should Pass, **SP-C1** "Every `archive/<id>_DONE/` has SUMMARY.md readable in <2min (per persona success-criteria quote)."
   Problem: "Readable in <2 min" is not observable from artefacts. The persona quote is an outcome claim, not a file property. A scorer cannot measure reading time.
   Suggested fix: Replace with three concrete sub-thresholds: (a) SUMMARY.md exists, (b) first heading is `# ` within first 5 lines, (c) file is ≤ 400 lines. That's a proxy for "skimmable in 2 min" with observable signals.

6. **[Hand-wavy]** Section: Changes Workflow / Should Pass, **SP-C2** "no mismatches" between archive outcome dirs and lessons.md `### [DONE] / ### [STUCK]` headings.
   Problem: The criterion does not spell out how to map archive id → heading. Multiple archives may contribute lessons to a single heading block; some older archives predate the heading convention. Without a deterministic mapping rule the criterion is unscore-able without interpretation.
   Suggested fix: "For every archive/<id>_DONE or stuck/<id> after 2026-03-01 (heading-rewrite commit 7678260), `grep -F '<id>' sudd/memory/lessons.md` returns a line that falls under a `### [DONE]` or `### [STUCK]` heading matching the outcome tier. Pass: 100% match for post-cutoff ids. Partial: ≥80%. Fail: <80%."

7. **[Over-specified]** Section: Global / Should Pass, **SP-G3** "`sudd vision` and `sudd vision context` produce output in under 1 second on a typical vision.md (~300 lines)."
   Problem: 1-second latency on a 300-line file is a sensible target but not a user-visible one; it risks false-failing on slow machines, in CI containers, or under high system load. There's no observable defect a user would experience if this took 1.5 s.
   Suggested fix: Loosen to "under 5 seconds" or replace with "exits 0 with at least one non-empty line on stdout". Keep latency as a SP, not a hard threshold.

8. **[Untestable without external service]** Section: Learning / **MP-L1** and **SP-L1** both assume `~/.sudd/learning/patterns.md` exists.
   Problem: On a fresh audit machine (audit subprocess runs in a clean container per RunAudit), `~/.sudd/` may not exist at all — these criteria would fail on a pristine CI box where no `sudd learn sync` has ever run. That's not a defect; it's absence of cross-repo history.
   Suggested fix: Reframe as "if `~/.sudd/learning/patterns.md` exists AND `sudd learn status` reports it, counts must be > 0. If file doesn't exist, this criterion is N/A, not Fail."

9. **[Missing coverage]** No criterion covers **UC-9 / UC-8** (dead code). Also no criterion covers the doctor preflight itself (Stefano's "fail loud" memory invariant) except via the auto-side MP-G3 / DB-A1.
   Problem: Vision explicitly lists `sudd doctor` as the preflight gate and the persona memory entry is "Preflight blocks by default, never silent-fails." The rubric checks the *consumer* (auto refuses to start) but not the *supplier* (doctor itself actually runs all checks and returns non-zero on any blocker). If doctor has a warn-and-continue path internally, MP-G3 passes vacuously.
   Suggested fix: Add **MP-G7 [obj#2]**: "`sudd doctor --json` exits non-zero when any required check fails. Signal: `sudd-go/internal/doctor/` — every check's failure path sets exit code. Pass: chmod -w sudd.yaml, run doctor, exit != 0. Partial: exit != 0 only for a subset of check failures. Fail: exit 0 despite a failure (silent-warn)."

### MINOR (improvements, not blockers)

10. **[Traceability]** Section: Global / **MP-G3** cites "vision.md line ~203". Line numbers drift; readers can't verify the quote. Fix: replace with the exact phrase `"Fail loud at session start, never silently mid-run"` (an immutable substring the scorer can grep).

11. **[Format-version naming]** The header says `Format version: 1.0`. No schema exists anywhere else in the repo for rubric format. Either add a pointer to the schema or drop the field to avoid implying an enforced format.

12. **[Summary bucket arithmetic]** The Summary Score Bucket rules overlap: "NEEDS_WORK" lists `0 Deal-Breaker fails` but so does GOOD and EXCELLENT. A single row fails with `>=1 DB fail → CRITICAL`, which is fine, but the NEEDS_WORK row mentions "0 Deal-Breaker fails" redundantly. Also, "EXCELLENT: All Must Pass + 80% Should Pass" means a single Must Pass miss kicks to NEEDS_WORK — the rubric's own bucket rules contradict the observed stance that "7 Must Pass fails = NEEDS_WORK bordering on CRITICAL". 7 MP fails should almost certainly be CRITICAL under any reasonable reading. Clarify the band boundaries numerically: CRITICAL if `MP_fails >= 3 OR DB_fails >= 1`, else NEEDS_WORK if `MP_fails >= 1`, else GOOD if `SP_fails > 50%`, else EXCELLENT.

## Pages with No Issues
- Snapshots & Recovery (MP-N1, MP-N2, DB-N1): concrete signals, observable, correct severity.
- Live-Only enumeration: correctly marked non-scored, accurate scope note.
- Audit / **MP-AU1** (header presence): binary, observable, right threshold.
- Changes Workflow **MP-C1** (disjoint dirs): `comm -12` is a concrete signal with a deterministic pass/fail.
- Markdown Framework **MP-F1** (35 non-empty agents) and **DB-F1** (no 0-byte agent): exact counts, filesystem-observable.
- Auto **MP-A4** (TimeoutReason non-empty) and **DB-A2** (deferred finalize stop_reason): both have file:line evidence and binary thresholds.
