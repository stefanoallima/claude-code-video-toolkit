---
name: sudd:test
description: Run tests and validate implementation
phase: validate
micro: true
prereq: sudd:apply (code implemented)
creates: test results
---

Run tests and validate the implementation against specs.

**Input**:
- `/sudd:test` — run all tests for active change
- `/sudd:test {change-id}` — test specific change
- `/sudd:test unit` — unit tests only
- `/sudd:test integration` — integration tests only

---

## ORCHESTRATOR CHECK

```bash
cat sudd/state.json
```

If no active change:
- Find changes with code but not validated
- Auto-select or ask

---

## PRE-TEST CHECK (v3.0)

Before running tests, verify task-level validation status:

```
Read state.json → task_progress
For each task:
  If status == "in_progress": WARN "Task {id} not yet validated — test results may be incomplete"
  If status == "blocked_failed": WARN "Task {id} blocked after {retries} attempts — related tests may fail"
```

Include micro-persona validation results in the test report as additional evidence for the gate.

---

## STEP 0: TEST FRAMEWORK DETECTION (runs once, result saved to sudd.yaml)

Before running any tests, detect or confirm the test command:

**Priority order:**
1. `sudd/sudd.yaml` has `test_command` field (user override) → use it directly
2. `Makefile` exists with a "test" target → `make test`
3. `*_test.go` files exist anywhere in repo → `go test ./...`
4. `package.json` exists with `scripts.test` defined → `npm test`
5. `test_*.py` or `*_test.py` files exist → `pytest`
6. None of the above found → QA agent creates test infrastructure as first task

After detection, save the result to `sudd/sudd.yaml` so subsequent runs skip detection:

```yaml
test_command: "go test ./..."
```

If `sudd/sudd.yaml` already has `test_command`, skip detection entirely and use the saved value.

---

## STEP 1: READ CONTEXT

Read:
- `sudd/changes/active/{id}/specs.md` — what to test
- `sudd/changes/active/{id}/tasks.md` — what was implemented
- `sudd/memory/lessons.md` — avoid known issues

---

## STEP 2: RUN TESTS

### Unit Tests
```bash
pytest tests/unit/ -v --tb=short
```

### Integration Tests
```bash
pytest tests/integration/ -v --tb=short
```

### Coverage
```bash
pytest --cov=src --cov-report=term-missing
```

---

## STEP 3: ANALYZE RESULTS

```
Tests: {change-id}

  Unit Tests:
    ✓ test_user_creation .......... passed
    ✓ test_user_validation ........ passed
    ✗ test_user_deletion .......... FAILED
      AssertionError: Expected 204, got 500

  Integration Tests:
    ✓ test_full_flow .............. passed

  Coverage: 78% (target: 80%)

Summary: 2/3 passed, 1 failed
```

---

## STEP 4: FIX FAILURES

For each failing test:

```
Task(agent=blocker-detector):
  ERROR: {test failure}
  Classify: bug | spec_issue | test_issue

If bug:
  → Task(agent=coder): fix the bug
  → Re-run test
  → Max 2 quick fixes before escalation

If spec_issue:
  → Update specs.md
  → Re-run test

If test_issue:
  → Fix test
  → Re-run
```

---

## STEP 5: UPDATE STATE

Update `sudd/changes/active/{id}/log.md`:
```markdown
## {timestamp}
- Tests run: N passed, M failed
- Coverage: X%
- Issues: {list}
```

---

## OUTPUT

```
Tests: {change-id}

  Unit: 5/5 passed ✓
  Integration: 3/3 passed ✓
  Coverage: 82%

All tests passing!

If running autonomously (from /sudd:run): proceed directly to gate validation. Do NOT stop.
If running standalone: Next → /sudd:gate
```

### Update State
After ALL tests pass:
Update sudd/state.json:
  - tests_passed = true
  - last_command = "sudd:test"

---

## GUARDRAILS

- Run all test types, not just unit
- Track coverage, flag if < 80%
- Fix bugs before proceeding to gate
- Don't skip failing tests
- Log all results
