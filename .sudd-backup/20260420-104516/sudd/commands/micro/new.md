---
name: sudd:new
description: Create a new change proposal
phase: planning
micro: true
prereq: vision.md (auto-created if missing)
creates: sudd/changes/active/{id}/proposal.md
---

Create a new change proposal. First step in the planning phase.

**Input**: 
- `/sudd:new` — prompt for what to build
- `/sudd:new "description"` — create from description
- `/sudd:new {type}_{name}_{seq}` — create with specific ID

**Change ID format**: `{NNN}_{type}_{name}_{seq:02d}`
- NNN: global creation order (count all dirs in active/ + archive/ + stuck/, then +1, zero-padded to 3 digits)
- type: green | brown | fix | refact | discovered
- name: kebab-case description
- seq: two-digit sequence number

Examples:
- `001_green_auth_01` — first change ever, new auth system
- `005_brown_api-v2_01` — fifth change overall, API modification
- `012_fix_login-crash_01` — twelfth change, fix login crash

---

## ORCHESTRATOR CHECK

```bash
cat sudd/state.json
```

If no active change, proceed. If active change exists:
- Show current change
- Ask: "Replace with new change, or continue existing?"

---

## STEP 0: LOAD VISION CONTEXT (v3824)

Run `sudd vision context` and inject the output into your planning
scratchpad as the section `## Vision Context` BEFORE drafting the
proposal. This carries the user's North Star and the last 5 directional
choices into proposal generation.

Do NOT prompt the user about alignment — silent alignment is the success
condition. The session-end divergence detector handles real divergence
on its own (only fires after 3 consecutive DIVERGENT changes). When
`sudd vision context` outputs nothing (vision.md missing/empty), proceed
without context.

---

## STEP 1: UNDERSTAND SCOPE

If no description provided, ask:
> "What do you want to build? Describe the feature or fix."

From description, determine:
1. **Type**: green (new) | brown (modify) | fix | refact
2. **Name**: kebab-case from description
3. **Seq**: next available number in sudd/changes/

---

## STEP 2: CHECK FOR EXISTING

```bash
ls sudd/changes/active/
ls sudd/changes/archive/
```

Find highest seq for this name. Increment.

---

## STEP 3: DETERMINE IF ASK NEEDED

**Ask user if:**
- Change affects project scope heavily
- Change is very large (>5 major components)
- Vision is unclear

**Auto-create if:**
- Clear, focused change
- Within existing scope
- User provided good description

---

## STEP 4: CREATE PROPOSAL

Create directory:
```bash
mkdir -p sudd/changes/active/{change-id}/
```

Write `sudd/changes/active/{change-id}/proposal.md`:
```markdown
# Change: {change-id}

## Status
proposed

## Summary
{1-2 sentence description}

## Motivation
Why this change? What problem does it solve?

## Scope
What's included:
- 
- 

What's NOT included:
- 

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Dependencies
- None | List dependencies

## Risks
- Risk 1: mitigation
```

Create empty placeholder files:
- `specs.md` — to be filled
- `design.md` — to be filled
- `tasks.md` — to be filled
- `log.md` — execution log

---

## STEP 5: UPDATE STATE

Update `sudd/state.json`:
```json
{
  "active_change": "{change-id}",
  "phase": "planning",
  "last_command": "sudd:new"
}
```

---

## OUTPUT

```
Created: sudd/changes/active/{change-id}/

  proposal.md  ✓ (created)
  specs.md     ○ (empty, run /sudd:plan)
  design.md    ○ (empty, run /sudd:plan)
  tasks.md     ○ (empty, run /sudd:plan)

Next: Run /sudd:plan to create specs and design
```

---

## GUARDRAILS

- Don't create specs/design yet — that's /sudd:plan
- Always check for existing changes first
- Preserve seq numbering across archive
- Ask for scope-heavy changes, auto-create for focused ones
