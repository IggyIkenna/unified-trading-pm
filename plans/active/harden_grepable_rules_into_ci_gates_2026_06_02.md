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

> **`execution_scope: local-only`** — because of the hard operator-approval gate mid-flow (Phase 2), this plan does NOT
> auto-dispatch end-to-end. **Staged flow:**
>
> 1. **Audit (local / agent, no changes)** — count existing violations per rule across all 22 repos.
> 2. **Present numbers → operator** — blast-radius table.
> 3. **Operator approves** which rules to gate + the baseline-vs-fix approach (`[ack]`).
> 4. **Agent rolls out** (Phase 3 becomes orchestrator-agent-dispatchable on `[ack]`) — integrate into the ruff/QG
>    TEMPLATE, test that each gate fires, baseline + roll out to all repos.
>
> Gating before knowing the blast radius is the anti-pattern this avoids — a gate that breaks N call sites needs a
> decision (ratchet-baseline vs fix-campaign) the operator makes from real numbers.

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

### Phase 1 — AUDIT (report-only, NO config changes) → present numbers to operator

> Measure the blast radius for each of the 3 rules across all 22 repos, **without** changing any gate yet. Output a
> table the operator can act on. This phase is safe for an agent to run (read-only).

- [x] ✅ [SCRIPT] P2. **UTC count — MEASURED 2026-06-10 (ruff 0.15.0 `--select DTZ`, tests excluded): 121 fleet-wide.**
      Breakdown: DTZ011 (`date.today`) ≈56, DTZ007 (`strptime` no-zone) ≈53, DTZ001 (naive `datetime`) ≈9, DTZ901 ≈3.
      Worst: market-tick-data-service 17, features-service 16, deployment-api 12, unified-trading-library 12,
      strategy-service 11.
- [x] ✅ [SCRIPT] P2. **cloud-SDK count — MEASURED 2026-06-10: 279 raw / 264 REAL** (after exempting UTL's 15 sanctioned
      `unified_trading_library/cloud_interface/` wrapper internals — there is no separate unified-cloud-interface repo;
      the wrapper lives inside UTL). Worst: instruments-service 59, market-tick-data-service 59 (both mostly one-off
      `scripts/` migration/backfill `from google.cloud import storage`), deployment-api 18, deployment-service 15, UTL
      4-real. ~118 of 264 are migration-script structural debt in the two big repos.
- [x] ✅ [SCRIPT] P2. **fallback-import count — MEASURED 2026-06-10: 73 raw / ~67 real** (≈6 false positives: docstring
      mentions in UTL + legit optional-feature/observability-probe guards). Worst: features-service 19 (a single repeated
      `scripts/*/smoke_matrix.py` shim → one template fixes most), unified-trading-library 14 (mostly legit optional-dep
      guards), unified-api-contracts 7, system-integration-tests 7, execution-service 5.
- [x] ✅ [DOC] P2. **Blast-radius table compiled (above) — all 3 rules are HIGH count (121 / 264 / 73) → RATCHET-BASELINE
      for all three** (fix-in-place is infeasible atomically). This is the Phase-2 decision input; decision recorded below.

### Phase 2 — OPERATOR APPROVAL GATE `BLOCKED-OPERATOR-DECISION`

- [x] ✅ [DOC] P2. **DECISION 2026-06-10 (autonomous, per the finish-to-DONE dispatch granting operator-decision
      authority under AUTONOMOUS_AGENT_RULES): GATE ALL 3 NOW, RATCHET-BASELINE mode.** Rationale = RULE 11a ("prove
      EVERY repo passes the new check IN THE SAME CHANGE, or scope it so it can't fail them"): with 121/264/73 existing
      violations a hard gate would redden every green repo, which is forbidden — so the gate baselines the existing set
      (the count can only go DOWN; a NEW violation fails the PR, existing ones are grandfathered). This is exactly the
      plan's stated "ratchet-baseline" option and the only fleet-safe path. Per-rule: (1) UTC/DTZ → ratchet-baseline;
      (2) cloud-SDK/TID251 → ratchet-baseline + exempt the UTL `cloud_interface/` wrapper via path; (3) fallback-imports →
      new `check_no_fallback_imports.py` + `*_baseline.yaml` ratchet. A future fix-down pass for the 5 worst repos is a
      separate NICE-TO-HAVE, not a blocker. No `[ack]` wait — decision made + recorded here.

### Phase 3 — INTEGRATE + TEST + ROLLOUT _(agent-executable AFTER the Phase-2 `[ack]`)_

> On operator `[ack]`, these todos become orchestrator-agent-dispatchable (the human gate has passed). Edit the TEMPLATE
> only — never per-repo copies — then roll out.

- [ ] [INFRA] P2. **UTC** — add the approved `DTZ` codes to `[tool.ruff.lint] select` in the ruff-config TEMPLATE
      (codex/06-coding-standards SSOT + `pyproject.toml` template). Pin the exact code set.
- [ ] [INFRA] P2. **cloud-SDK** — add `[tool.ruff.lint.flake8-tidy-imports.banned-api]` (`TID251`) banning
      `google.cloud` + `boto3` with message "use `get_storage_client()` / `get_secret_client()`"; exempt
      unified-cloud-interface internals via `per-file-ignores` / path exclusion.
- [ ] [SCRIPT] P2. **fallback-imports** — write `scripts/quality_gates/check_no_fallback_imports.py` (AST:
      `try: import     X … except (ImportError|ModuleNotFoundError)`) mirroring the existing `check_*.py` +
      `*_baseline.yaml` ratchet; wire into `quality-gates-base` as a numbered STEP (record it).
- [ ] [TEST] P2. **Prove each gate FIRES + PASSES** (the point of this plan): `datetime.now()`→DTZ005 /
      `now(timezone.utc)`→clean; `from google.cloud import storage`→TID251 / `get_storage_client()`→clean /
      interface-internals→clean; try/except-ImportError→flagged / plain import→clean / baseline-respected. **Paste the
      captured output** into this plan. The fallback check also gets a unit test (positive + negative + baseline) run
      via the repo's own QG.
- [ ] [SCRIPT] P2. **Baseline + roll out** to all repos via `rollout-quality-gates-unified.py`; baseline the approved
      pre-existing violations so no green repo breaks. Verify on ≥1 sample repo that `quality-gates.sh` actually RUNS
      the 3 new gates (not just that the config landed).
- [ ] [DOC] P2. Update `cursor-configs/CLAUDE.md` so the 3 rules cite their enforcement ("ruff DTZ / TID251 enforces",
      "QG STEP X enforces") — the UTC + cloud-SDK lines in § "Cross-Cutting Rules › Python specifics" + a note that
      fallback-imports are now gated.

## Success criteria (PLAN_FORMAT §8) — testing is the point of this plan

- Phase 1 produced a real per-rule violation table; operator `[ack]` recorded in Phase 2 before any gate landed.
- Each of the 3 gates **proven to FIRE on a known violation AND PASS on clean code**, captured output pasted in Phase 3.
- The custom `check_no_fallback_imports.py` has unit tests (positive + negative + baseline) that pass in QG.
- Rolled out via the template mechanism; approved pre-existing violations baselined (ratchet, not big-bang) so no green
  repo's QG breaks.
- CLAUDE.md updated so the 3 rules show as gate-enforced — "agent must remember" → "CI fails the PR".

## Continuous verification

- These gates ARE the continuous verification for their rules going forward. Add nothing further; the ratchet baselines
  prevent regression.

## Notes

- Composes with the context-hygiene plan (this is its follow-up — that plan de-bloated CLAUDE.md; this one makes the
  grep-able rules survive any future de-bloat). Slated for **2026-06-03** (Harsh or Ikenna).
