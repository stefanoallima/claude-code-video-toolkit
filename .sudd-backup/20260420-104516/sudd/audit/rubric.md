# Audit Rubric: SUDD Platform

Generated from: sudd/vision.md + sudd/personas/default.md (Stefano / Framework Owner) + sudd/codebase-manifest.json + sudd/audit/codeintel.json + sudd/audit/manifest.json
Generated at: 2026-04-20T00:45:00Z
Git SHA: 2eb9211c715ee50fc6300729cc23d8870eb4ac08
Revision: v2 (post-adversary pass)

Scope: whole platform (Go CLI + markdown framework). No frontend exists — rubric targets CLI commands, state files, and framework invariants.
Persona: single enriched persona "Stefano (Fallback End-User) — Technical Lead / Framework Owner" with four `## Objectives` at `sudd/personas/default.md:29-40`.

---

## How to Read This Rubric

Each criterion is a **neutral threshold** — not a verdict on today's repo. Structure:

- `ID [obj#N]`: short title mapped to a persona objective line.
- `Signal`: a specific file, command, or grep the scorer runs.
- `Pass` / `Partial` / `Fail`: three rows, observable, mutually exclusive.

The scorer's today-verdict lives in **`## Current Scoring (git 2eb9211)`** at the bottom — not inside the criteria themselves. That separation keeps the rubric reusable on future commits.

Criteria that require a running HTTP surface or live browser are flagged **`LIVE_ONLY`** — this repo has no frontend, so they are enumerated, not scored. See `## Live-Only Criteria` at the bottom.

Vision-quote citations use the exact substring (grep-able) rather than a line number, since line numbers drift.

---

## Global / Cross-Platform

Identified by: the `sudd/` tree exists and `sudd-go/bin/sudd` is on PATH or built from source.

### Must Pass

- **MP-G1 [obj#1 — working code, all tests pass]**: `go test ./... -v` from sudd-go/ exits 0.
  - Signal: `sudd-go/` `go test` exit code.
  - Pass: exit 0 with no FAIL lines.
  - Partial: passes except known `t.Skipf` on non-repo hosts.
  - Fail: any non-skip FAIL.

- **MP-G2 [obj#1 — no placeholder data]**: No agent file in `sudd/agents/*.md` is 0 bytes; `sudd/standards.md` is non-empty.
  - Signal: `TestFrameworkIntegrity_NoZeroByteAgents` + `TestFrameworkIntegrity_StandardsMDNotEmpty` (framework_integrity_test.go:53,90).
  - Pass: both tests pass.
  - Fail: either fails.

- **MP-G3 [obj#2 — autonomy]**: `sudd auto` refuses to start if `sudd doctor` reports a blocker and `--skip-preflight` is not passed.
  - Signal: auto.go preflight gate + vision substring `"Fail loud at session start, never silently mid-run"`.
  - Pass: auto exits non-zero with a doctor-cite stderr message when a required check fails.
  - Partial: auto logs a warning and continues despite a failing check.
  - Fail: auto proceeds with no mention of the failing check.

- **MP-G4 [obj#2 — crash recovery]**: `sudd/state.json` writes are atomic (tmp file + fsync + rename).
  - Signal: `sudd-go/internal/auto/state.go` SaveState implementation.
  - Pass: uses `writeAtomic` / `atomicWrite` pattern (tmp + fsync + rename), mirroring `internal/state/write.go:78` or `internal/vision/vision.go:86`.
  - Partial: tmp file + rename present but missing `fsync` (or vice versa — tmp file present but no rename).
  - Fail: direct `os.WriteFile` or any non-atomic write to `state.json`.

- **MP-G5 [obj#2 — no silent-fails]**: Every `SaveState` error site in `sudd auto` has one of three remediations: (a) retry, (b) abort the loop, (c) promote to STUCK. Plain stderr warn + continue is disallowed.
  - Signal: every `SaveState` call in `sudd-go/cmd/sudd/auto.go`.
  - Pass: 100% of SaveState error paths have one of the three remediations; none use `fmt.Fprintf(os.Stderr, "Warning: ...") + continue`.
  - Partial: ≥1 but <100% call sites have a remediation.
  - Fail: any call site uses warn-and-continue with no other handling.

- **MP-G6 [obj#1, obj#3 — manifest reality]**: Every CLI command listed in `sudd/codebase-manifest.json` under the CLI-commands section corresponds to a registered cobra command (i.e., an `AddCommand(...)` call) OR is explicitly annotated in the manifest as a flag-only helper.
  - Signal: `sudd --help` output vs `jq` over `codebase-manifest.json`.
  - Pass: every manifest entry is either runnable via `sudd <name>` (exit 0 or 1 with a real help message, not "unknown command") or explicitly labelled flag-only.
  - Partial: 1 drift (off by ≤1 entry).
  - Fail: ≥2 drifts, or a prominent advertised command is missing.

- **MP-G7 [obj#2 — fail-loud preflight]**: `sudd doctor --json` exits non-zero whenever any required check fails.
  - Signal: each failure path in `sudd-go/internal/doctor/*` sets an exit-code-changing flag.
  - Pass: contrived failure (e.g., `chmod -w sudd/sudd.yaml`, missing tier CLI) yields `sudd doctor` exit ≠ 0 and stderr citing the failed check.
  - Partial: exit code flips for some but not all required checks.
  - Fail: doctor exits 0 despite a check marked "required" reporting failure (silent-warn).

### Should Pass

- **SP-G1 [obj#3 — clarity]**: CLI command `--help` text names the primary state files each command reads or writes.
  - Signal: `sudd <cmd> --help` output.
  - Pass: every help-text mentions at least one of state.json / vision.md / sudd.yaml / changes/ when that command touches them.
  - Partial: ≥50% of commands.
  - Fail: <50%.

- **SP-G2 [obj#2 — observability]**: `sudd state` and `sudd status` render without error on a repo where state.json is valid but minimal (only `active_change` and `phase`).
  - Signal: both commands exit 0 on a minimal state.json.

- **SP-G3 [obj#3 — responsiveness]**: `sudd vision` and `sudd vision context` exit 0 with non-empty stdout on a typical vision.md (~300 lines), within 5 seconds on a developer laptop.
  - Signal: `time sudd vision` and `time sudd vision context`.
  - Pass: both exit 0, non-empty stdout, real time <5s.
  - Partial: exit 0 with non-empty stdout but time 5-15s.
  - Fail: exit non-zero OR stdout empty OR >15s.

### Deal-Breakers

- **DB-G1 [obj#3 — sacred files]**: `sudd update` NEVER overwrites `sudd/vision.md`, `AGENTS.md`, or files under `sudd/personas/`.
  - Signal: `TestUpdateFromLiveSource_NeverTouchesVisionMD` in installer; mtime comparison before/after a live `sudd update` run.
  - Instant FAIL: vision.md mtime changes across a `sudd update` invocation.

- **DB-G2 [obj#2 — recovery]**: `sudd update` ALWAYS creates a snapshot in `~/.sudd/snapshots/<slug>/<ts>.tar.gz` BEFORE modifying any target file.
  - Signal: compare snapshot tarball mtime vs first modified target file mtime.
  - Instant FAIL: any `sudd update` run leaves no snapshot behind, OR snapshot mtime > first modified file mtime.

- **DB-G3 [obj#2 — shrink gate]**: `sudd update` refuses to write a file that would shrink the target by >50% or to 0 bytes unless `--allow-shrink` is passed.
  - Signal: `installer.UpdateOptions.AllowShrink` + shrink-gate refusal behaviour.
  - Instant FAIL: a 5KB target file gets overwritten with a 100-byte file without `--allow-shrink`.

---

## CLI Command: `sudd auto` (the Ralph Loop engine)

Identified by: invoking `sudd auto` from an initialized SUDD repo with at least one active change or proposal in `changes/active/` or `changes/inbox/`.

### Must Pass

- **MP-A1 [obj#2 — autonomy]**: Empty queue triggers discovery, not exit.
  - Signal: `sudd-go/internal/auto/queue.go` + `discovery.go ShouldRunDiscovery`.
  - Pass: `sudd auto --fresh` against an empty proposal set invokes `/sudd-discover` as a subprocess and re-scans the queue.
  - Fail: exits with "nothing to do" when discovery was due.

- **MP-A2 [obj#1 — completion]**: Every change in the queue resolves to exactly one of `archive/<id>_DONE`, `dirty/<id>`, or `stuck/<id>`. No change remains in `active/` without a log.md updated during the session.
  - Signal: `sudd-go/internal/auto/runner.go performArchival` + `sudd/changes/active/` post-session state.
  - Pass: 100% of session's processed changes leave `active/` into one of the three resolution dirs.
  - Partial: >0 but <100% remain in `active/` with a log.md showing in-session progress.
  - Fail: a change remains in `active/` with no log.md and no resolution.

- **MP-A3 [obj#2 — retry ladder]**: Retries escalate tiers per vision substring `"Retry 0-1: free tier"` / `"Retry 6-7: opus"` / `"Retry 8:   STUCK"`.
  - Signal: `sudd/sudd.yaml → escalation:` + `internal/auto/runner.go` retry dispatch.
  - Pass: the tier used at retry N matches the yaml ladder; retry 8 lands the change in `stuck/`.
  - Fail: retry count increments without tier change, or retry 8+ does not promote to STUCK.

- **MP-A4 [obj#4 — diagnostics]**: Every `stuck/<id>/STUCK_REPORT.md` contains a non-empty `TimeoutReason:` line.
  - Signal: `sudd-go/internal/auto/stuck.go` (see commit dbbcd9e).
  - Pass: 100% of `stuck/<id>/STUCK_REPORT.md` files have a non-empty `TimeoutReason:` line.
  - Partial: ≥50% but <100%.
  - Fail: <50%.

### Should Pass

- **SP-A1 [obj#3 — morning report]**: `sudd/auto-reports/<date>/summary.md` lists every processed change with outcome and tier used at resolution.
  - Signal: file presence + grep for each processed id and tier name.
  - Pass: 100% of session ids appear with outcome + tier.

- **SP-A2 [obj#3 — inline stats]**: `state.json.stats` increments per change (not only at session end) so a mid-session crash preserves counts.
  - Signal: `IncrementChangeStats` call sites in `auto.go`.
  - Pass: stats-delta observable after the first change completes and is persisted across a simulated SIGKILL. (Depends on MP-G4 atomicity for full crash-safety.)

### Deal-Breakers

- **DB-A1 [obj#2]**: `sudd auto` refuses to start if `sudd doctor` reports blockers and `--skip-preflight` is not passed.
  - Signal: auto.go preflight gate.
  - Instant FAIL: auto runs despite doctor blocker without `--skip-preflight`.

- **DB-A2 [obj#3]**: Deferred session finalizer runs on panic, signal, budget, and normal exit — writes `summary.md` and sets `auto_session.stop_reason` to a non-empty string.
  - Signal: `defer finalize(...)` in auto.go.
  - Instant FAIL: any exit path leaves `auto_session.stop_reason` empty.

---

## CLI Command: `sudd audit` (platform persona gate)

Identified by: invoking `sudd audit [target] [--skip-browser]`.

### Must Pass

- **MP-AU1 [obj#1]**: After `sudd audit` completes, `sudd/audit/report.md` exists and its first heading is exactly one of: `EXCELLENT`, `GOOD`, `NEEDS_WORK`, `CRITICAL`.
  - Signal: `head -20 sudd/audit/report.md | grep -E '^# (EXCELLENT|GOOD|NEEDS_WORK|CRITICAL)'`.
  - Pass: header present + a score section present.
  - Fail: no report.md OR missing/misspelled header.

- **MP-AU2 [obj#4 — gap proposals]**: Each gap identified in `report.md` produces a corresponding `sudd/changes/active/discovered_audit_*` proposal.
  - Signal: for each gap listed in report.md, a directory matching `discovered_audit_<slug>_NN` exists.
  - Pass: every gap has a proposal.
  - Partial: ≥80%.
  - Fail: <80%.

- **MP-AU3 [obj#2 — classified failure]**: `sudd audit` surfaces a subprocess-outcome classification (timeout / quota / crash / generic) on non-zero exit.
  - Signal: `sudd-go/internal/auto/audit.go` error wrapping + CLI exit path.
  - Pass: non-zero exits include a classification token (e.g., `[TIMEOUT]`, `[QUOTA]`, `[CRASH]`) in stderr.
  - Partial: some but not all classes distinguished.
  - Fail: all errors wrap uniformly with no class.

### Should Pass

- **SP-AU1 [obj#1]**: `sudd audit` has Go-level smoke test coverage.
  - Signal: presence of `sudd-go/cmd/sudd/audit_test.go` OR tests in `sudd-go/internal/auto/audit_test.go`.
  - Pass: at least one test file exists and its tests pass.
  - Fail: neither file exists.

---

## State File: `sudd/state.json`

Identified by: top-level file at `sudd/state.json`.

### Must Pass

- **MP-S1 [obj#2, obj#3 — parseability]**: File is valid JSON parseable by `json.Unmarshal` at all times, including after a simulated SIGKILL during write.
  - Signal: `LoadState` succeeds on any non-empty state.json that the framework itself produced.
  - Pass: `jq . sudd/state.json` exit 0 before and after a SIGKILL-during-save test.
  - Fail: parse error on a framework-produced file (implies non-atomic write corruption).

- **MP-S2 [obj#3 — round-trip]**: Unknown fields are preserved across load/save.
  - Signal: `state.go` `map[string]json.RawMessage` pattern.
  - Pass: a custom field injected into state.json survives a `sudd auto` no-op cycle.

- **MP-S3 [obj#2 — stop_reason]**: `auto_session.stop_reason` is non-empty at the end of every session (including panic / signal / budget exits).
  - Signal: deferred finalize in `auto.go` sets `stop_reason`.
  - Pass: grep `"stop_reason": ""` in recent state.json samples returns nothing.
  - Fail: any recent session ended with empty `stop_reason`.

- **MP-S4 [obj#2 — no silent reset]**: On any `LoadState` error, `sudd auto` must NOT silently seed a fresh state.json overwriting the broken one. (Regression guard — promoted from DB-S1 in v1.)
  - Signal: state.go load-error path.
  - Pass: LoadState error → `os.Exit(1)` with "parse state.json" message; broken file untouched.
  - Fail: silent reset that loses history.

### Should Pass

- **SP-S1 [obj#3]**: `stats` block increments inline per-change (not only at session end).
  - Signal: `IncrementChangeStats` inline call sites.
  - Pass: inline increment present and `RollupSessionStats` either deleted or explicitly marked orphaned.

### Deal-Breakers

- **DB-S1 [obj#2 — atomic writes]**: `SaveState` must use tmp + fsync + rename. Non-atomic writes that can leave unparseable JSON brick the autonomous loop (violates vision substring `"Fail loud at session start, never silently mid-run"`).
  - Signal: SaveState implementation in `state.go`.
  - Instant FAIL: direct `os.WriteFile` or any write path that leaves state.json mid-write observable to a concurrent LoadState.

---

## Markdown Framework: `sudd/agents/` & `sudd/commands/`

Identified by: directory structure + framework_integrity_test regression guards.

### Must Pass

- **MP-F1 [obj#1 — agent count]**: `sudd/agents/` contains exactly 35 non-empty markdown files.
  - Signal: `ls sudd/agents/*.md | wc -l` plus `TestFrameworkIntegrity_NoZeroByteAgents`.
  - Pass: count == 35 AND all files non-empty.
  - Partial: count == 35 with one non-empty file missing a required section (e.g., `## ACTIVATION`).
  - Fail: count != 35 OR any agent file is 0 bytes.

- **MP-F2 [obj#1 — template matches live]**: Embedded template agent count equals live count.
  - Signal: `find sudd-go/cmd/sudd/templates/sudd/agents -name '*.md' | wc -l` vs `ls sudd/agents/*.md | wc -l`.
  - Pass: counts match (both 35 at v3.8.x).
  - Partial: templates > live (benign drift — live repo hasn't pulled latest).
  - Fail: templates < live (the v3.8.x self-wipe scenario).

- **MP-F3 [obj#1 — command-invoked agents exist]**: Every agent named in `sudd/commands/{macro,micro}/*.md` exists under `sudd/agents/`.
  - Signal: `TestFrameworkIntegrity_CommandInvokedAgentsExist`.
  - Pass: regression guard green.

### Should Pass

- **SP-F1 [obj#3 — tier consistency]**: Agent bodies with `**Tier**: X` hints match `sudd.yaml → agents.<name>.tier`.
  - Signal: `TestLintAgentTiers_LiveRepo`.
  - Pass: test green.

### Deal-Breakers

- **DB-F1 [obj#1 — no 0-byte agents]**: No agent file is 0 bytes.
  - Signal: `TestFrameworkIntegrity_NoZeroByteAgents`.
  - Instant FAIL: any 0-byte agent (the v3.8.x wipe scenario).

---

## Changes Workflow: `sudd/changes/{active,archive,dirty,stuck,inbox}/`

Identified by: directory tree.

### Must Pass

- **MP-C1 [obj#2 — no double-bookkeeping]**: No change id appears in more than one of `active/`, `archive/`, `dirty/`, `stuck/` simultaneously.
  - Signal: `comm -12` across `ls` of each dir (normalizing the `_DONE` suffix).
  - Pass: all sets disjoint.
  - Fail: any id present in two dirs.

- **MP-C2 [obj#4 — stuck artefacts]**: Every `stuck/<id>/` has `STUCK.md` AND `STUCK_REPORT.md` with a non-empty `TimeoutReason:`.
  - Signal: file-presence grep sweep.
  - Pass: 100% conformance.
  - Fail: any stuck dir missing STUCK.md, STUCK_REPORT.md, or with empty TimeoutReason.

- **MP-C3 [obj#4 — dirty artefacts]**: Every `dirty/<id>/` has `FOLLOWUP.md` AND `SUMMARY.md`.
  - Signal: file-presence check.
  - Pass: 100%.
  - Fail: any dirty dir missing either file.

- **MP-C4 [obj#2 — no zombie actives]**: No change in `active/` older than 24 hours lacks `log.md`.
  - Signal: `find sudd/changes/active -mindepth 1 -maxdepth 1 -type d -mmin +1440` + `test -f log.md`.
  - Pass: 100% of active dirs older than 24h have a log.md.
  - Partial: ≥80%.
  - Fail: <80%, OR any active dir older than 72h lacks log.md.

### Should Pass

- **SP-C1 [obj#3 — skimmable SUMMARY]**: Every `archive/<id>_DONE/SUMMARY.md` is skimmable in ~2 min, proxied by (a) file exists, (b) first non-blank line starts with `# `, (c) file ≤ 400 lines.
  - Signal: file presence + head -1 + wc -l.
  - Pass: 100% of archives conform.
  - Partial: ≥80%.
  - Fail: <80%.

- **SP-C2 [obj#3 — heading matches outcome]**: For every `archive/<id>_DONE/` or `stuck/<id>/` created after commit 7678260 (heading-rewrite fix), `grep -F '<id>' sudd/memory/lessons.md` returns a line under a `### [DONE]` (for archives) or `### [STUCK]` (for stucks) heading.
  - Signal: grep archive ids vs lessons.md headings.
  - Pass: 100% match for post-cutoff ids.
  - Partial: ≥80%.
  - Fail: <80%.

### Deal-Breakers

- **DB-C1 [obj#1 — no empty archives]**: No `archive/<id>_DONE/` dated after `/sudd-plan` was mandatory is missing `specs.md`.
  - Signal: find + test -f specs.md for archives newer than the plan-mandate commit.
  - Instant FAIL: a qualifying archive missing specs.md.

---

## Learning & Memory: `sudd/memory/` + `~/.sudd/learning/`

Identified by: files at those paths.

### Must Pass

- **MP-L1 [obj#3 — learn status works]**: `sudd learn status` exits 0 and prints a pattern count and a lesson count.
  - Signal: CLI run + stdout grep for `patterns:` and `lessons:`.
  - Pass: exit 0, both counts printed (may be 0 on a fresh repo — that's valid).
  - Fail: non-zero exit or missing count fields.

- **MP-L2 [obj#3 — archive → lesson]**: Every DONE or DONE_DIRTY archive has at least one matching heading in `sudd/memory/lessons.md`.
  - Signal: for each `archive/<id>_DONE/`, `grep -F '<id>' sudd/memory/lessons.md` returns ≥1 line.
  - Pass: 100%.
  - Partial: ≥80%.
  - Fail: <80%.

### Should Pass

- **SP-L1 — N/A-aware [obj#3]**: IF `~/.sudd/learning/patterns.md` exists, its line count ≥ `sudd/memory/patterns.md` promoted entries (cross-repo sync worked). If the file does not exist, criterion is **N/A** — absence of cross-repo history is not a defect on a fresh audit machine.
  - Signal: `ls ~/.sudd/learning/patterns.md` + `wc -l`.
  - Pass: file exists AND line count ≥ local promoted count, OR file does not exist (N/A).
  - Fail: file exists but line count < local promoted count (lost promotions).

---

## Snapshots & Recovery: `~/.sudd/snapshots/<slug>/`

### Must Pass

- **MP-N1 [obj#2 — snapshot per update]**: Every `sudd update` leaves a new tarball with mtime > update start time.
  - Signal: `find ~/.sudd/snapshots/<slug>/ -newer /tmp/update.start`.
  - Pass: ≥1 new tarball per update run.

- **MP-N2 [obj#2 — one-command recovery]**: `sudd restore-snapshot <repo> <timestamp>` completes non-interactively.
  - Signal: `echo "" | sudd restore-snapshot ...` exits 0 without prompting.

### Deal-Breakers

- **DB-N1 [obj#2 — retention safety]**: 30-day retention prune never deletes the most recent snapshot.
  - Signal: post-prune `ls ~/.sudd/snapshots/<slug>/` still contains the latest tarball.
  - Instant FAIL: pruning removes the most-recent snapshot.

---

## Live-Only Criteria (Not Scored — Framework Promises Tested Downstream)

These map to persona objectives but require a live environment:

- **LIVE-1 [obj#1]** — Real browser-based persona validation via persona-browser-agent. N/A for THIS repo (CLI framework, no HTTP surface). Must be tested in downstream consumer repos that have a frontend.
- **LIVE-2 [obj#2]** — Tier-auth-exhaustion behaviour (claude CLI quota depleted mid-session). Requires live LLM account state.
- **LIVE-3 [obj#1]** — MemPalace semantic-index correctness. Requires running MCP server.
- **LIVE-4 [obj#4]** — End-to-end recovery from a corrupted state.json under a real `sudd auto` session. Requires SIGKILL + re-run in wall-clock time.

Enumerated for completeness per the agent spec rule: "if an objective can't be observed without live browser, say so."

---

## Summary Score Bucket

Scoring algorithm (evaluated in order):

1. If `DealBreaker_fails >= 1` → **CRITICAL** (stop).
2. Else if `MP_fails >= 3` → **CRITICAL**.
3. Else if `MustPass_fails == 0 AND DB_fails == 0`:
   - If `ShouldPass_fails == 0` AND `DB_fails == 0` → **EXCELLENT**.
   - Else if `ShouldPass_fail_rate <= 50%` → **GOOD**.
   - Else → **NEEDS_WORK**.
4. Else (`MP_fails` is 1 or 2, `DB_fails == 0`) → **NEEDS_WORK**.

**Override clamp (from v1 critique issue #2)**: If `MP-G4 == Fail` OR `DB-S1 == Fail` (state.json not atomic), the maximum achievable band is **NEEDS_WORK**, regardless of other scores. Rationale: the whole framework's "fail loud" invariant depends on state.json being durable; declaring EXCELLENT or GOOD while that's broken would make the audit itself a liar.

---

## Current Scoring (git 2eb9211)

Today's observations mapped to the neutral thresholds above. This section is updated per audit run.

| ID | Verdict | Evidence | Trace |
|----|---------|----------|-------|
| MP-G1 | Pass | `go test ./... -v` exits 0 | local run |
| MP-G2 | Pass | 35 non-empty agents, standards.md non-empty | framework_integrity_test |
| MP-G3 | Pass | auto.go preflight gate present, blocks on blocker | auto.go preflight path |
| MP-G4 | **Fail** | `state.go:178` uses `os.WriteFile` directly | UC-1 in codeintel.json |
| MP-G5 | **Fail** | 10 SaveState sites use `fmt.Fprintf(os.Stderr, "Warning: ...")` + continue | UC-2 in codeintel.json |
| MP-G6 | **Fail** | `fleet` advertised in manifest:92 but no `AddCommand` in fleet.go | UC-3 / DRIFT-1 |
| MP-G7 | Pass (not re-tested) | doctor non-zero path present in internal/doctor/* | codeintel.json |
| SP-G1 | Partial | Some commands' help text names state files, coverage uneven | manual sweep |
| SP-G2 | Pass | both commands exit 0 on minimal state.json | manual run |
| SP-G3 | Pass | both <1s locally | local run |
| DB-G1 | Pass | `TestUpdateFromLiveSource_NeverTouchesVisionMD` present | installer tests |
| DB-G2 | Pass | snapshot.go + update flow verified | code review |
| DB-G3 | Pass | `AllowShrink` gate + refusal message | installer |
| MP-A1 | Pass | queue.go ShouldRunDiscovery path | code review |
| MP-A2 | **Fail** | `discovered_audit_handoff-validator-template-cleanup_01` zombie in active/ | UC-5 |
| MP-A3 | Pass | yaml ladder + runner.go dispatch | sudd.yaml + runner |
| MP-A4 | Pass | commit dbbcd9e enforced non-empty TimeoutReason | git log |
| SP-A1 | Pass | morning report present after recent sessions | auto-reports sample |
| SP-A2 | Partial | inline increment works but crash-safety gated on MP-G4 | UC-1 dependency |
| DB-A1 | Pass | auto preflight gate active | auto.go |
| DB-A2 | Pass | deferred finalize writes stop_reason | auto.go defer |
| MP-AU1 | Pass (on last run) | header present in previous report.md | sudd/audit/report-previous.md |
| MP-AU2 | Pass | discovered_audit_* entries present in active/ | ls sudd/changes/active |
| MP-AU3 | **Fail** | all subprocess errors wrap as `audit subprocess: %w` uniformly | UC-4 |
| SP-AU1 | **Fail** | no audit_test.go at CLI or internal/auto/ | UC-4 |
| MP-S1 | **Fail** | non-atomic write → crash produces unparseable JSON → LoadState fatal | UC-1 |
| MP-S2 | Pass | `map[string]json.RawMessage` preserves unknowns | state.go:82 |
| MP-S3 | Pass | recent state.json samples have non-empty stop_reason | grep sweep |
| MP-S4 | Pass | LoadState error → os.Exit(1) "parse state.json" | state.go load-error path |
| SP-S1 | Partial | inline increment works; RollupSessionStats orphaned with stale docstring | UC-6 |
| DB-S1 | **Instant FAIL** | state.go:178 uses `os.WriteFile` directly | UC-1 |
| MP-F1 | Pass | 35 non-empty agents | framework_integrity |
| MP-F2 | Pass | live 35 == template 35 | find sweep |
| MP-F3 | Pass | regression guard green | framework_integrity |
| SP-F1 | Pass | TestLintAgentTiers_LiveRepo green | test run |
| DB-F1 | Pass | no 0-byte agents | framework_integrity |
| MP-C1 | Pass | archive-clears-zombie-stuck-dirs_01 fix (commit f200569) keeps sets disjoint | git log |
| MP-C2 | Pass | 3/3 stuck dirs conform post-commit dbbcd9e | grep sweep |
| MP-C3 | Pass | single dirty/ entry conforms | ls |
| MP-C4 | **Fail** | zombie handoff-validator-template-cleanup_01 >24h without log.md | UC-5 |
| SP-C1 | Pass | archives have SUMMARY.md within 400 lines | wc -l sweep |
| SP-C2 | Partial | some older archives predate heading convention; post-7678260 ids match | grep check |
| DB-C1 | Pass | post-plan-mandate archives have specs.md | find + test |
| MP-L1 | Pass | `sudd learn status` exits 0 with counts | CLI run |
| MP-L2 | Partial | most archives have lessons entries; some older ones don't | grep sweep |
| SP-L1 | N/A | `~/.sudd/learning/patterns.md` absent on this audit machine | ls |
| MP-N1 | Pass | snapshot.go + update flow | code review |
| MP-N2 | Pass | restore non-interactive | snapshot.go |
| DB-N1 | Pass | retention preserves latest | prune logic |

**Tallies (git 2eb9211):**
- Must Pass fails: 7 (MP-G4, MP-G5, MP-G6, MP-A2, MP-AU3, MP-S1, MP-C4)
- Should Pass fails: 1 hard (SP-AU1) + 3 partials (SP-G1, SP-A2, SP-S1, SP-C2, MP-L2 partial) — treat partials as 0.5 each
- Deal-Breaker fails: 1 (DB-S1 = Instant FAIL, driven by state.go:178 non-atomic write)

**Band: CRITICAL** (DB-S1 Instant FAIL triggers rule 1; 7 MP fails would also trigger rule 2 independently; override clamp from MP-G4 also applies.)

---

## Revision Log

| # | Severity | Critique | Disposition | Change Made |
|---|----------|----------|-------------|-------------|
| 1 | CRITICAL | Pre-baked "Fail (CURRENT)" verdicts inside criteria | Accepted | Moved all "today" verdicts to `## Current Scoring` table; criteria now state only neutral thresholds |
| 2 | CRITICAL | DB-AU1 unfalsifiable (self-referential) | Accepted | Removed DB-AU1; added band-override clamp in `## Summary Score Bucket` |
| 3 | CRITICAL | DB-S1 was wrong-shape deal-breaker (regression guard for a behaviour nobody claimed); atomic-write failure itself is the real deal-breaker | Accepted | Demoted old DB-S1 to MP-S4 regression guard; added new DB-S1 for non-atomic-write Instant FAIL |
| 4 | IMPORTANT | MP-F2 tautology (required a test that didn't exist) | Accepted | Reframed MP-F2 as an executable `find`/`ls` count comparison |
| 5 | IMPORTANT | SP-C1 "readable in 2 min" not observable | Accepted | Replaced with three proxy signals (file exists, `# ` first heading, ≤400 lines) |
| 6 | IMPORTANT | SP-C2 lacked a mapping rule from archive id → heading | Accepted | Scoped to post-7678260 ids with explicit grep rule |
| 7 | IMPORTANT | SP-G3 1s threshold too tight | Accepted | Relaxed to 5s / 15s bands |
| 8 | IMPORTANT | MP-L1 / SP-L1 would false-fail on fresh audit machine with no `~/.sudd/` | Accepted | Reworded MP-L1 to accept zero counts; added N/A rule to SP-L1 |
| 9 | IMPORTANT | Missing doctor-preflight supplier coverage (MP-G3 only tested consumer) | Accepted | Added MP-G7 for `sudd doctor` itself exiting non-zero on check failure |
| 10 | MINOR | vision.md line numbers drift | Accepted | Replaced line-number cites with grep-able substrings |
| 11 | MINOR | "Format version 1.0" misleading | Accepted | Removed field from header |
| 12 | MINOR | Band arithmetic ambiguity | Accepted | Rewrote `## Summary Score Bucket` as an ordered algorithm |
