---
name: sudd:audit
description: Whole-platform persona audit — validate the deployed product against all personas
phase: any
macro: true
---

Platform-wide persona audit. Validates the entire product against repo-level
personas, independent of any active change. Works on repos with all changes
completed, repos mid-development, or fresh repos after port.

**Input**:
- `/sudd:audit` — audit the full platform
- `/sudd:audit {persona}` — audit from a specific persona's perspective
- `/sudd:audit --url {url}` — audit against a deployed URL (not just dev server)
- `/sudd:audit --skip-browser` — skip live browser testing, code analysis only

---

Agent invocation follows `sudd/standards.md` → Agent Invocation.

---

## STEP 0: PERSONA SELF-HEALING

Before any validation, ensure personas exist and are enriched. This is what
makes audit work on ANY repo state — fresh port, all changes done, or empty.

```
Read: sudd/personas/*.md

CASE 1: No personas directory or no files
  → Dispatch(agent=persona-detector, scope=repo):
      Input: vision.md, codebase (full), README.md, package.json
      Output: sudd/personas/{detected}.md (shallow profiles)
  → Continue to enrichment below

CASE 2: Personas exist but are shallow (no ## Objectives section)
  → Flag for enrichment below

CASE 3: Personas exist and enriched (have ## Objectives)
  → Use as-is, skip enrichment

ENRICHMENT (for cases 1 and 2):
  For each persona in sudd/personas/:
    Check: does file have "## Objectives" section?
    If no:
      Dispatch(agent=persona-researcher):
        Input: sudd/personas/{name}.md, vision.md, codebase
        Output: enriched sudd/personas/{name}.md
        Key: must produce ## Objectives with 3-5 testable objectives

  Log: "Enriched {N} personas for audit."

VALIDATION:
  After enrichment, verify each persona has:
    □ ## Role (non-empty)
    □ ## Goals or ## What Makes Them Satisfied
    □ ## Deal-Breakers
    □ ## Objectives (3-5 with action verbs)
  If any persona fails validation after enrichment: log warning, proceed with available data.
```

---

## STEP 0b: INITIALIZE AUDIT DIRECTORY

```bash
mkdir -p sudd/audit/screenshots sudd/audit/browser-reports sudd/audit/validation-results
```

If a previous audit exists (`sudd/audit/report.md`), rename it for comparison:
```bash
mv sudd/audit/report.md sudd/audit/report-previous.md 2>/dev/null || true
```

Clean transient artifacts from previous run:
```bash
rm -f sudd/audit/*_codeintel.json sudd/audit/codeintel.json sudd/audit/manifest.json sudd/audit/audit.log
```

---

## STEP 1: CODEBASE SNAPSHOT

Get a ground-truth picture of what exists right now.

```
Check: sudd/codebase-manifest.json exists AND git SHA matches current HEAD?
  If yes: use cached manifest
  If no:
    Dispatch(agent=codebase-explorer, tier=low):
      Output: sudd/codebase-manifest.json

Read manifest. Extract:
  - All frontend routes (for browser testing)
  - All backend endpoints (for API validation)
  - Auth mechanism (for login flow testing)
  - Tech stack (to detect start command)
  - Test inventory (coverage baseline)
```

---

## STEP 2: CODE INTELLIGENCE (if applicable)

Follow the SAME pipeline as `gate.md` Steps 2a-2d, with these audit-specific overrides:

```
IF manifest shows frontend routes OR backend endpoints:

  KEY DIFFERENCES FROM GATE:
    - scope=audit on all dispatches (writes to sudd/audit/ not changes/{id}/)
    - No specs.md/design.md required — use vision.md + codebase-manifest.json instead
    - Feed manifest route list as input context to code-analyzers
      (avoids redundant endpoint scanning — manifest already found them)
    - Only one of FE/BE is required (skip missing side)

  2a. Dispatch(agent=code-analyzer-fe, scope=audit):
      Input: frontend source code + codebase-manifest.json (use api_surface.frontend_routes as guide)
      Output: sudd/audit/fe_codeintel.json
      (Skip if manifest shows no frontend routes)

  2b. Dispatch(agent=code-analyzer-be, scope=audit):
      Input: backend source code + codebase-manifest.json (use api_surface.backend_endpoints as guide)
      Output: sudd/audit/be_codeintel.json
      (Skip if manifest shows no backend endpoints)
      
      2a and 2b run IN PARALLEL.

  2c. Dispatch(agent=code-analyzer-reviewer, scope=audit):
      Input: fe/be_codeintel.json + codebase-manifest.json + personas/*.md + vision.md
      Output: sudd/audit/codeintel.json, sudd/audit/manifest.json, sudd/audit/rubric.md
      Note: uses vision.md + persona objectives as rubric source (not specs.md/design.md)

  2d. Rubric adversary loop (same as gate.md Steps 2d-2e):
      Dispatch(agent=rubric-adversary): critique → revision → critique → FINAL

  All outputs go to sudd/audit/ (not changes/ — audit is repo-scoped).
  
  CACHING: If sudd/audit/codeintel.json exists AND git SHA matches
  codebase-manifest.json.git_sha, skip Steps 2a-2d. Use cached intel.
```

---

## STEP 3: LIVE VALIDATION (unless --skip-browser)

```
IF --skip-browser: skip to Step 4

3a. START DEV SERVER (or use --url):
    If --url provided: use that URL, skip server start
    Else:
      Auto-detect start command:
        sudd.yaml → start_command (if set)
        package.json → scripts.dev or scripts.start
        Makefile → dev target
        Python: uvicorn/gunicorn/flask run detection
      Start server, health check, timeout 30s
      If server fails: log warning, skip browser testing, continue with code analysis

3b. BROWSER TESTING PER PERSONA:
    For each persona in sudd/personas/:
      persona-test \
        --persona "sudd/personas/{name}.md" \
        --url {url} \
        --objectives "{from persona ## Objectives}" \
        --manifest "sudd/audit/manifest.json" \
        --rubric "sudd/audit/rubric.md" \
        --codeintel "sudd/audit/codeintel.json" \
        --scope audit --max-steps 50 --timeout 120 \
        --screenshots-dir "sudd/audit/screenshots/{name}/" \
        --output "sudd/audit/browser-reports/{name}.json"

    Personas CAN run in parallel.

3c. CLEANUP:
    Kill dev server (if we started it), cleanup Chrome instances.
```

---

## STEP 4: PERSONA VALIDATION (always runs — with or without browser reports)

```
For each persona in sudd/personas/:

  Dispatch(agent=persona-validator, mode=audit):
    Input:
      - Persona research: sudd/personas/{name}.md
      - Browser report: sudd/audit/browser-reports/{name}.json (if exists)
      - Codebase manifest: sudd/codebase-manifest.json
      - Code intelligence: sudd/audit/codeintel.json (if exists)
      - Rubric: sudd/audit/rubric.md (if exists)
      - Scope: REPO (not change)
    Instruction:
      "You are auditing the ENTIRE platform, not a single change.
       Evaluate whether this persona can accomplish ALL their objectives
       using the product as it exists today.
       If browser report is available, use it as primary evidence.
       If no browser report, assess from code intelligence and manifest.
       Score holistically — partial implementations count as partial credit."
    Returns: {score, level, objectives_met[], gaps[], recommendations[]}

  [If UI] Dispatch(agent=ux-tester, mode=audit):
    Input: browser reports, manifest, design tokens
    Returns: {verdict, ux_issues[], accessibility_issues[]}

Log results to sudd/audit/validation-results/{name}.md
```

---

## STEP 5: GAP ANALYSIS & PROPOSAL GENERATION

```
Read all persona validation results.

For each persona:
  For each objective NOT met (or partially met):
    Create a gap entry:
      - Persona: {name}
      - Objective: {description}
      - Score: {objective score}
      - Evidence: {what's missing or broken}
      - Suggested fix: {what would satisfy this objective}

For each ux_issue with severity critical/high:
  Create a gap entry:
    - Type: ux_issue
    - Description: {issue}
    - Severity: {critical/high}

DEDUPLICATION:
  Check sudd/changes/active/ — skip gaps already covered by active proposals
  Check sudd/alignment-report.md — merge with existing gap entries if present

IF actionable gaps found:
  Dispatch(agent=task-discoverer, tier=top):
    Input: audit gaps + personas + codebase manifest
    Enhanced instruction: "Generate proposals from the audit gaps.
      Each unmet persona objective should become a proposal.
      Each critical UX issue should become a proposal.
      Reference the persona and objective in the proposal's ## Why section.
      Prefer S-size changes."
    Output: sudd/changes/active/discovered_*/ directories

  Log: "Audit generated {N} proposals from {M} gaps across {P} personas."
```

---

## STEP 6: AUDIT REPORT

Write `sudd/audit/report.md`:

```markdown
# Platform Audit Report

**Date**: {ISO-8601}
**Git SHA**: {current HEAD}
**Personas evaluated**: {N}
**Overall health**: {EXCELLENT / GOOD / NEEDS_WORK / CRITICAL}

## Persona Scores

| Persona | Score | Level | Objectives Met | Gaps |
|---------|-------|-------|---------------|------|
| {name}  | {N}/100 | {level} | {met}/{total} | {gap count} |

## Overall Health Criteria

- EXCELLENT: All personas >= 98, no critical gaps
- GOOD: All personas >= 80, no critical gaps
- NEEDS_WORK: Any persona 50-79, or important gaps
- CRITICAL: Any persona < 50, or critical gaps

## Per-Persona Details

### {Persona Name} — {score}/100 ({level})

#### Objectives
- [x] {Objective 1} — {evidence}
- [ ] {Objective 2} — {what's missing}
- [~] {Objective 3} — {partial, what needs work}

#### Gaps Found
1. **{gap title}** — {severity}
   - Evidence: {from browser report or code analysis}
   - Suggested proposal: {discovered_xxx_01 or "manual review needed"}

#### UX Issues
- {issue 1} — {severity}
- {issue 2} — {severity}

## Proposals Generated

| # | Proposal | Persona | Gap | Size |
|---|----------|---------|-----|------|
| 1 | discovered_xxx_01 | {name} | {gap} | S |

## Recommendations

1. {Highest priority recommendation}
2. {Second priority}
3. {Third priority}

## Previous Audit Comparison

{If previous audit/report.md exists, show delta:
  - Scores improved/declined per persona
  - Gaps closed since last audit
  - New gaps discovered}
```

---

## STEP 7: UPDATE STATE

```
Update sudd/state.json:
  last_audit_at: {ISO-8601}
  last_audit_score: {min persona score}
  last_audit_health: {EXCELLENT/GOOD/NEEDS_WORK/CRITICAL}
```

---

## CONFIGURATION

In `sudd/sudd.yaml`:

```yaml
audit:
  auto_after_n_changes: 5       # run audit after every N completed changes (0 = never)
  browser_testing: true         # enable live browser testing
  start_command: ""             # override dev server start command
  url: ""                       # override URL (skip dev server)
  enrichment_model: mid         # tier for persona enrichment during audit
```

---

## INTEGRATION WITH AUTO PIPELINE

`/sudd:auto` can trigger audit periodically:

```
After processing all changes in queue:
  Read state.json → last_audit_at, changes_since_last_audit
  Read sudd.yaml → audit.auto_after_n_changes

  If auto_after_n_changes > 0 AND changes_since >= threshold:
    Launch CLI subprocess: "/sudd:audit"
    Proposals generated by audit feed into next auto session's queue
```

---

## DIFFERENCES FROM /sudd:gate

| Aspect | /sudd:gate | /sudd:audit |
|--------|-----------|-------------|
| Scope | Single active change | Entire platform |
| Requires | Active change + tests passed | Nothing (self-heals) |
| Personas | Change-level (from changes/{id}/personas/) | Repo-level (from sudd/personas/) |
| Output | Pass/fail + retry | Report + proposals |
| Blocking | Blocks the change pipeline | Non-blocking, advisory |
| Phase | validate (strict) | any (no phase guard) |
| Browser testing | Required for UI changes | Optional (--skip-browser) |
| Code intel | Written to changes/{id}/ | Written to sudd/audit/ |

---

## OUTPUT

```
═══════════════════════════════════════
  SUDD PLATFORM AUDIT
═══════════════════════════════════════
  Personas:  {N} evaluated ({M} enriched during audit)
  Health:    {EXCELLENT / GOOD / NEEDS_WORK / CRITICAL}
  Scores:
    {persona-1}:  {score}/100 ({level}) — {met}/{total} objectives
    {persona-2}:  {score}/100 ({level}) — {met}/{total} objectives
  Gaps:      {N} found, {M} proposals generated
  Report:    sudd/audit/report.md
═══════════════════════════════════════
```

---

## DIRECTORY LIFECYCLE

### What gets committed (small, useful)
- `sudd/audit/report.md` — human-readable audit report
- `sudd/audit/rubric.md` — rubric used for validation

### What stays gitignored (large, transient)
- `sudd/audit/screenshots/` — browser screenshots (large binaries)
- `sudd/audit/browser-reports/` — raw JSON reports (regeneratable)
- `sudd/audit/fe_codeintel.json`, `be_codeintel.json`, `codeintel.json` — regeneratable
- `sudd/audit/manifest.json` — regeneratable
- `sudd/audit/validation-results/` — regeneratable
- `sudd/audit/audit.log` — subprocess log

### Cleanup
Before starting a new audit, delete previous transient artifacts:
```
rm -rf sudd/audit/screenshots/ sudd/audit/browser-reports/ sudd/audit/validation-results/
rm -f sudd/audit/*_codeintel.json sudd/audit/codeintel.json sudd/audit/manifest.json sudd/audit/audit.log
```
Keep `report.md` and `rubric.md` for comparison with the new run.

### .gitignore entries (auto-added during install)
```
sudd/audit/screenshots/
sudd/audit/browser-reports/
sudd/audit/*_codeintel.json
sudd/audit/codeintel.json
sudd/audit/manifest.json
sudd/audit/validation-results/
sudd/audit/audit.log
```

---

## GUARDRAILS

1. **Never skip persona enrichment.** Shallow personas produce shallow audits.
2. **Never fabricate browser evidence.** If browser testing fails/skips, score from code analysis only and note evidence gaps.
3. **Always compare to previous audit** if one exists. Regressions are more important than new gaps.
4. **Audit outputs go to sudd/audit/**, not changes/. Audit is repo-scoped, not change-scoped.
5. **Proposals from audit use `discovered_audit_` prefix** to distinguish from discovery-generated proposals.
6. **Don't block on missing tools.** If persona-browser-agent isn't installed, skip browser testing and continue with code analysis. Log what was skipped.
