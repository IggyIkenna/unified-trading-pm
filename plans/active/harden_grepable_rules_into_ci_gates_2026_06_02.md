---
title: Harden grep-able CLAUDE.md rules into CI gates (UTC datetimes · cloud-SDK direct-import ban · fallback-imports)
parent_epic: plan_hygiene_master
priority: P2
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
created: 2026-06-02
locked_by: live-defi-rollout
locked_since: 2026-06-02
related_plans:
  - plans/active/agent_context_and_memory_hygiene_2026_06_02.md
  - plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md
  - plans/epics/plan_hygiene_master.md
---

# Harden grep-able CLAUDE.md rules into CI gates

> **`execution_scope: local-only`** — a teammate (Harsh or Ikenna) runs this deliberately + tests it; it is **not**
> auto-dispatched to orchestrator workers (it edits the QG/ruff TEMPLATE that rolls out to all 22 repos — sensitive,
> needs a human to verify the gate + grep fire correctly before rollout).

## Why

Behavioral rules in `cursor-configs/CLAUDE.md` depend on an agent **reading + remembering** them — fragile. This very
session (2026-06-02) **lost 8 such rules** when CLAUDE.md was condensed; they only came back via a manual before/after
audit. A **CI gate enforces a rule regardless of whether the prose survives or an agent skims past it** — that's the
durable form. The principle: _anything grep-able or count-able should be a gate, not a paragraph._

**Pre-audit (done 2026-06-02)** — grepped the QG infra to see what's already enforced vs not:

- **Already gated** (do NOT duplicate): `os.getenv` (`scripts/quality-gates-base/base-service.sh`), inline `gs://`
  (`scripts/quality_gates/check_inline_bucket_uri.py`), `category=` kwarg, `pipeline_mode`/`source=` at record-calls,
  `record_empty` reason closed-set, architectural-ratchets (UI-18 etc.), import-patterns, dep-pin drift, + ~35 more.
- **NOT gated → this plan** (verified zero hits in `scripts/quality_gates` / `quality-gates-base` / `validation`):
  UTC-datetime ban, `from google.cloud` / `import boto3` direct, `try/except ImportError` fallback.

## Scope

**IN (3 confirmed grep-able candidates):**

1. **UTC datetimes** — `datetime.now()` (naive) / `datetime.utcnow()` / `datetime.today()` banned; require
   `datetime.now(timezone.utc)`.
2. **No direct cloud SDK** — `from google.cloud import …` / `import boto3` banned; require `get_storage_client()` /
   `get_secret_client()` from unified-cloud-interface.
3. **No `try/except ImportError` fallback** — no fallback-import shims (hardens the existing
   `.cursor/rules/standards/no-empty-fallbacks.mdc`, which is NOT CI-enforced).

**OUT (assessed 2026-06-02, deliberately excluded — record the rationale so this isn't re-litigated):**

- **`pickle`** — the sanctioned replacement **joblib uses the pickle protocol under the hood**, and there are legit
  framework-internal uses (multiprocessing, some libs); a blunt `import pickle` grep is false-positive-prone for little
  gain. Keep as a prose rule + code review.
- **Summary docs** (`*_SUMMARY.md`/`READY_TO_*`/`COMPLETION_*`) — filename heuristic, near-zero harm; not worth a gate.
- **Backward-compat shims** (`_old.py`/`# deprecated`) — needs judgment about what _is_ a shim; not cleanly grep-able.

## Phases

### Phase 1 — UTC datetimes via ruff `flake8-datetimez` (no custom code)

- [ ] [INFRA] P2. Add `DTZ` to `[tool.ruff.lint] select` in the **ruff config TEMPLATE** (codex/06-coding-standards
      SSOT + the `pyproject.toml` template — **NEVER** edit per-repo copies; SSOT-first then rollout). Relevant codes:
      `DTZ005` (naive `datetime.now()`), `DTZ003` (`utcnow()`), `DTZ001/002/006/007/011/012` as appropriate. Pin the
      exact code set in the plan when landed.
- [ ] [TEST] P2. Prove it FIRES: temp file with `datetime.now()` → ruff reports `DTZ005`; `datetime.now(timezone.utc)` →
      clean. Capture the before/after ruff output in this plan.
- [ ] [INFRA] P2. Count existing violations workspace-wide; if many, **baseline-ratchet** them (so green repos don't
      break on rollout); if few, fix in-place. Decide + record the count + decision here.

### Phase 2 — cloud-SDK direct-import ban via ruff `flake8-tidy-imports` banned-api (`TID251`, no custom code)

- [ ] [INFRA] P2. Add `[tool.ruff.lint.flake8-tidy-imports.banned-api]` to the template banning `google.cloud` + `boto3`
      with the message "use `get_storage_client()` / `get_secret_client()` from unified-cloud-interface". **Exempt
      unified-cloud-interface's own internals** (it legitimately imports the SDKs) — per-package `per-file-ignores` or a
      path exclusion.
- [ ] [TEST] P2. Prove it FIRES: `from google.cloud import storage` → `TID251`; `import boto3` → `TID251`; sanctioned
      `get_storage_client()` → clean; unified-cloud-interface internals → still clean (exemption works). Capture output.

### Phase 3 — `try/except ImportError` fallback check (custom QG script)

- [ ] [SCRIPT] P2. Write `scripts/quality_gates/check_no_fallback_imports.py` — AST-walk for
      `try: import X … except (ImportError|ModuleNotFoundError):`. Mirror the existing `check_*.py` structure +
      baseline-ratchet (`*_baseline.yaml`) for pre-existing hits. (No clean ruff rule exists — it's control-flow.)
- [ ] [TEST] P2. `tests/.../test_check_no_fallback_imports.py` — positive (a try/except-ImportError block → flagged),
      negative (plain top-level import → clean), + baseline-respected. Run via the repo's own QG, not standalone pytest.
- [ ] [SCRIPT] P2. Wire the check into `quality-gates-base` as a numbered STEP; record the STEP number.

### Phase 4 — rollout + close the loop in CLAUDE.md

- [ ] [SCRIPT] P2. Roll out the ruff-config + QG-step changes to all repos via `rollout-quality-gates-unified.py`
      (template → all repos; NEVER hand-edit per-repo copies). Verify on ≥1 sample repo that `quality-gates.sh` actually
      runs the 3 new gates (not just that the config landed).
- [ ] [DOC] P2. Update `cursor-configs/CLAUDE.md` so the 3 rules cite their enforcement (like the other gated rules do —
      "QG STEP X / ruff DTZ enforces"): the UTC + cloud-SDK lines in § "Cross-Cutting Rules › Python service/library
      specifics", and a one-line note that fallback-imports are now gated.

## Success criteria (PLAN_FORMAT §8) — testing is the point of this plan

- Each of the 3 gates **proven to FIRE on a known violation AND PASS on clean code**, with the captured output pasted
  into the relevant phase (not just "added to config").
- The custom `check_no_fallback_imports.py` has unit tests (positive + negative + baseline) that pass in QG.
- Rolled out to all repos via the template mechanism; pre-existing violations **baselined** so no green repo's QG breaks
  (ratchet, not big-bang fix).
- CLAUDE.md updated so the 3 rules show as gate-enforced — converting "agent must remember" → "CI fails the PR".

## Continuous verification

- These gates ARE the continuous verification for their rules going forward. Add nothing further; the ratchet baselines
  prevent regression.

## Notes

- Composes with the context-hygiene plan (this is its follow-up — that plan de-bloated CLAUDE.md; this one makes the
  grep-able rules survive any future de-bloat). Slated for **2026-06-03** (Harsh or Ikenna).
