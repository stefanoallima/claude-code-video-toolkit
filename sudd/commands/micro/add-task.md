---
name: "SUDD: Add Task"
description: Add a new change proposal to the SUDD backlog
category: SUDD
tags: [sudd, tasks, changes]
---

Add a new change proposal to the SUDD backlog.

**Input**: Description of what to build (after `/sudd:add-task`).

**Change ID Format**: `task_{name}_{seq:02d}`

**Steps**

1. Parse the user's description
2. Derive a kebab-case name (e.g., "build analytics dashboard" → `build-analytics-dashboard`)
3. Determine the next sequence number by scanning existing `sudd/changes/active/task_*` directories
4. Create change ID: `task_{name}_{seq:02d}`
5. Read `personas/` to identify the best matching persona (default: "default")
6. Create `sudd/changes/active/{id}/proposal.md`:

```markdown
# Change: [Title]

**ID:** {id}
**Size:** S
**Persona:** [persona-name]

## What
[What to build — from user's description]

## Why
[Why this matters to the persona — infer from persona goals]

## Acceptance Criteria
1. [Concrete, testable criterion]
2. [Another one]
3. [Another one]
```

7. Create `sudd/changes/active/{id}/tasks.md`:

```markdown
# Tasks: {id}

- [ ] [Task description derived from acceptance criteria]
```

8. Confirm:
```
Change proposal created: sudd/changes/active/{id}/
  - proposal.md
  - tasks.md
Persona: {persona-name}
Run /sudd:run to process it, or /sudd:run {id} for just this change.
```
