---
name: sudd:port
description: Import artifacts from OpenSpec, BMAD, Superpowers, or Generic/PRD into SUDD structure
phase: inception
macro: true
---

Port existing artifacts from other frameworks into SUDD structure. Supports 4 framework types with auto-detection and multi-framework merge.

**Safety**: Original files are NEVER deleted or modified. Port creates copies only. All ported artifacts are tagged with their source for traceability.

**Input**:
- `/sudd:port` — auto-detect framework(s)
- `/sudd:port openspec` — from OpenSpec structure
- `/sudd:port bmad` — from BMAD structure
- `/sudd:port prd` — from Generic/PRD document
- `/sudd:port superpowers` — from Superpowers structure
- `/sudd:port merge` — force merge of all detected frameworks

---

## STEP 1: DETECTION

### 1a. Auto-detect frameworks

Scan the project root for signature files/directories. Check ALL of the following — a project may use multiple frameworks:

### Framework Priority (when multiple detected)
| Priority | Framework | Rationale |
|----------|-----------|-----------|
| 1 | OpenSpec | Most structured — has specs, changes, tasks |
| 2 | BMAD | Has epics, stories, acceptance criteria |
| 3 | Generic/PRD | Less structured but has requirements |
| 4 | Superpowers | Skills/patterns only, least SUDD-mappable |

When 2+ frameworks detected:
- Auto-select highest priority framework for primary port
- Display resolution with override options
- In merge mode (`/sudd:port merge`): port all, merge in priority order (highest first)
- Existing BMAD+PRD dedup rule (Guardrail 6) still applies

```
Check 1: openspec/project.md exists?
  → YES: add { framework: "openspec", confidence: "definite", evidence: ["openspec/project.md"] }

Check 2: .bmad-core/ directory exists?
  → YES: add { framework: "bmad", confidence: "definite", evidence: [".bmad-core/"] }

Check 3: .claude/skills/superpowers/ exists?
  → YES: add { framework: "superpowers", confidence: "definite", evidence: [".claude/skills/superpowers/"] }
  → NO: AGENTS.md AND reference/ both exist?
    → YES: add { framework: "superpowers", confidence: "probable", evidence: ["AGENTS.md", "reference/"] }

Check 4: PRD.md exists? (case-insensitive: PRD.md, prd.md, Prd.md)
  OR docs/prd.md exists?
  → YES, BUT .bmad-core/ also detected?
    → SKIP (BMAD already covers docs/prd.md — don't double-count)
  → YES, no .bmad-core/:
    → add { framework: "prd", confidence: "definite", evidence: ["PRD.md"] }
```

### 1b. Display results

```
Framework Detection
═══════════════════

  ✓ OpenSpec  (definite) — openspec/project.md  [PRIORITY: 1]
  ✓ BMAD      (definite) — .bmad-core/          [PRIORITY: 2]
  ✗ Superpowers
  ✗ Generic/PRD (covered by BMAD)

Detected: 2 frameworks
Resolution: Port OpenSpec (highest priority). BMAD artifacts available for merge.
Override: /sudd:port merge (combine all), /sudd:port bmad (use BMAD only)
```

### 1c. Ensure SUDD directories exist

Before any porting, create the target directory structure if missing:
```bash
mkdir -p sudd/specs sudd/personas sudd/memory sudd/changes/active
```
If `sudd/memory/lessons.md` doesn't exist, create it with header: `# SUDD Lessons Learned`

### 1d. Preview mapping

Before writing any files, display a summary of what WILL be created:
```
Port Preview
═════════════
Framework: BMAD (from .bmad-core/)

Will create:
  sudd/vision.md          ← docs/prd.md (purpose, goals sections)
  sudd/personas/           ← docs/prd.md (user persona sections)
  sudd/changes/active/     ← docs/stories/ (1 change, 4 tasks)
  sudd/memory/lessons.md   ← .bmad-core/data/technical-preferences.md

Proceed? (y/n)
```

If autonomous mode: proceed without confirmation.
If interactive: wait for user confirmation before writing.

### Dry-Run Mode

If `--dry-run` flag is present (parsed from input args: `/sudd:port --dry-run` or `/sudd:port {framework} --dry-run`):

1. Run ALL detection, decomposition, and mapping logic normally
2. Instead of writing files, collect all would-be writes into a preview list
3. Display the full preview:
   ```
   DRY RUN — No files will be written
   ═══════════════════════════════════

   Framework: {detected}

   Would create:
     sudd/vision.md          ← {source} ({N} sections)
     sudd/personas/          ← {source} ({N} personas)
     sudd/changes/active/    ← {source} ({N} changes, {M} tasks)
     sudd/specs/             ← {source} ({N} spec domains)
     sudd/memory/lessons.md  ← {source} ({N} conventions)

   Decomposition Confidence:
     Definite: {N} sections
     Probable: {N} sections
     Uncertain: {N} sections (would go to vision.md with warnings)

   Collisions:
     {file}: exists with {N} lines of custom content — would {merge|skip}

   No files were written. Remove --dry-run to execute.
   ```
4. Display confidence scoring results (if PRD decomposition ran)
5. Exit without writing any files

### 1e. Handle results

- **0 detected**: "No recognized framework found. Options: (1) Specify framework manually: `/sudd:port bmad`, `/sudd:port prd`, `/sudd:port openspec`, `/sudd:port superpowers`, (2) Start fresh with `/sudd:new`"
- **1 detected**: Auto-proceed with that framework
- **2+ detected**:
  - **Autonomous mode**: Auto-select highest priority framework (per priority table above), log: "Auto-selected {framework} (priority {N}). Other frameworks available for merge."
  - **Interactive mode**: Show recommendation with override:
    ```
    Multiple frameworks detected.
    Recommended: {highest-priority} (Priority {N} — {rationale})

    Options:
      1. Port from {highest-priority} only (recommended)
      2. Merge all into SUDD (combine artifacts, priority order)
      3. Port from {second} only
      ...
    ```
- **Explicit arg** (e.g., `/sudd:port bmad`): Skip detection, use specified framework
- **`/sudd:port merge`**: Force merge of all detected frameworks

### 1f. Git Checkpoint

Before writing any ported files (after detection, preview, and dry-run check):

1. Check if in a git repo: `git rev-parse --git-dir 2>/dev/null`
2. If yes:
   - Stage any unstaged changes: `git add -A`
   - Commit: `git commit -m "chore(sudd:port): pre-port checkpoint" --allow-empty`
   - Log: "Git checkpoint created — revert with: git reset --hard HEAD~1"
3. If not in git repo: log warning "Not in git repo — no rollback available"
4. If `--dry-run` mode: skip checkpoint entirely (no files will be written)

---

## STEP 2: PORT — OPENSPEC

### Map Structure
```
openspec/project.md                → sudd/vision.md
openspec/specs/{domain}/spec.md    → sudd/specs/{domain}.md
openspec/changes/{id}/proposal.md  → sudd/changes/active/{id}/proposal.md
openspec/changes/{id}/tasks.md     → sudd/changes/active/{id}/tasks.md
openspec/changes/{id}/design.md    → sudd/changes/active/{id}/design.md
openspec/changes/{id}/specs/       → merged into sudd/changes/active/{id}/specs.md
openspec/AGENTS.md                 → sudd/memory/lessons.md (extract conventions)
```

### Steps

1. **Vision**: Read `openspec/project.md`. Transform to `sudd/vision.md`:
   - Add `<!-- ported from: openspec [openspec/project.md] -->` at top
   - Map `# Project` → `# Vision`
   - Preserve all content

2. **Specs**: For each `openspec/specs/{domain}/spec.md`:
   - Copy to `sudd/specs/{domain}.md`
   - Add source tag

3. **Changes**: For each directory in `openspec/changes/`:
   - Check if `active/` or `archive/` — only port active
   - Create `sudd/changes/active/{id}/`
   - Map: proposal.md, tasks.md, design.md (direct copy with source tags)
   - **Delta spec flattening**: If `openspec/changes/{id}/specs/` exists:
     - Read each delta spec file
     - Look for `### ADDED`, `### MODIFIED`, `### REMOVED` section headers
     - If headers found: ADDED → new requirements, MODIFIED → updated requirements, REMOVED → "Out of scope"
     - If no delta headers found: copy content verbatim as requirements (treat as additive spec)
     - Merge all delta specs into single `sudd/changes/active/{id}/specs.md`
   - **Task state**: Preserve `[x]` and `[ ]` checkbox state

4. **Conventions**: If `openspec/AGENTS.md` exists:
   - Extract coding conventions, patterns, preferences
   - Append to `sudd/memory/lessons.md` as:
     ```markdown
     ### [PORTED] OpenSpec conventions — {date}
     **Source:** openspec/AGENTS.md
     {extracted conventions}
     ```

5. **Agent mappings** (note only):
   - `.opencode/command/opsx-*` → note in log, commands regenerated from sudd/
   - `.opencode/skills/` → note in log, skills regenerated from sudd/

---

## STEP 3: PORT — BMAD

### Map Structure
```
docs/prd.md                              → sudd/vision.md (purpose, goals)
                                         → sudd/personas/{persona}.md (user sections)
docs/architecture.md                     → sudd/changes/active/{id}/design.md
docs/epics/{name}/                       → sudd/changes/active/{epic}/proposal.md
docs/stories/{epic}/{story}/story.md     → task entries in tasks.md
docs/stories/{epic}/{story}/ACCEPTANCE_CRITERIA.md → success criteria
.bmad-core/data/technical-preferences.md → sudd/memory/lessons.md
.bmad-core/checklists/                   → noted in lessons.md
```

### Steps

1. **PRD Decomposition** (KEYWORD TABLE — also used by Generic/PRD in STEP 4): Read `docs/prd.md` and split by section headers. For each `##` or `###` header, check if ANY keyword below appears in the header text (case-insensitive):

   | Header keywords (case-insensitive) | Target |
   |---|---|
   | purpose, overview, vision, goals, objectives, mission, introduction | `sudd/vision.md` |
   | persona, user, target, icp, audience, customer, ideal customer | `sudd/personas/{name}.md` |
   | requirement, feature, scope, functionality, capability, specification | `sudd/changes/active/{id}/specs.md` |
   | architecture, technical, system, infrastructure, stack, technology | `sudd/changes/active/{id}/design.md` |
   | Any unmatched section | Append to `sudd/vision.md` (log warning: "Unmatched section '{header}' appended to vision.md") |

   #### Confidence Scoring for PRD Section Routing

   For each PRD section header, count keyword matches against the table above:

   | Confidence | Condition | Action |
   |------------|-----------|--------|
   | definite | 2+ keywords match a single target | Route to that target |
   | probable | 1 keyword matches a single target | Route to that target, log: "Probable match: '{header}' → {target} (keyword: {matched})" |
   | ambiguous | Keywords match 2+ targets equally | Route to first-priority target (specs > design > personas > vision), log warning with both targets |
   | uncertain | 0 keywords match | Route to vision.md, add to `## Ambiguous Sections` in log.md |

   #### Ambiguous Sections in log.md

   After decomposition, if any uncertain or ambiguous sections exist, append to log.md:

   ```markdown
   ## Ambiguous Sections (from PRD decomposition)
   | Section | Content Preview (first 50 chars) | Routed To | Confidence | Suggested Target |
   |---------|----------------------------------|-----------|------------|-----------------|
   | {header} | {preview...} | vision.md (default) | uncertain | {best guess or "unknown"} |
   ```

   In interactive mode: display this table and ask for corrections before writing.
   In autonomous mode: write with defaults, log for later review.

   Add `<!-- ported from: bmad [docs/prd.md] -->` at top of each output file.

2. **Persona Extraction**: From persona sections in prd.md:
   - Each distinct persona/user type → `sudd/personas/{kebab-name}.md`
   - Use the persona template (see STEP 6)
   - If no explicit personas found, create a single persona from project name + "User" (e.g., "VinumAI User") with role inferred from project type (e.g., "wine recommendation user")

3. **Epic → Change mapping**:

   **NNN (global creation order)**: Before creating any change directory, count all existing directories in `changes/active/`, `changes/archive/`, and `changes/stuck/`. NNN = that total + 1 (increment for each new change created in this session), zero-padded to 3 digits.

   - **If `docs/epics/` exists AND has subdirectories**: Each subdirectory → one SUDD change
     - Change ID: `{NNN}_brown_port-{epic-name}_01` (sanitize: lowercase, replace spaces/underscores with hyphens, strip non-alphanumeric except hyphens)
     - Epic description → `proposal.md`
   - **If `docs/epics/` exists but is empty** (or contains only README): treat as "doesn't exist", fall through
   - **If `docs/stories/` exists (no epics/)**:
     - With subdirectories: each subdir → one SUDD change
     - Flat (just .md files): all stories → tasks in one change
   - **If neither exists (or both empty)**: Create single change `{NNN}_brown_port-bmad_01` from PRD content

4. **Story → Task mapping**: For each story found:
   - `story.md` content → task description in `tasks.md`
   - `ACCEPTANCE_CRITERIA.md` → success criteria bullets under task:
     ```markdown
     - [ ] T{N}: {story title}
       - Criteria: {from ACCEPTANCE_CRITERIA.md}
       - Files: {inferred from story}
       - Effort: {S|M|L based on criteria count}
     ```
   - Story status (if tracked) → checkbox state

5. **Architecture**: If `docs/architecture.md` exists:
   - Copy to `sudd/changes/active/{id}/design.md`
   - Add source tag

6. **Technical Preferences**: If `.bmad-core/data/technical-preferences.md` exists:
   - Extract coding standards, tool preferences, patterns
   - Append to `sudd/memory/lessons.md`:
     ```markdown
     ### [PORTED] BMAD technical preferences — {date}
     **Source:** .bmad-core/data/technical-preferences.md
     {extracted preferences}
     ```

7. **Checklists**: If `.bmad-core/checklists/` exists:
   - Note checklist contents in `sudd/memory/lessons.md` for validation agents
   - Don't create separate files — condense into lessons

---

## STEP 4: PORT — GENERIC/PRD

### Map Structure
```
PRD.md (or docs/prd.md)       → sudd/vision.md (purpose + goals)
                               → sudd/personas/{persona}.md (user sections)
                               → sudd/changes/active/{id}/specs.md (requirements)
architecture_diagrams.md       → sudd/changes/active/{id}/design.md
tasklist.md                    → sudd/changes/active/{id}/tasks.md
AGENTS.md / CLAUDE.md / GEMINI.md → sudd/memory/lessons.md (coding conventions)
```

### Steps

1. **Find PRD**: Search for (case-insensitive): `PRD.md`, `prd.md`, `docs/prd.md`, `docs/PRD.md`

2. **PRD Decomposition**: Use the same KEYWORD TABLE and **Confidence Scoring** from STEP 3 (BMAD), subsection 1 "PRD Decomposition". For each `##`/`###` header, match keywords to route sections to vision/personas/specs/design. Apply the same confidence scoring (definite/probable/ambiguous/uncertain) and log ambiguous sections to log.md. The difference from BMAD: no epic/story structure to process.

   - If PRD has **no recognizable section headers** → treat entire document as `sudd/vision.md`
   - Create single change: `{NNN}_brown_port-prd_01`
   - Add `<!-- ported from: prd [PRD.md] -->` at top of each output

3. **Supplementary files** (if they exist):
   - `tasklist.md` → `sudd/changes/active/{id}/tasks.md`
     - Preserve checkbox state
     - Convert numbered lists to checkbox format if needed
   - `architecture_diagrams.md` → append to `design.md`
   - `architecture.md` → append to `design.md`
   - Add source tags to each

4. **Agent config conventions**: Check for `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` in project root (in that order). For each that exists:
   - Extract build commands, coding patterns, architectural notes
   - Skip any `<!-- SUDD:START -->` ... `<!-- SUDD:END -->` blocks (those are SUDD's own)
   - Append to `sudd/memory/lessons.md`:
     ```markdown
     ### [PORTED] Project conventions from {filename} — {date}
     **Source:** {filename}
     {extracted conventions}
     ```

---

## STEP 5: PORT — SUPERPOWERS

### Map Structure
```
AGENTS.md                                → sudd/vision.md
reference/*.md                           → sudd/memory/lessons.md (one entry per file)
.opencode/skills/superpowers/*.md        → noted in lessons.md (patterns for SUDD agents)
.claude/skills/superpowers/*.md          → noted in lessons.md (patterns for SUDD agents)
.claude/*plan*.md, *implementation*.md   → sudd/changes/active/{id}/proposal.md
.claude/*brainstorm*.md, *explore*.md    → appended to most recent proposal
```

### Steps

1. **AGENTS.md**: Read and transform to `sudd/vision.md`:
   - Add `<!-- ported from: superpowers [AGENTS.md] -->` at top
   - Structure the output as:
     ```markdown
     # Vision: {project name from first heading or filename}
     <!-- ported from: superpowers [AGENTS.md] -->

     ## Purpose
     {first paragraph or section of AGENTS.md}

     ## Technical Context
     {extract: language, framework, build tools, key dependencies}

     ## Conventions
     {extract: coding standards, naming conventions, patterns to follow}
     ```
   - If AGENTS.md has no clear structure, copy content verbatim under `# Vision`

2. **Reference docs**: For each `.md` file in `reference/`:
   - Read the file
   - Append to `sudd/memory/lessons.md`:
     ```markdown
     ### [PORTED] {filename without extension} — {date}
     **Source:** reference/{filename}
     **Type:** {categorize: "architecture" | "design-decision" | "pattern" | "spec" based on content}
     {file content, condensed to key points if >100 lines}
     ```
   - If `reference/` contains non-markdown files, skip them and note in log

3. **Skill patterns**: For each `.md` file in `.opencode/skills/superpowers/` or `.claude/skills/superpowers/`:

   #### Collision Detection (before writing agent notes)

   Before appending patterns to any agent file or lessons.md:

   1. **Check for existing SUDD agents**: For each skill that maps to a SUDD agent:
      - Read `sudd/agents/{agent-name}.md`
      - Check if file has been modified from default (compare first 10 lines to template)
      - If modified: COLLISION detected

   2. **Handle collision**:
      - **Interactive mode**: "Agent {name}.md has custom content ({N} lines). Merge Superpowers patterns? (y/n/diff)"
      - **Autonomous mode**: MERGE by appending Superpowers notes as a new section `## Superpowers Patterns (ported)` — never overwrite existing content
      - Log: "Collision: {agent}.md — merged (preserved {N} lines of existing content)"

   3. **Skip if identical**: If Superpowers skill maps to the same pattern already in the agent, skip silently

   Then proceed with skill mapping:
   - Read the skill file
   - Extract the skill name (from frontmatter `name:` field or filename)
   - Map known skill patterns to SUDD agent notes:
     - `*brainstorming*` → note in lessons: "Project uses structured brainstorming before implementation"
     - `*test-driven*` or `*tdd*` → note in lessons: "Project follows TDD — qa agent should enforce"
     - `*debugging*` → note in lessons: "Project uses systematic debugging — blocker-detector should follow"
     - Other skills → note name and purpose in lessons
   - Don't create separate files — condense all into one lessons.md entry:
     ```markdown
     ### [PORTED] Superpowers skill patterns — {date}
     **Source:** .claude/skills/superpowers/
     {list of skills and their implications for SUDD agents}
     ```

4. **Plan files**: Glob `.claude/` for files matching `*plan*.md` or `*implementation*.md`:
   - For each found file:
     - Sanitize filename for change ID: lowercase, replace spaces/underscores with hyphens, strip non-alphanumeric except hyphens
     - Create `sudd/changes/active/{NNN}_brown_port-{sanitized-name}_01/proposal.md`
     - Write: source tag + file content as proposal body
     - Create empty `specs.md`, `design.md`, `tasks.md`, `log.md` placeholders
   - If no plan files found: skip silently (this step is optional)

5. **Brainstorming results**: Glob `.claude/` for files matching `*brainstorm*.md` or `*explore*.md`:
   - For each found file:
     - Scan for `##` headers containing: "Decision", "Conclusion", "Selected", "Chosen", "Result", "Outcome"
     - If matching headers found: extract those sections only
     - If no matching headers: copy the full file content
     - Append extracted content to the most recently created change proposal under `## Brainstorming Context`
   - If no brainstorming files found: skip silently

6. **State**: Set phase to "inception" (superpowers projects typically need more planning than pre-specified frameworks)

---

## STEP 6: PERSONA EXTRACTION

**Execution order**: This step runs AFTER the framework-specific step (2, 3, 4, or 5) completes. It is a post-processing step that supplements any personas already created by the framework mapper. If the framework mapper already created personas (e.g., BMAD step 3.2), this step merges/deduplicates rather than recreating.

### Per-framework lookup locations

| Framework | Where to look | What to extract |
|-----------|---------------|-----------------|
| OpenSpec | `openspec/project.md` | Infer from project description |
| BMAD | `docs/prd.md` — User Personas / ICP sections | Names, roles, goals, pain points |
| Generic/PRD | `PRD.md` — Target Users / Personas sections | Names, roles, goals |
| Superpowers | `AGENTS.md` — project context | Infer from conventions |

### Persona file template

For each distinct persona found, create `sudd/personas/{kebab-name}.md`:

```markdown
# Persona: {Display Name}
<!-- ported from: {framework} [{source_file}] -->

## Role
{what this user does — their job title or function}

## Goals
- {what they want to achieve with this product}

## Pain Points
- {what frustrates them about current solutions}

## Context
{additional background: technical skill, frequency of use, environment}

## Deal-Breakers
- {things that would make them reject the product}
```

### Merge logic (multi-framework)
- Match personas by role name: case-insensitive exact match OR one name is a substring of the other (e.g., "Admin" matches "Administrator", "End User" matches "End User (Admin)")
- Merge attributes from multiple sources into one file — combine goals/pain-points lists, keep longest role description
- Note all source frameworks in source tag: `<!-- ported from: bmad [docs/prd.md], prd [PRD.md] -->`

### Fallback
If NO personas found in any source:
- Create `sudd/personas/end-user.md` with generic attributes inferred from project type
- Flag in log.md: "No personas found — created generic end-user. Run persona-researcher to enrich."

---

## STEP 7: MERGE STRATEGY (Multi-Framework)

When 2+ frameworks are being ported simultaneously:

### 7a. Vision merge
- Concatenate vision content from each framework
- Add framework headers: `## From OpenSpec`, `## From BMAD`
- Deduplicate identical sentences (exact match)
- Source tag each section

### 7b. Spec merge
- Append all specs (specs are additive, not deduplicating)
- Each spec section tagged with source
- Organize by domain if possible

### 7c. Task merge
- List all tasks from all sources
- Check for duplicates: compare task titles (text after `T{N}:`) — if two tasks share 3+ identical non-stopword tokens, merge into one
- Merged tasks note both sources in a comment
- Preserve most specific acceptance criteria (keep the longer criteria list)

### 7d. Design merge
- Concatenate design sections with framework headers
- If conflicting architecture decisions: note both, flag for human review

### 7e. Source tagging
Every section in every ported artifact gets:
```html
<!-- ported from: {framework} [{source_file}] -->
```

---

## STEP 8: FINALIZE

### 8a. State

Create/update `sudd/state.json` with ALL required fields:
```json
{
  "version": "1.0",
  "mode": "brown",
  "autonomy": "full",
  "active_change": "{first-change-id}",
  "phase": "build",
  "retry_count": 0,
  "imported_from": "{framework}",
  "tests_passed": false,
  "gate_score": null,
  "gate_passed": false,
  "stats": {
    "tasks_completed": 0,
    "tasks_stuck": 0,
    "tasks_blocked": 0,
    "total_retries": 0
  },
  "last_command": "sudd:port",
  "last_run": "{ISO-8601-timestamp}"
}
```
- `imported_from`: single framework name, or `"{fw1}+{fw2}"` if merged
- `phase`: "build" for OpenSpec/BMAD/PRD (have specs), "inception" for Superpowers-only
- `active_change`: set to the first (or only) change created during port
- If `state.json` already exists: preserve `stats` (tasks_completed, etc.) from existing file to avoid resetting progress counters on re-port. Overwrite all other fields.

### 8b. Sync

If sync script exists, run it to generate CLI commands:
```bash
# Check existence first
if [ -f sudd/sync.sh ]; then
  bash sudd/sync.sh
elif [ -f sudd/sync.bat ]; then
  sudd/sync.bat
else
  # Log warning: "sync script not found — run sudd installer or manually copy commands"
fi
```

### 8c. Summary log

Create `sudd/changes/active/{id}/log.md` if it doesn't exist (with header `# Log: {change-id}`), then append:
```markdown
## {date} — Ported from {framework}
- Vision: ✓ (from {source})
- Specs: {N} domains ported
- Changes: {N} active changes ported
- Personas: {N} extracted
- Lessons: {N} conventions captured
- Unmapped: {list of artifacts that couldn't be mapped}
```

### 8d. Post-Port Validation

After the summary log (8c), validate that nothing was silently dropped:

1. **Count source sections**: Read the original source document(s), count `##`/`###` headers
2. **Count ported sections**: Read all generated SUDD files, count `##`/`###` headers
3. **Compare**:
   - If ported >= source: PASS
   - If ported < source: check which source sections have no match
4. **Classify gaps**:
   - Source section contains requirement keywords (requirement, feature, must, shall, capability) → CRITICAL (requirement may be lost)
   - Source section is informational → WARNING (content dropped but not blocking)
5. **Report** in log.md:
   ```markdown
   ## Post-Port Validation
   - Source documents: {list}
   - Source sections: {N}
   - Ported sections: {M}
   - Coverage: {M/N * 100}%
   - Missing:
     - [CRITICAL] "{section name}" — contains requirements, not ported
     - [WARNING] "{section name}" — informational, not ported
   - Result: PASS (all requirements covered) | FAIL (requirements missing)
   ```
6. **On FAIL**: If autonomous mode, log and continue (rollback handled by Step 9 if >30% missing). If interactive, display and ask user whether to proceed or rollback.

### 8e. Design Token Extraction

After port completes, check if ported project has frontend files:

1. Glob for: `**/*.html, **/*.css, **/*.scss, **/*.tsx, **/*.jsx, **/*.vue, **/*.svelte`
   (exclude node_modules/, dist/, build/, .worktrees/)

2. If frontend files found AND `sudd/sudd.yaml` has no `design:` section (or entire line is commented):
   - Scan CSS/SCSS files for:
     - Color declarations (hex, rgb, hsl, oklch) → extract dominant palette
     - Font-family declarations → extract typography
     - Spacing/gap patterns → identify spacing scale
   - If tokens found: add commented-out design section to sudd.yaml with discovered values
   - If no tokens found: add commented-out template with warning

3. Output appended to sudd.yaml:
   ```yaml
   # Design context (auto-detected from ported frontend files)
   # design:
   #   brand_colors:
   #     primary: "{discovered or 'oklch(60% 0.15 250)'}"
   #   typography:
   #     heading_font: "{discovered or 'system-ui'}"
   #     body_font: "{discovered or 'system-ui'}"
   #   design_system: "minimalist"
   ```

4. Log: "Frontend files detected — design config template added to sudd.yaml (commented out, review needed)"
5. If sudd.yaml doesn't exist: create minimal one with the design section only
6. If sudd.yaml already has an active (uncommented) `design:` section: skip entirely, log "design section already configured"

### 8f. Iterative Review (interactive mode only)

If NOT autonomous mode AND decomposition produced any "probable" or "uncertain" sections (from confidence scoring in Steps 3/4):

1. Display decomposition summary:
   ```
   PRD Decomposition Review
   ════════════════════════
   Definite: {N} sections (auto-routed)
   Probable: {N} sections (review recommended)
   Uncertain: {N} sections (needs your input)

   Probable:
     "{header}" → {target} (keyword: "{matched}")

   Uncertain:
     "{header}" → vision.md (default)

   Accept decomposition? (y/n/edit)
   ```

2. If "edit": let user reassign sections by number
3. If "y": proceed with current routing
4. If "n": abort, user can re-run with manual overrides

In autonomous mode: skip this step entirely — use defaults.

---

## STEP 9: ERROR HANDLING

During porting, handle these edge cases gracefully — log warnings, don't abort:

| Situation | Action |
|-----------|--------|
| Source file exists but is empty | Skip file, log warning: "Skipped empty file: {path}" |
| Source file is not valid markdown (binary, corrupted) | Skip file, log warning: "Skipped non-markdown file: {path}" |
| Directory exists but is empty (e.g., `docs/epics/` with no subdirs) | Treat as "doesn't exist", use fallback path |
| Permission error reading a file | Log warning, continue with other files |
| A section fails to port but others succeed | Continue porting remaining sections, log partial failure |
| `sudd/` target file already exists | Overwrite it (port is idempotent) |
| Multiple unmatched PRD sections dumped to vision.md | Log each: "Unmatched section '{header}' → vision.md" so user can review |

### Rollback on Critical Failure

If post-port validation (Step 8d) reports CRITICAL failures AND more than 30% of requirements are missing:

1. **Interactive mode**: "Port validation failed — {N} requirements missing ({percentage}%). Rollback to pre-port checkpoint? (y/n)"
2. **Autonomous mode**: auto-rollback
3. Rollback: `git reset --hard HEAD~1` (to pre-port checkpoint from Step 1f)
4. Log: "Port rolled back — {reason}. Original files restored."
5. If no git checkpoint exists (not in git repo): log error "Cannot rollback — no git checkpoint. Manual cleanup required."

After ALL porting steps complete, run validation:
1. Check `sudd/state.json` is valid JSON with `mode: "brown"` and `imported_from` set
2. Check `active_change` points to an existing directory in `sudd/changes/active/`
3. Verify at least one persona exists in `sudd/personas/` (or fallback was created)
4. Verify `sudd/vision.md` is non-empty
5. List any warnings accumulated during porting in the output

---

## OUTPUT

### Single framework
```
Ported from {Framework}:
  ✓ vision.md       (from {source_file})
  ✓ {N} specs       → sudd/specs/
  ✓ {N} changes     → sudd/changes/active/
  ✓ {N} personas    → sudd/personas/
  ✓ {N} conventions → sudd/memory/lessons.md
  ⚠ {N} unmapped    (see log.md)

State: brown mode, {phase} phase
imported_from: {framework}

Review the ported artifacts, then:
  /sudd:status  — check what was created
  /sudd:run     — start autonomous workflow
```

### Multi-framework merge
```
Merged from {N} frameworks:
  OpenSpec:     ✓ vision, 3 specs, 1 change
  BMAD:         ✓ vision, 2 personas, 1 epic→change

  Combined:
    ✓ vision.md  (merged from 2 sources)
    ✓ 3 specs
    ✓ 2 changes
    ✓ 2 personas
    ✓ 5 conventions

State: brown mode, build phase
imported_from: openspec+bmad

Review the ported artifacts, then:
  /sudd:status  — check what was created
  /sudd:run     — start autonomous workflow


---

## MODE: UPGRADE (SUDD version migration)

**Input**: `/sudd:port --upgrade`

Upgrades existing SUDD installation from older version to current.

### Process

1. **Detect current version**: Read `sudd/state.json` → `sudd_version`
   - If missing: assume v2.0
   - If current: "Already at v{current}. Nothing to upgrade."

2. **Copy new agent files** (5 new):
   - micro-persona-generator.md
   - wiring-checker.md
   - macro-wiring-checker.md
   - integration-reviewer.md
   - micro-persona-validator.md

3. **Update existing agent files** (6 updated):
   - persona-detector.md, persona-researcher.md, decomposer.md
   - coder.md, contract-verifier.md, persona-validator.md

4. **Remove deprecated** (1):
   - handoff-validator.md

5. **Copy updated commands**:
   - apply.md, plan.md, gate.md, test.md (micro)
   - run.md, port.md (macro)

6. **Update standards.md**: Add task-level scoring section

7. **Update sudd.yaml**: Add new agents, remove handoff-validator

8. **Update state.json**: Add `sudd_version: "3.0"`

9. **Migrate active changes**:
   For each change in `sudd/changes/active/`:
   a. Stamp proposal.md with `sudd_version: 3.0`
   b. Create `tasks/` directory structure
   c. Run micro-persona-generator for existing tasks
   d. Run persona-detector + persona-researcher for change personas

10. **Run sync**: Execute `sudd/sync.sh` to propagate to CLI agent folders

11. **Report**:
```
SUDD Upgrade Complete: v{old} → v3.0

  New agents: 5
  Updated agents: 6
  Removed agents: 1
  Updated commands: 6
  Active changes migrated: N

  New capabilities:
  - Per-task micro-personas with 100/100 validation
  - Wiring checks (per-task + per-change)
  - Integration review (dual-scope)
  - Version stamping on all changes
```

### v3.0 → v3.1 Upgrade Steps

If detected version is 3.0:

1. Add 2 new agent files (ux-architect.md, ux-reviewer.md)
2. Update agents: micro-persona-generator (add rubric), micro-persona-validator (rubric-based), qa (tests from rubric), context-manager (subagent context), monitor (confidence+cost)
3. Update sudd.yaml: add execution field to all agents, add model_mapping, add adaptive_planning, add ux-architect + ux-reviewer
4. Update commands: apply.md (subagent dispatch, parallel squad, canary, selective re-validation, confidence, disagreement), run.md (same + checkpointing + UX architect), gate.md (parallel personas), plan.md (UX architect step)
5. Update standards.md: rubric scoring, confidence protocol, v3.1 state schema
6. Convert commands to skills: .claude/commands/sudd/ → .claude/skills/sudd-*/
7. Remove OpenSpec skills: .claude/skills/openspec-*/
8. Migrate state.json for active changes:
   - Change micro_score (int) → micro_verdict (string): 100 → "PASS", null → null
   - Add rubric_results: {} (empty, populated on next validation)
   - Add confidence: null
9. Stamp sudd_version: "3.1"
10. Run sync.sh to propagate

Report:
```
SUDD Upgrade Complete: v3.0 → v3.1

  New agents: 2 (ux-architect, ux-reviewer)
  Updated agents: 5
  Updated commands: 4
  
  New capabilities:
  - Rubric-based validation (CONTRACT/ERROR/EDGE/BEHAVIORAL criteria)
  - Subagent isolation for 13 agents
  - UX design architecture + code review
  - Parallel validation squad dispatch
  - Canary validation on first task
  - Orchestrator checkpointing
  - Confidence scores on all verdicts
  - Commands converted to Claude Code skills
```

---

## GUARDRAILS

1. **Never delete original files** — port creates copies only
2. **Preserve completion state** — done tasks stay done, checked items stay checked
3. **Note unmapped artifacts** — don't silently drop content; list in log.md
4. **Set mode to brown** — ported projects always have existing context
5. **Run sync after port** — ensure CLI commands are available
6. **BMAD + PRD dedup** — if `.bmad-core/` detected, don't also count `docs/prd.md` as Generic/PRD
7. **Source tag everything** — every ported section needs `<!-- ported from: {framework} [{file}] -->`
8. **Extract real personas** — don't just use generic fallbacks; extract from actual source docs
9. **Case-insensitive PRD detection** — check PRD.md, prd.md, Prd.md, docs/prd.md
10. **Idempotent** — running port twice overwrites SUDD artifacts cleanly. For `lessons.md`: before appending, check if a `### [PORTED]` section from the same source already exists — if so, replace it instead of duplicating
11. **Graceful degradation** — missing optional files (tasklist.md, architecture.md, checklists/) produce warnings in log, not errors. Port continues with available files. See STEP 9 error handling table for all edge cases
12. **No silent data loss** — if a PRD section can't be classified, append to vision.md with a logged warning rather than dropping it
13. **Framework priority resolution** — when 2+ frameworks detected, auto-select highest priority (OpenSpec > BMAD > PRD > Superpowers). In interactive mode, show recommendation with override option
14. **Dry-run safety** — `--dry-run` must never write files, create git commits, or modify state. It runs all logic and displays results only
15. **Git checkpoint before writes** — always create a pre-port checkpoint commit before writing ported files. Skip only if `--dry-run` or not in a git repo
16. **Rollback on critical failure** — if post-port validation reports CRITICAL + >30% missing, auto-rollback in autonomous mode, ask in interactive mode
17. **Confidence scoring on all PRD decomposition** — both BMAD (Step 3.1) and Generic/PRD (Step 4.2) must use confidence scoring. Log all probable/uncertain/ambiguous matches
18. **Agent collision detection** — never silently overwrite existing agent files with Superpowers patterns. Merge by appending, or ask in interactive mode
19. **Design token extraction is best-effort** — regex-based, not a CSS parser. Always commented out — user must review and uncomment
