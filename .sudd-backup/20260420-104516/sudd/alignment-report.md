# Alignment Report

**Generated**: 2026-04-19T20:30:00Z
**Manifest**: 732edebbd45c44b6f727c164d5b8bd60e4359254
**Gaps found**: 12
**Skipped (already active/done)**: 3

## Critical Gaps

### GAP-001: `browser_use:` config section missing from shipped `sudd.yaml` but code/docs depend on it
- **Type**: integration_mismatch
- **Severity**: critical
- **Priority**: 1
- **Evidence (expected)**: `CLAUDE.md:168` lists `browser_use:` as a top-level `sudd.yaml` section: *"`browser_use:` — Persona-browser-agent config (provider, thresholds, scoring)"*. `sudd-go/internal/auto/runner.go:324` — code: *"Check if browser_use is enabled in sudd.yaml"* — parses `browser_use: / enabled: true`. `sudd-go/internal/auto/runner_test.go:609-736` exercises 4+ scenarios against real parse paths. `sudd/commands/micro/gate.md` and `sudd/agents/browser-test-auditor.md` both instruct readers to check `browser_use.enabled`.
- **Evidence (actual)**: `grep browser_use /Users/apple/GitHub/sudd2/sudd/sudd.yaml` and `.../templates/sudd/sudd.yaml` both return no matches — the section is absent from both the live config and the shipped template. Go code defaults to `enabled: false` on absence, which silently disables zero-trust browser-test verification (runner.go:247 *"Zero-trust: verify browser testing ran if browser_use is enabled"*).
- **Persona impact**: Stefano (default persona) Deal-Breaker #3 ("No tests — untested code is unfinished code") and Success Criterion ("The code works, it's documented"). Every `sudd auto` session today ships with the browser-test zero-trust net silently disarmed because the config key it looks for is missing from the yaml. Effectively equivalent to preflight silent-fail — the exact anti-pattern vision.md and MEMORY.md preflight note explicitly forbid.
- **Suggested change**: Add a `browser_use:` block to `sudd-go/cmd/sudd/templates/sudd/sudd.yaml` (and mirror to live `sudd/sudd.yaml`) with documented defaults (`enabled: true`, provider, thresholds). Extend `TestUpdateFromLiveSource` or add a new test asserting the section is present after `sudd update`.
- **Estimated size**: S
- **Dependencies**: none

### GAP-002: `sudd/AGENTS-SUDD.md` missing the CURRENT_STATE.md session-start instructions that sibling repos already receive
- **Type**: partial_impl
- **Severity**: critical
- **Priority**: 1
- **Evidence (expected)**: `sudd-go/cmd/sudd/templates/sudd/AGENTS-SUDD.md:107-135` ships a full `## Session-start read: sudd/CURRENT_STATE.md (v3.8.23+)` section with content-origin notes, refresh triggers, kill switch (`SUDD_STATE_DOC=off`), and the contract that CLI agents read this file FIRST. `sudd/codebase-manifest.json` lists `sudd/AGENTS-SUDD.md` as "framework (auto-refreshes)" authoritative for workflow cheatsheet.
- **Evidence (actual)**: `diff sudd/AGENTS-SUDD.md templates/.../AGENTS-SUDD.md` shows the 29-line `## Session-start read` block exists ONLY in the template. `sudd/AGENTS-SUDD.md` has zero mentions of `CURRENT_STATE`, `SUDD_STATE_DOC`, or the session-start read contract.
- **Persona impact**: Stefano Objective 2 ("Assess autonomous progress without intervention"). When the sudd2 repo's own Claude session wakes with cleared context, it does NOT know CURRENT_STATE.md exists, so it re-explores `changes/active/`, re-parses `state.json`, and re-reads archive SUMMARYs — burning the 15–30k tokens that v3.8.23 was explicitly built to save. Sibling repos get the fix on next `sudd update`; the source repo that dogfoods SUDD does not.
- **Suggested change**: Copy the `## Session-start read: sudd/CURRENT_STATE.md` block from `templates/sudd/AGENTS-SUDD.md` into `sudd/AGENTS-SUDD.md` so the live file matches the shipped template. Identical fix for `sudd/commands/macro/run.md` (missing the Step 0-first handoff read — see GAP-003).
- **Estimated size**: S
- **Dependencies**: none

### GAP-003: `sudd/commands/macro/run.md` missing "Step 0-first. Session-start handoff read" block present in the shipped template
- **Type**: partial_impl
- **Severity**: critical
- **Priority**: 1
- **Evidence (expected)**: `sudd-go/cmd/sudd/templates/sudd/commands/macro/run.md:23-38` ships a Step 0-first block instructing the orchestrator to read `sudd/CURRENT_STATE.md` BEFORE re-exploring the repo, with a trust-contract describing the `<!-- refreshed-at: ... -->` header. `SUMMARY.md` of `brown_v3823-current-state-doc_01_DONE` documents this step as part of the shipped feature.
- **Evidence (actual)**: `diff sudd/commands/macro/run.md templates/.../run.md | head -40` — live file has no corresponding block. Grep confirms zero occurrences of `CURRENT_STATE` in `sudd/commands/macro/run.md`.
- **Persona impact**: Stefano Success Criterion ("I can see exactly what happened"). The orchestrator in the sudd2 repo still does the slow-boot exploration every session. Doubly bad because sudd2 is the source repo used to validate SUDD changes — if the source-repo orchestrator doesn't exercise the new handoff path, regressions in that path won't be caught during development.
- **Suggested change**: Sync `sudd/commands/macro/run.md` to match `sudd-go/cmd/sudd/templates/sudd/commands/macro/run.md`. Add a CI test (or extend existing livesource test) asserting the two files are identical.
- **Estimated size**: S
- **Dependencies**: GAP-002 (logical coupling — same family of drift)

## Important Gaps

### GAP-004: `CLAUDE.md` architecture section undercounts agents (22 vs actual 35) and omits all v3.8.x Go subcommands
- **Type**: tech_debt
- **Severity**: important
- **Priority**: 2
- **Evidence (expected)**: Manifest `api_surface.cli_commands[]` enumerates 24 cobra subcommands (init, status, update, setup, auto, audit, metrics, doctor, diagnose, heal, fleet, triage, promote, list-snapshots, restore-snapshot, learn + 5 subs, vision + context, state). Manifest `structure.directories[].sudd/agents/` says `file_count: 35` and `api_surface.agents[]` lists 35 names. Vision.md section "Agent Roles (v3.8.x, 35 agents)" is authoritative.
- **Evidence (actual)**: `CLAUDE.md:58` — *"`agents/` — 22 agent instruction files"* (off by 13). `CLAUDE.md:71` — *"`cmd/sudd/main.go` — CLI entry point with `init`, `status`, `update`, `setup`, `auto`, `audit`, `learn` subcommands"* — omits 17 subcommands. `CLAUDE.md:67` labels Go CLI as "v3.6"; `sudd-go/Makefile:3` reads `VERSION := 3.8.9` and the most recent archive is `brown_v3824-*`. `README.md:151` also says "22 agent instruction files". No mention of `sudd vision`, `sudd state`, `CURRENT_STATE.md`, or the `internal/vision` / `internal/state` packages anywhere in CLAUDE.md.
- **Persona impact**: Stefano Objective 3 ("Understand what changed and why"). CLAUDE.md is the first file Claude reads on a fresh session; stale counts and missing subcommands mean the orchestrator may not know features exist, may not invoke them, and may reinvent them in future changes (fragmentation risk vision.md "Framework Priority" explicitly warns against).
- **Suggested change**: Update `CLAUDE.md` Architecture section to reflect v3.8.24: correct agent count (35), enumerate all cobra subcommands, add a bullet for `sudd/vision.md`/`sudd/CURRENT_STATE.md` first-class docs, refresh version label to v3.8.x. Same fix for `README.md:151`.
- **Estimated size**: S
- **Dependencies**: none

### GAP-005: `sudd/vision.md` "Known Open Work" section lists four already-shipped changes as still-open
- **Type**: tech_debt
- **Severity**: important
- **Priority**: 2
- **Evidence (expected)**: `sudd/vision.md:281-286` table lists `brown_v3817-resilience_01`, `brown_v3818-persona-autogen_01`, `brown_v3819-batch-review_01`, `brown_v3820-wipe-postmortem-deep-audit_01` as proposals "captured in active/ proposals".
- **Evidence (actual)**: `ls sudd/changes/archive/` shows all four as `*_DONE`: `brown_v3817-resilience_01_DONE`, `brown_v3818-persona-autogen_01_DONE`, `brown_v3819-batch-review_01_DONE`, `brown_v3820-wipe-postmortem-deep-audit_01_DONE`. `ls sudd/changes/active/` shows only the 3 `discovered_audit_*` proposals — none of the v3817–v3820 items. v3824 SUMMARY says vision.md becomes an "auto-append on archive" living log, so this stale table contradicts the file's own new contract.
- **Persona impact**: Stefano Objective 3 ("Understand what changed and why from the archive — clear summary of work done"). Reading vision.md to orient himself, Stefano sees four "open" items that actually shipped months ago — directly contradicts Success Criterion ("Can explain to stakeholders what was built in under 2 minutes"). Also undermines the v3824 feature (vision.md as living decision log) since the header part of the file says the opposite of the Current Path section.
- **Suggested change**: Delete the `## Known Open Work (captured in active/ proposals)` section from `sudd/vision.md` entirely — its job is now served by the `## Current Path` auto-append log added by v3824 and by the active/ dir itself. Or replace it with a pointer: "See `## Current Path` below and `sudd/changes/active/` for live open work."
- **Estimated size**: S
- **Dependencies**: none

### GAP-006: Stale `handoff-validator` references in shipped Claude templates re-introduce a deleted agent on every `sudd update`
- **Type**: integration_mismatch
- **Severity**: important
- **Priority**: 2
- **Evidence (expected)**: `sudd/sudd.yaml:101` — *"# Removed in v3.0: handoff-validator (subsumed by integration-reviewer)"*. `docs/superpowers/specs/2026-03-20-sudd-v3-autonomy-design.md:23` confirms the agent was deleted and its role moved to `integration-reviewer`. `ls sudd/agents/` — no `handoff-validator.md` exists.
- **Evidence (actual)**: `sudd-go/cmd/sudd/templates/.claude/commands/sudd/apply.md:86` ships *"Task(agent=handoff-validator):"* in the `/sudd-apply` slash command. `sudd-go/cmd/sudd/templates/.claude/commands/sudd/init.md:62` ships a checklist with *"`agents/handoff-validator.md`"*. `.claude/skills/sudd-init/SKILL.md:66` and `.claude/skills/sudd-port/SKILL.md:792,800` both reference the removed agent (the port skill even tells users to "remove handoff-validator" — a no-op in repos that already don't have it, but the instruction itself is now misleading).
- **Persona impact**: Stefano Frustration #1 ("AI writes code that compiles but doesn't actually do anything useful"). Target repos installing SUDD via `sudd update` receive `apply.md` and `init.md` that invoke a non-existent agent — the dispatch fails or hangs at retry loop time, consuming the exact "hours of compute time with nothing to show for it" Stefano calls out in Frustration #3. Also breaks framework integrity invariants: every change-invoked agent must exist per the v3.8.16 CI regression tests.
- **Suggested change**: Grep templates recursively for `handoff-validator`, remove the invocations in `apply.md`, remove from the `init.md` agent checklist, rewrite the `sudd-port` skill step 7 to say "Remove any lingering handoff-validator.md references in foreign frameworks" instead of "Update sudd.yaml: ... remove handoff-validator" (which the current sudd.yaml has already done). Add a template-integrity test that asserts `grep -r handoff-validator sudd-go/cmd/sudd/templates/` returns nothing.
- **Estimated size**: S
- **Dependencies**: none

### GAP-007: `sudd/memory/session-log.md` stub still exists alongside shipped `auto-reports/` — NOTE: covered by active proposal `discovered_audit_session-log-cleanup_01`; flagged here only because the proposal solves the file but not the reader references surfaced during this audit
- **Type**: tech_debt
- **Severity**: important
- **Priority**: 2
- **Evidence (expected)**: `discovered_audit_session-log-cleanup_01/proposal.md` "Acceptance" says *"Every reader reference to `sudd/memory/session-log.md` in agents, templates, and Go code either is removed or explicitly points to `auto-reports/`."*
- **Evidence (actual)**: `sudd/agents/monitor.md:108` still directs *"Write health reports to `memory/session-log.md`:"* and line 128 says *"Log each subagent's confidence to session-log.md"*. Grep surfaces the same directive in `sudd-go/cmd/sudd/templates/sudd/agents/monitor.md`. The proposal mentions monitor agent but the AC focuses on code-level references — flag this so task-discoverer expansions of the proposal include the agent edits explicitly.
- **Persona impact**: Same as `discovered_audit_session-log-cleanup_01`.
- **Suggested change**: Not a new change — extend the existing `discovered_audit_session-log-cleanup_01` tasks.md to explicitly include updating both `sudd/agents/monitor.md` and the template mirror so the monitor agent writes to `auto-reports/` going forward. No separate GAP/proposal needed.
- **Estimated size**: S (handled inside the existing active proposal)
- **Dependencies**: `discovered_audit_session-log-cleanup_01`

## Minor Gaps

### GAP-008: Manifest lists `cmd/sudd/fleet.go` under `cli_commands` but it registers no cobra subcommand
- **Type**: undocumented_code
- **Severity**: minor
- **Priority**: 3
- **Evidence (expected)**: `sudd/codebase-manifest.json` `api_surface.cli_commands[]`: *"{ name: "fleet", handler: "sudd-go/cmd/sudd/fleet.go", purpose: "fleet status/update helpers for multi-project rollups" }"*.
- **Evidence (actual)**: `grep rootCmd.AddCommand sudd-go/cmd/sudd/fleet.go` returns zero matches. `fleet.go` exposes `statusAllSiblingsRun` / `updateAllSiblingsRun` called from `statusCmd --all-siblings` and `updateCmd --all-siblings` respectively — not a standalone `sudd fleet` command. Manifest misrepresents the surface.
- **Persona impact**: Low-level inaccuracy in the ground-truth manifest itself. Affects future alignment reviews and discovery runs (they may hallucinate a nonexistent `sudd fleet` subcommand). No direct persona harm today but erodes trust in the manifest that every agent downstream reads.
- **Suggested change**: Update `codebase-explorer` to classify `fleet.go` as a "helper package" or demote its entry to `--all-siblings flag handlers` under `status`/`update` rather than a standalone command. One-line fix in codebase-explorer prompt logic.
- **Estimated size**: S
- **Dependencies**: none

### GAP-009: `sudd-go/cmd/sudd/auto_vision.go` has no dedicated test file; `vision.go` likewise untested
- **Type**: tech_debt
- **Severity**: minor
- **Priority**: 3
- **Evidence (expected)**: `sudd/codebase-manifest.json.test_inventory.source_files_without_tests_sample[]` calls out `sudd-go/cmd/sudd/auto_vision.go` and `sudd-go/cmd/sudd/vision.go` among untested CLI files. Test ratio 0.67 overall but both NEW v3.8.24 files on the critical session-end path have zero coverage. `state_cli.go` got a test (`state_cli_test.go`) in the same cycle, establishing a precedent for the pattern.
- **Evidence (actual)**: `ls sudd-go/cmd/sudd/ | grep -E "vision_test|auto_vision_test"` returns nothing. The files contain non-trivial logic: `auto_vision.go:24-64 maybeDirectionCheck` handles TTY detection, 60s timeout, editor shell-out, and error fail-soft — all of which are worth exercising. `vision.go:13-52` wires cobra subcommand and the `vision context` helper used by injection in `/sudd-new` and `/sudd-chat`.
- **Persona impact**: Stefano Deal-Breaker #3 ("No tests — untested code is unfinished code") applied to the direction-check feature itself. If `maybeDirectionCheck` regresses (e.g., wrong TTY detection, blocking forever in CI), `sudd auto` hangs every night with no test signal to catch it.
- **Suggested change**: Add `sudd-go/cmd/sudd/vision_test.go` covering the happy-path + missing-vision-file for `sudd vision context`. Add `sudd-go/cmd/sudd/auto_vision_test.go` using a fake `term.IsTerminal` and `io.Reader`/`Writer` pair to drive `maybeDirectionCheck` through the divergence-detected and not-detected branches. Existing test fixtures in `internal/vision/divergence_test.go` can be reused.
- **Estimated size**: M
- **Dependencies**: none

### GAP-010: `internal/auto/runner.go` at 769 lines is the repo's largest source file and concentrates too many responsibilities
- **Type**: tech_debt
- **Severity**: minor
- **Priority**: 3
- **Evidence (expected)**: CLAUDE.md architecture documents `runner.go` with a one-line purpose ("RunChange: launch CLI subprocess per change, detect outcome"). `sudd/codebase-manifest.json.code_quality.files_over_500_lines[]` lists 8 files ≥500 lines with `runner.go` at 769.
- **Evidence (actual)**: `runner.go` now holds: subprocess launch + timeout + interrupt wiring, browser-test zero-trust verification including inline `sudd.yaml` line-by-line parsing (lines 323-440), pre-archive check invocation, state.Refresh hook (line 656), vision.MigrateVisionMD plumbing, and `performArchival`. `runner_test.go` is 1164 lines — largest test file in the repo — and exercises 4 separate concerns, making TDD for any one of them expensive.
- **Persona impact**: Indirect — bleeds into Stefano Objective 1 ("working code with clear documentation") through maintenance friction. Every v3.8.x change touched runner.go; each touch risks a regression in an unrelated concern. Low user visibility today but rising.
- **Suggested change**: Extract three seams from `runner.go` into sibling files in `internal/auto/`: (a) `browseryaml.go` — the `isBrowserUseEnabled` / line-parse helpers + their tests; (b) `archival.go` — `performArchival` plus its `state.Refresh` and `vision.AppendForChange` hooks; (c) keep `runner.go` focused on subprocess lifecycle. No behavior change, just decomposition. Add a test that asserts the public API surface of `internal/auto/` is unchanged before/after.
- **Estimated size**: M
- **Dependencies**: none

### GAP-011: `sudd.yaml` has no schema/config keys for v3.8.23/v3.8.24 features (state refresh kill switch, vision migration policy)
- **Type**: tech_debt
- **Severity**: minor
- **Priority**: 3
- **Evidence (expected)**: v3824 SUMMARY describes env-var kill switches `SUDD_PRE_ARCHIVE_CHECKS=off`, `SUDD_STATE_DOC=off`. `sudd.yaml` already centralizes knobs for discovery/audit/auto/learning/mempalace/parallelization — the documented north-star in vision.md is that sudd.yaml is "the canonical authority" for runtime configuration.
- **Evidence (actual)**: `grep -n "SUDD_STATE_DOC\|SUDD_PRE_ARCHIVE_CHECKS\|state_doc\|pre_archive" sudd/sudd.yaml` returns nothing. The kill switches only exist as env vars, undocumented in yaml and invisible to `sudd doctor`. `CLAUDE.md` Configuration section (lines 157-168) lists sections but neither state nor vision are among them.
- **Persona impact**: Stefano Objective 2 ("autonomous progress without intervention — no silent side effects"). A user who sets `SUDD_STATE_DOC=off` in their shell to debug something will leave it there; the next autonomous run silently stops writing `CURRENT_STATE.md` and nobody notices until session-start handoff breaks. If the knob lived in yaml, `sudd doctor` could surface it.
- **Suggested change**: Add top-level yaml blocks: `state_doc: { enabled: true }` and `vision: { migrate_on_update: true, direction_check_timeout_seconds: 60 }`. Teach `internal/state/refresh.go` and `internal/vision/*` to prefer yaml value over env var when both are set. Add a `sudd doctor` probe that warns when either kill switch is engaged.
- **Estimated size**: M
- **Dependencies**: none

### GAP-012: `sudd-go/internal/porter/openspec.go` has 3 in-code TODOs that leak into generated output
- **Type**: partial_impl
- **Severity**: minor
- **Priority**: 3
- **Evidence (expected)**: Manifest `code_quality.todo_count: 3`, all in `internal/porter/openspec.go:160,189,238`. Porter promises to translate openspec changes into SUDD proposals that `task-discoverer` and humans can consume.
- **Evidence (actual)**: `sudd-go/internal/porter/openspec.go:189` — the generated `SUMMARY.md` literally contains the string `"- Files: TODO — openspec source didn't track target files"`. Line 238: `"tasks.md — translated from openspec flat-list to SUDD numbered format. Effort defaults to M, Files fields are TODO — review and adjust."`. Every imported openspec change in `sudd/changes/inbox/` carries this TODO forward into the triage UI.
- **Persona impact**: Stefano Objective 4 ("Identify stuck items and unblock them — clear diagnosis of what failed and why"). Browsing triaged inbox items, he hits `TODO` strings that aren't actionable without re-reading openspec source material. The porter's contract says "best-effort translate"; the output says "you still have to finish this for me". Acceptable for one-off imports but perennial because `consumer_insights_ai` has 71+ queued items (vision.md Known Open Work note).
- **Suggested change**: Either (a) upgrade `openspec.go` to actually extract target files from openspec's `proposal.md` code blocks with a regex pass, or (b) replace the `TODO` sentinel with a clearer banner `**Files**: _(openspec source didn't track — infer from tasks.md during planning)_` so humans + AI know this is expected-incomplete and not a bug.
- **Estimated size**: S
- **Dependencies**: none

## Skipped (Already Addressed)

- `discovered_audit_prearchive-checks-in-report_01`: covers the gap that v3.8.22 `internal/auto/checks.go` registry runs silently — morning report section proposed. Not reopened here.
- `discovered_audit_session-log-cleanup_01`: covers the stub file and template references. See GAP-007 which extends (not duplicates) this proposal's scope into `monitor.md`.
- `discovered_audit_state-json-session-fields_01`: covers `state.json` mode/last_command/last_run/design_gate_passed etc. populate-or-drop. Not reopened here.

## Summary

| Type | Critical | Important | Minor | Total |
|------|----------|-----------|-------|-------|
| Missing Feature | 0 | 0 | 0 | 0 |
| Undocumented Code | 0 | 0 | 1 | 1 |
| Partial Implementation | 2 | 1 | 1 | 4 |
| Integration Mismatch | 1 | 1 | 0 | 2 |
| Technical Debt | 0 | 2 | 3 | 5 |
| **Total** | **3** | **4** | **5** | **12** |
