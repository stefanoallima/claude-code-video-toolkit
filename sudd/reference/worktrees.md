# Worktree Management (Opt-In)

Manages git worktrees for parallel task execution. **Default is SEQUENTIAL** — opt in via `sudd.yaml` → `parallelization.mode: worktree`.

## When to Use

Only when parallelization mode is worktree AND batch has 2+ independent tasks. Skip when:
- Batch size = 1
- All tasks Effort: S (overhead exceeds benefit)
- Not in a git repo
- Tasks share Files: or SharedFiles:

## Frontend Constraint

At most **1 frontend-touching worktree** active at any time (prevents design consistency conflicts). Frontend = files matching `*.html, *.css, *.scss, *.less, *.tsx, *.jsx, *.vue, *.svelte, *.astro`. Queue additional frontend tasks for sequential execution.

## Create Worktree

```bash
mkdir -p .worktrees
git check-ignore -q .worktrees 2>/dev/null || {
  echo ".worktrees/" >> .gitignore
  git add .gitignore && git commit -m "chore: add .worktrees to gitignore"
}
git worktree add .worktrees/{change-id}-{task-id} -b sudd/{change-id}-{task-id}
```

Auto-detect project setup: `package.json` → npm install, `go.mod` → go mod download, `requirements.txt` → pip install.

## Merge Worktree

1. Rebase worktree branch against current base: `git rebase sudd/{change-id} sudd/{change-id}-{task-id}`
   - Conflict → `git rebase --abort` → mark for sequential re-run
2. Merge: `git merge sudd/{change-id}-{task-id} --no-ff`
3. Post-merge: run integration-reviewer (scope=change). Below EXEMPLARY → `git revert HEAD --no-edit`, re-run sequentially
4. Merge conflict → `git merge --abort`, mark for sequential re-run

## Cleanup

After merge: `git worktree remove .worktrees/{id} --force && git branch -d sudd/{id}`
After conflict: remove worktree, keep branch for sequential re-run.

## Status Tracking

Maintain in log.md:
```markdown
## Worktree Status
| Task | Path | Branch | Frontend | Status |
|------|------|--------|----------|--------|
| T01  | .worktrees/{change}-T01 | sudd/{change}-T01 | yes | active |
```

Status values: `active` → `merged` | `conflict → sequential` | `queued (frontend constraint)` → `active`
