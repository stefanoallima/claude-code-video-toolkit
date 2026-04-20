# Persona: Stefano (Fallback End-User)

This is the FALLBACK persona used when no specific consumer is detected. In practice, the persona-detector and persona-researcher agents construct task-specific consumer personas dynamically.

**Role:** Technical Lead / Framework Owner
**Context:** Uses AI coding agents to build software autonomously. Returns expecting completed, documented, working code.

## Goals
1. Every task produces working code with clear documentation
2. The system runs autonomously without asking questions
3. When something fails, it retries with escalation — not a dead stop
4. Clear visibility into what was accomplished and what's still pending

## Frustrations
1. AI writes code that compiles but doesn't actually do anything useful
2. Systems that ask "what should I do?" instead of trying harder
3. Hours of compute time with nothing to show for it
4. Over-engineered solutions when something simple would work

## Success Criteria
> "I came back and the task is completed. The code works, it's documented, and I can see exactly what happened."

## Deal-Breakers
1. Empty/mock data in outputs — if the API returns `[]`, that's a fail
2. Code that doesn't run — syntax errors, missing imports
3. No tests — untested code is unfinished code

## Objectives
1. Review completed task output and verify working code — all files compile, tests pass, no placeholder data
   - Steps: Open the change directory, read the code, run tests, check for empty/mock returns
   - Success: All tests pass, code runs, outputs contain real data
2. Assess autonomous progress without intervention — system ran end-to-end without asking questions
   - Steps: Check log.md for session history, verify no BLOCKED or STUCK states, confirm commits exist
   - Success: Tasks completed autonomously, retry count reasonable (< 5 per task)
3. Understand what changed and why from the archive — clear summary of work done
   - Steps: Read SUMMARY.md, review git log, check lessons learned
   - Success: Can explain to stakeholders what was built in under 2 minutes
4. Identify stuck items and unblock them — clear diagnosis of what failed and why
   - Steps: Read stuck-history, check accumulated feedback, review error patterns
   - Success: Each stuck item has actionable human steps, not vague "needs investigation"

---

**NOTE:** For most tasks, the persona-detector will identify more specific consumers (e.g., "Frontend Developer consuming this API", "Crawler parsing these URLs"). Those dynamically constructed personas are more accurate than this static fallback.
