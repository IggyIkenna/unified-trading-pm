---
title: "Repo scripts/ governance — ruff-lint pass + deprecate/delete audit + strict-quickmerge carve scope (D16)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
created: 2026-06-18
locked_by: live-defi-rollout
source:
  - operator decision 2026-06-18 (CI/CD drift audit D16 follow-up)
  - plans/audit/results/cicd_pipeline_vs_plans_drift_audit_2026_06_17.md § D16
---

# Repo scripts/ governance — lint + audit + the strict-quickmerge carve scope

## Decisions (operator-ratified 2026-06-18)

1. **`scripts/` stays OUT of typecheck (basedpyright) + coverage — by design.** Repo `scripts/` are one-off/throwaway
   (run a handful of times, then deleted). Gating them with the typechecker/coverage only manufactures **refactor
   tech-debt** for code meant to be removed (every refactor would have to keep soon-to-be-deleted scripts type-clean).
   Recurring/important logic must become a **CLI subcommand** (which IS gated as part of `$SOURCE_DIR`), never a
   permanent `scripts/` file. Confirms the existing Script-Homes contract (`codex/06-coding-standards/script-homes.md`).
2. **ADD a ruff-lint pass on `scripts/`** (cheap, autofixable rot-catch — syntax / imports / obvious bugs) — **no
   basedpyright** (too heavy + high-noise for throwaway code). Exact ruff scope (which rules, ratchet vs hard) is
   surfaced by the Phase-1 audit.
3. **`tests/` stays AS-IS** — essential; ruff-linted + pytest-run on every QG (local + CI + staging); deliberately
   **no** basedpyright (noise > help on test code); naturally no coverage. No change.
4. **D16 — the strict-quickmerge `scripts/` carve scope (PM-only vs all-repos) is PENDING this audit.** Verified: the
   carve only affects **provenance** (the `Quickmerge:` trailer + dep-gate pre-flight), NOT content-gating — `scripts/`
   is QG-unchecked either way. Decide after the audit shows what service-repo `scripts/` actually contain.

## Verified facts (`base-service.sh` — the same script CI + staging run)

| Path           | ruff | basedpyright | pytest | coverage |
| -------------- | ---- | ------------ | ------ | -------- |
| `$SOURCE_DIR/` | ✅   | ✅ (L746)    | —      | ✅       |
| `tests/`       | ✅   | ❌           | ✅     | —        |
| `scripts/`     | ❌   | ❌           | ❌     | ❌       |

A `scripts/*.py` is checked **nowhere** (local or staging — same script both places). Accepted as intentional (decision
1); partially closed by the ruff-lint pass (decision 2). `tests/` ARE caught in staging (ruff + pytest), so a carved-out
`tests/*.py` is genuinely gated — the carve is safe for tests.

## Inventory (2026-06-18, `find scripts/ -name '*.py'` fleet-wide)

**~647 `.py` across 22 repos; ~131 match a stale-name heuristic**
(`migrat|backfill|one_off|reconcile|dedup|cleanup|fix_| repair|rename|move_|delete_|purge|sweep` — a starting list, NOT
a verdict). Heaviest:

| Repo                     | .py | stale-named                          |
| ------------------------ | --- | ------------------------------------ |
| instruments-service      | 111 | **65** ← biggest cleanup target      |
| unified-trading-pm       | 248 | 18 (mostly LEGIT tooling — see note) |
| market-tick-data-service | 62  | 29                                   |
| deployment-service       | 53  | 5                                    |
| e2e-testing              | 48  | 2                                    |
| features-service         | 31  | 2                                    |
| unified-api-contracts    | 28  | 0                                    |
| (others ≤16 each)        | …   | …                                    |

> **PM is special — do NOT lump it with service repos.** Its 248 scripts are the workspace **tooling host** (the CICD
> machinery, propagation templates, plan-hygiene, agents) — genuine, recurring, chicken-and-egg infrastructure, NOT
> one-off throwaway. This is exactly why the strict-quickmerge `scripts/` carve exists for PM. The throwaway-one-off
> model applies to **service-repo** scripts (instruments-service / MTDS are the big targets).

## Phase 1 — audit each repo's scripts/ (characterize + flag) [P2]

- [ ] [AUDIT] P2. Walk each repo's `scripts/` (start with the heavy/stale concentrations: instruments-service,
      market-tick-data-service, deployment-service, e2e-testing). Classify each script: (a) LIVE one-off still needed;
      (b) RAN-ONCE-DONE → delete (Script-Homes: delete after prod-run + a GCS orphan-sweep shows 0 stale targets); (c)
      OUT-OF-SHAPE / divergent from current code (hardcoded buckets / pre-env-short paths / direct
      `google.cloud`/`boto3` / dead imports / references to deleted modules) → mark deprecated or delete; (d) RECURRING
      → should be a CLI subcommand (file the promotion). Land a results doc under `plans/audit/results/`. Target: all
      service repos.
- [ ] [AUDIT] P2. From the audit, produce the concrete delete / deprecate / CLI-promotion lists; execute the deletes
      carefully (never delete a script that still has live GCS targets — verify first). Target: per-repo.

## Phase 2 — ruff-lint pass on scripts/ [P2]

- [ ] [SCRIPT] P2. Add `scripts/` to the **ruff lint** pass in `base-service.sh` (lint-only — NOT basedpyright, NOT
      coverage). Decide ruff rule scope + ratchet-vs-hard from the Phase-1 findings (a fleet of messy one-offs will
      light up → likely a baselined ratchet that only goes DOWN, like the existing 5.94/5.95 ratchets). Repo:
      **unified-trading-pm** (`base-*.sh`) → fleet-live via the PM-sourced base scripts (no per-repo rollout).
      **Sequencing:** run AFTER Phase-1 deletes so the ratchet baseline isn't inflated by soon-to-be-deleted scripts.

## Phase 3 — D16 strict-quickmerge carve scope [P2]

- [ ] [SCRIPT] P2. Decide + implement the `scripts/` provenance-carve scope, informed by Phase 1 (how often service-repo
      scripts are legitimately direct-pushed during migrations): - **PM-only** → make `check_strict_quickmerge.py`
      repo-aware (carve `scripts/` for PM; treat a service repo's `scripts/*.py` as gated source needing the
      `Quickmerge:` trailer) + update CLAUDE.md carve #3 to match. - **all-repos** → update CLAUDE.md carve #3 to "any
      repo's `scripts/**`" so the doc matches the current code. Keep `tests/` exempt either way (it's caught in staging
      via pytest). Repo: unified-trading-pm.

## Codex SSOT updates

- `codex/06-coding-standards/script-homes.md` — add the "scripts/: ruff-lint YES; basedpyright + coverage NO (by design,
  to avoid refactor tech-debt on throwaway code); recurring logic → CLI" clarification when Phase 2 lands.

## Success criteria

- Every service repo's `scripts/` audited; the delete/deprecate list executed (0 out-of-shape scripts left in-tree).
- `scripts/` is ruff-linted fleet-wide (ratcheted); basedpyright + coverage remain excluded by design.
- The D16 carve scope is decided + implemented; CLAUDE.md matches `check_strict_quickmerge.py`.
- `tests/` unchanged (confirmed intentional).
