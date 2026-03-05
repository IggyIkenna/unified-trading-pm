---
name: PM–Codex–Code Version Tracking Implementation
overview: How to implement and enforce per-file version headers across PM, Codex, and service repos so that drift is detectable as a failing unit test, not a manual review.
related_plan: pm_codex_drift_zero_architecture (team member plan — covers CI/CD infrastructure layer)
doc_version: "1.0"
codex_version: "0.1.0"
last_modified: "2026-03-04"
status: proposed
---

# Version Tracking: Implementation and Enforcement Guide

**Companion to:** `alignment-version-tracking-design.md` (design + pros/cons)
**Builds on top of:** PM–Codex Drift Zero Architecture (CI/CD infrastructure phases 0–7)
**Scope:** The per-file header system — what to write, where, how to enforce it

---

## How the Two Plans Fit Together

The team member's Drift Zero plan handles the **infrastructure layer**:

- Manifest sync (Phase 0)
- CI cloning Codex/PM as siblings (Phase 5)
- Per-repo validators wired into quality-gates (Phase 6)
- Diff checker using validators (Phase 7)

This plan handles the **provenance layer** — the layer that records _why_ a file was changed and _which spec_ it was built against. Both are required. Drift Zero gives us the plumbing; this plan gives us the signal.

```
Drift Zero Plan                    This Plan
─────────────────                  ─────────────────────────────────
manifest sync ──────────────────►  manifest[repo] == doc.service_version
CI clones codex ────────────────►  check-alignment-drift.py runs in CI
run_validators.py ──────────────►  ALIGN-06 (doc header validator) added
quality-gates.sh ───────────────►  header check step added
```

---

## Part 1: The Header Standard

### Decision: Simplest Possible Format

All open questions from the design doc resolved as follows:

| Question                   | Decision                                                            | Reason                                     |
| -------------------------- | ------------------------------------------------------------------- | ------------------------------------------ |
| `doc_version` format       | Semantic integer pair: `"1.2"`                                      | Simple to bump, agent-readable, ordered    |
| Header location in code    | Module-level comment block, top of file                             | No docstring pollution, no extra files     |
| Enforcement strictness     | Warning in CI for first 30 days, then blocking                      | Avoids hard stop during rollout            |
| Cross-cutting pattern docs | Reference `section_version` of the codex section                    | Same mechanism, different reference target |
| Retroactive coverage       | Agent pass on all service docs first; code files only going forward | Prioritise specs over implementation       |

---

### Header Format: Codex Doc (`.md` files)

Every codex doc that describes a specific service, library, or component gets a YAML front-matter block at the top:

```markdown
---
doc_version: "1.0"
codex_version: "0.1.0"
last_modified: "2026-03-04"
describes: market-data-processing-service
status: stable
---
```

**Fields:**

| Field           | Type            | Description                                                                                    |
| --------------- | --------------- | ---------------------------------------------------------------------------------------------- |
| `doc_version`   | `"MAJOR.MINOR"` | Version of this specific document. Bumped manually when content changes meaningfully.          |
| `codex_version` | `"X.Y.Z"`       | Version of `unified-trading-codex` at the time of last edit. Read from codex `pyproject.toml`. |
| `last_modified` | `"YYYY-MM-DD"`  | Date of last substantive edit.                                                                 |
| `describes`     | string          | The repo, service, or component this doc is about. Matches key in `workspace-manifest.json`.   |
| `status`        | enum            | `stable` \| `draft` \| `deprecated`                                                            |

**When to bump `doc_version`:**

- Content changes (schema updated, pattern changed, new section added) → bump minor: `1.0` → `1.1`
- Doc substantially rewritten or restructured → bump major: `1.1` → `2.0`
- Typo or formatting fix only → no bump
- `codex_version` bumps (whole codex releases) → update `codex_version` field, no `doc_version` bump

---

### Header Format: Code Files (`.py`, `.ts`, `.sh`, `.yaml`)

Any file changed as part of a task that was created from a codex spec doc gets a header comment block immediately after any shebang line and before imports:

**Python:**

```python
# codex-ref: 02-data/batch/per-service/market-data-processing-service.md
# doc-version: 1.1
# codex-version: 0.1.0
# last-modified: 2026-03-04
```

**TypeScript:**

```typescript
// codex-ref: 02-data/batch/per-service/market-data-processing-service.md
// doc-version: 1.1
// codex-version: 0.1.0
// last-modified: 2026-03-04
```

**Shell:**

```bash
#!/usr/bin/env bash
# codex-ref: 06-coding-standards/quality-gates.md
# doc-version: 2.3
# codex-version: 0.1.0
# last-modified: 2026-03-04
```

**YAML (service config):**

```yaml
# codex-ref: 04-architecture/batch-live-symmetry.md
# doc-version: 1.0
# codex-version: 0.1.0
# last-modified: 2026-03-04
```

**Fields:**

| Field           | Description                                                                                                                                                                 |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `codex-ref`     | Path to the codex doc, relative to `unified-trading-codex/`. This is the spec this file was built against.                                                                  |
| `doc-version`   | The `doc_version` of that codex doc at the time this file was last meaningfully edited. Must match the current `doc_version` in the referenced doc to pass alignment check. |
| `codex-version` | Version of the whole codex at time of edit.                                                                                                                                 |
| `last-modified` | Date of last substantive edit to this file.                                                                                                                                 |

---

### Header Format: PM Task/Plan Files

Every AI task file in `plans/ai/` gets a header block:

```markdown
---
spec_doc: 02-data/batch/per-service/market-data-processing-service.md
spec_doc_version: "1.1"
codex_version: "0.1.0"
created: "2026-03-04"
status: active
---
```

This records what version of the spec the task was written against. If the spec is updated while a task is still active, the mismatch is detectable before an agent starts work.

---

### Which Files Do and Do NOT Get Headers

**YES — add header:**

- All codex docs under `per-service/`, `per-service-live/`, `per-service-batch/` directories
- Code files changed as part of a spec-driven task
- PM task/plan files in `plans/ai/`
- Service config files changed to implement a codex pattern

**NO — do not add header:**

- `__init__.py`, `conftest.py`, `setup.py`
- `pyproject.toml`, `Dockerfile`, `cloudbuild.yaml`
- Cross-cutting utility files not tied to a specific spec (e.g. `utils/date_utils.py`)
- Test files (tests are assertions about code, not implementations of specs)
- Auto-generated files
- `workspace-manifest.json` itself

**Rule:** If the file exists because a specific codex spec says it should exist or what it should contain — it gets a header. If it is infrastructure glue, it does not.

---

## Part 2: The Enforcement Script

### `scripts/validation/check-alignment-drift.py`

Location: `unified-trading-pm/scripts/validation/check-alignment-drift.py`

This script is the enforcement engine. It runs five checks, each producing pass/fail/warning:

```
CHECK 1: header_present
  All codex per-service docs have YAML front-matter with required fields.
  Severity: BLOCKING

CHECK 2: doc_version_match
  For each code file with a codex-ref header:
    code_file.doc_version == referenced_codex_doc.doc_version
  If they differ: the code was built against a superseded spec.
  Severity: BLOCKING (after 30-day grace period)

CHECK 3: codex_version_match
  code_file.codex_version == unified-trading-codex pyproject.toml version
  Severity: WARNING (codex bumps infrequently, lag is acceptable for one minor)

CHECK 4: doc_version_monotonic
  When a codex doc is edited, new doc_version > old doc_version (from git diff).
  Prevents version going backwards accidentally.
  Severity: BLOCKING

CHECK 5: plan_spec_current
  For each active plan in plans/ai/:
    plan.spec_doc_version == spec_doc.doc_version
  If they differ: agent is about to work against a stale plan.
  Severity: WARNING (blocking only when agent task is about to start)
```

**Output:**

```
✓ PASS  header_present       47/47 codex service docs have valid headers
✗ FAIL  doc_version_match    2 files reference stale doc version
          market_data_processor.py → expects doc 1.1, spec is now 1.2
          batch_handler.py       → expects doc 1.1, spec is now 1.2
✓ PASS  codex_version_match  all files reference codex 0.1.0 (current)
✓ PASS  doc_version_monotonic no version regressions detected
⚠ WARN  plan_spec_current    1 active plan references stale spec
          TASK_MDP_SCHEMA.md → written against doc 1.1, spec is now 1.2

Exit code: 1 (blocking failures present)
```

---

### Integration as Validator ALIGN-06

The script is also packaged as a validator that integrates with the existing `run_validators.py` infrastructure in `unified-trading-codex/validators/`:

```python
# unified-trading-codex/validators/alignment/doc_header_validator.py

@ValidatorRegistry.register("ALIGN-06")
class DocHeaderValidator(BaseValidator):
    """
    Validator: Doc–Code Version Alignment

    Checks that code files built from codex specs reference the current
    doc_version of those specs. Detects stale implementations.
    """
    # Runs checks 1–4 above
    # check_5 (plan_spec_current) runs in PM repo only
```

This means `run_validators.py --category alignment` automatically includes the header check alongside the existing ALIGN-01 through ALIGN-05 validators.

---

## Part 3: Where Enforcement Runs

### 3.1 In `unified-trading-codex` quality gates

Add one step to `unified-trading-codex/scripts/quality-gates.sh`:

```bash
# Step: Doc header alignment check
echo "--- Checking doc-code version alignment ---"
python3 scripts/validate-alignment.py \
    --checks header_present,doc_version_monotonic \
    --fail-on blocking \
    || exit 1
```

The codex QG only runs checks 1 and 4 (what it owns). Checks 2 and 3 run in the service repos.

### 3.2 In per-service `quality-gates.sh`

Phase 6 of the Drift Zero plan already adds `run_validators.py` to service quality gates. ALIGN-06 is added to that same call:

```bash
# Already added by Drift Zero Phase 6:
python3 "${CODEX_ROOT}/validators/run_validators.py" \
    --scope service \
    --repo-type "${REPO_TYPE}" \
    --fail-on P0,P1

# ALIGN-06 is automatically included — no extra line needed
# once the validator is registered in the validators/ directory
```

### 3.3 As Step 0 of every agent task (pre-flight gate)

Add to `plans/tasks/cursor/TEMPLATE.md`, before any agent work begins:

```bash
# STEP 0: Verify alignment before starting work
cd unified-trading-pm
python3 scripts/validation/check-alignment-drift.py \
    --scope "${SPEC_DOC}" \
    --checks plan_spec_current \
    --exit-on-blocking

# If this fails: the spec changed since the plan was written.
# Update the plan header to reference the new doc_version before proceeding.
```

### 3.4 In the Codex merge gate (Drift Zero Phase 3)

When Codex CI runs `plan-incorporation validator`, it also runs the header check:

```bash
python3 validators/run_validators.py --validator ALIGN-06
```

This prevents merging codex docs that have a `doc_version` bump without the `last_modified` date being updated.

---

## Part 4: Cursor Rule for Agent Compliance

A cursor rule ensures all agents automatically include headers when editing spec-driven files. This is the single most important enforcement point because it makes compliance the path of least resistance.

**Rule location:** `.cursor/rules/core/codex-ref-header.mdc`

**Rule content (key excerpt):**

```
RULE: When editing a file as part of a task that was created from a codex spec doc,
add or update the codex-ref header block at the top of the file.

WHEN TO ADD:
- Editing a service module because a codex per-service doc was updated
- Implementing a new feature specified in a codex architecture doc
- Any file whose purpose is defined by a specific codex document

HEADER FORMAT (Python):
# codex-ref: <path-relative-to-unified-trading-codex>
# doc-version: <current doc_version from the spec doc's front-matter>
# codex-version: <current version from unified-trading-codex/pyproject.toml>
# last-modified: <today's date YYYY-MM-DD>

TO FIND doc_version:
  Read the YAML front-matter of the referenced codex doc.
  The doc_version field is the value to use.

TO FIND codex-version:
  Read unified-trading-codex/pyproject.toml → version field.

NEVER:
  Skip the header when the file is spec-driven
  Use an outdated doc-version (always read from the current doc front-matter)
  Add the header to __init__.py, conftest.py, pyproject.toml, Dockerfile
```

---

## Part 5: Rollout Order

This plan is sequenced to depend on Drift Zero phases but can partially run in parallel:

| Step                                                                        | Depends on             | Agent scope               | Time    |
| --------------------------------------------------------------------------- | ---------------------- | ------------------------- | ------- |
| **S1** Add YAML front-matter to all codex per-service docs                  | Nothing                | 1 agent, lobster workflow | 2–3 hrs |
| **S2** Write `check-alignment-drift.py`                                     | Nothing                | 1 agent                   | 2–3 hrs |
| **S3** Write `validators/alignment/doc_header_validator.py` (ALIGN-06)      | S2, Drift Zero Phase 6 | 1 agent                   | 1–2 hrs |
| **S4** Add cursor rule `codex-ref-header.mdc`                               | S1                     | 1 agent                   | 30 min  |
| **S5** Add check to `unified-trading-codex/scripts/quality-gates.sh`        | S2                     | 1 agent                   | 30 min  |
| **S6** Add Step 0 to `plans/tasks/cursor/TEMPLATE.md`                       | S2                     | 1 agent                   | 30 min  |
| **S7** Add `codex-ref` headers to existing service code files (retroactive) | S4 (rule exists first) | 1 agent per service tier  | 4–6 hrs |

S1–S4 can run in parallel. S5–S6 depend on S2. S7 runs after S4.

**Minimum viable enforcement (S1 + S2 + S4 + S5):** 1 day of agent work. Gives you: headers on all codex docs, drift check script, cursor rule for all future work, check running in codex CI. Everything after that is incremental hardening.

---

## Part 6: Living With It — Agent Workflow

Once live, this is what an agent's workflow looks like when given a task:

**Step 0 (pre-flight):**

```
Read: plans/ai/TASK_MDP_SCHEMA_UPDATE.md
→ spec_doc: 02-data/batch/per-service/market-data-processing-service.md
→ spec_doc_version: "1.1"

Read: unified-trading-codex/02-data/batch/per-service/market-data-processing-service.md
→ doc_version: "1.2"  ← MISMATCH

Action: STOP. The spec was updated since this task was created.
Notify: "Task references doc v1.1 but current spec is v1.2. Update plan header or re-read spec before proceeding."
```

**During edit:**

```
Editing: market-data-processing-service/market_data_processor.py

Add at top of file:
# codex-ref: 02-data/batch/per-service/market-data-processing-service.md
# doc-version: 1.2       ← current version from spec front-matter
# codex-version: 0.1.0   ← from unified-trading-codex/pyproject.toml
# last-modified: 2026-03-04
```

**When updating a codex doc:**

```
Editing: unified-trading-codex/02-data/batch/per-service/market-data-processing-service.md
→ Changed: added new output schema field

Update front-matter:
  doc_version: "1.2"   ← bumped from 1.1
  last_modified: "2026-03-04"
  codex_version: "0.1.0"  ← unchanged (whole codex not bumped)
```

**Pre-commit:**

```
quality-gates.sh runs check-alignment-drift.py
→ header_present: PASS
→ doc_version_monotonic: PASS (1.1 → 1.2)
→ Exit 0 — allowed to proceed
```

---

## Summary

The system has three moving parts, each with a single job:

| Part                                  | Job                                            | Owned by               |
| ------------------------------------- | ---------------------------------------------- | ---------------------- |
| YAML front-matter on codex docs       | Declare the current spec version               | Agent editing the doc  |
| `codex-ref` header on code files      | Declare which spec version the code implements | Agent editing the code |
| `check-alignment-drift.py` + ALIGN-06 | Assert that those two agree                    | quality-gates.sh + CI  |

When all three are in place: a stale implementation is a failing test. There is no way to merge code that was built against a superseded spec without the check catching it.

---

_When making changes to this document, bump `doc_version` and update `last_modified`._
