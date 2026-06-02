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

- [ ] [SCRIPT] P2. **UTC count**: run ruff with `--select DTZ` in **preview/report mode** (no config change — e.g.
      `ruff check --select DTZ --statistics <repo>/<src>` per repo). Tabulate violations per repo + per code
      (DTZ005/003/…). Record the total + worst repos in this plan.
- [ ] [SCRIPT] P2. **cloud-SDK count**: grep each repo for `from google.cloud` / `import boto3` (excluding
      unified-cloud-interface's own internals + `.venv`/tests). Tabulate per repo; note which are legit (the interface
      repo) vs violations.
- [ ] [SCRIPT] P2. **fallback-import count**: AST/grep each repo for
      `try: … import … except (ImportError|     ModuleNotFoundError)`. Tabulate per repo.
- [ ] [DOC] P2. **Present to operator**: one table — rule × total-violations × worst-repos × recommended approach
      (ratchet-baseline if many / fix-in-place if few). This is the decision input for Phase 2.

### Phase 2 — OPERATOR APPROVAL GATE `BLOCKED-OPERATOR-DECISION`

- [ ] [DOC] P2. **BLOCKED-OPERATOR-DECISION** — operator reviews the Phase-1 numbers and approves, per rule: (a) gate it
      now or defer; (b) ratchet-baseline existing violations vs run a fix-campaign first. Record the `[ack]` + the
      per-rule decision here. **Phase 3 does not start until this is acked.**

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
