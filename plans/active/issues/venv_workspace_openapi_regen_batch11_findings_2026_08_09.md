---
doc_type: issue
title: .venv-workspace + openapi-regen batch11 findings — extraction checkpoint, deprecated drift gate, GCS 404
summary: >-
  Findings from ci_satellite_ao_dispatch_batch11's .venv-workspace provisioning + generate-unified-openapi.sh regen
  todo. The venv root-cause fix (missing uv override-dependencies application) is shipped
  (unified-trading-pm@026a84d6f6). This doc tracks the remaining findings that could not be fixed inline: a
  BLOCKED-EXTRACTION-REGRESSION on config-registry.json's total_repos metric (root-caused but not auto-resolved), a
  stale reference to a deprecated QG script in the parent plan's own stated Gate, an unrelated GCS 404 in the
  instrument-snapshot sub-generator, and a stale phantom-repo entry in generate_config_registry.py.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [ci, openapi, venv-workspace, config-registry, extraction-checkpoint, gcs, findings]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/ci_satellite_ao_dispatch_batch11_finalize_2026_08_09.md,
    /plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md,
  ]
created: "2026-08-09"
author: infra worker (slot-10)
source: ci_satellite_ao_dispatch_batch11-2e8f39d10b00
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: fix
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# .venv-workspace + openapi-regen batch11 findings

## What I found

**1. BLOCKED-EXTRACTION-REGRESSION on `config-registry.json` (`total_repos` 19→14) — root-caused, not auto-resolved.**
After fixing `.venv-workspace` (see "Already fixed" below) and running `generate-unified-openapi.sh` end-to-end, the
fresh `config-registry.json` shows `total_configs` UP (26→30) but `total_repos` DOWN (19→14) vs the git-committed
baseline. Per the batch11 todo's own checkpoint rule ("If the fresh count is LOWER than the committed baseline for ANY
tracked output file, DO NOT commit"), I discarded the generated outputs (`git checkout --`) rather than commit.
Root-cause investigation: the 7 "missing" repos in fresh (`features-calendar-service`, `features-commodity-service`,
`features-cross-instrument-service`, `features-delta-one-service`, `features-multi-timeframe-service`,
`features-sports-service`, `ml-inference-service`) are exactly the phantom per-family services
`generate_config_registry.py`'s own top-of-file comment says were consolidated 2026-06-11 into
`features-service`/`ml-service` monorepos (whose root packages intentionally carry no top-level config class — also
documented in that file). The committed baseline predates that consolidation-aware script update and was never
regenerated since (this is the whole premise of the parent plan's Residual 1). The 5 "new" repos in fresh
(`fund-administration-service`, `greeks-service`, `instruments-service`, `market-tick-data-service`,
`unified-trading-library (config_interface/)`) are genuinely new, correct additions.
`unified-trading-system.openapi.json` (the other tracked file) shows NO regression — both paths (473→628) and schemas
(105→353) went up substantially. I did NOT override the checkpoint myself: it's an intentionally mechanical,
non-discretionary gate built specifically to stop a worker's own "I've reasoned it through" call under this exact time
pressure (per the parent doc's own 2026-08-07 note about the "rushed step 4" risk) — the right next step is a fresh pass
(or operator sign-off) that independently confirms this read and then commits deliberately, not me unilaterally
overriding today.

**2. `check_openapi_drift.py` — the parent plan's stated Gate references a script deprecated 2026-05-16, unrelated to
the files this regen produces.** The batch11 todo's step 6 ("Verify `check_openapi_drift.py`... this closes the parent
doc's own stated Gate") cannot be meaningfully executed: the script's own docstring says
`**DEPRECATED 2026-05-16 — DO NOT WIRE INTO QG**` and compares `unified-trading-api/openapi.json` (a 61-path slim
facade) against `unified-trading-system-ui/lib/registry/openapi.json` (a 479-path aggregated UI mirror) — a
structurally-different file pair that has nothing to do with `unified-trading-system.openapi.json` /
`config-registry.json` (the outputs this task actually regenerates). No successor drift-check script exists for those
two files (`grep`-confirmed against `scripts/quality_gates/` and `scripts/openapi/`).

**3. (Minor, unrelated to venv work) `generate_instrument_snapshot.py` fails with a GCS 404** —
`gs://instruments-store-cefi-central-element-323112/instrument_availability/by_date/day=2026-03-27/` — "the specified
bucket does not exist." This halted the `generate-unified-openapi.sh end to end` run before it reached the
`audit_type_usage.py` / `audit_dead_code.py` / `audit_api_ui_coverage.py` steps, which never got a chance to run at all
this pass. Not caused by anything in this task's scope (venv/imports were all confirmed healthy at that point); looks
like a stale/renamed bucket reference.

**4. (Trivial) `unified-market-interface` is a stale/phantom entry in `generate_config_registry.py`'s `CONFIG_REGISTRY`
list** — that repo does not exist anywhere in this workspace (no directory, not in `workspace-manifest.json`). Every
regen run will `WARNING: SKIP` on it forever until removed.

## Already fixed (this session, shipped)

- **Root cause of the venv incompleteness**: `setup-workspace-venv.sh`'s `uv pip install -e <repo>` installs each repo
  standalone with no calling-project `[tool.uv]` context, so a repo's own `override-dependencies` (e.g.
  execution-service's `requests>=2.33.0` override needed to beat betfairlightweight's `requests<2.33.0` cap) was never
  applied — leaving `execution-service` (and its dependents `e2e-testing`, `system-integration-tests`) permanently
  unable to editable-install. Fixed by collecting the union of every repo's own overrides once and passing them via
  `--overrides` to every editable install. Shipped: `unified-trading-pm@026a84d6f6`. Verified: every real service in the
  manifest now imports cleanly (21 OK, 4 documented non-Python tooling-only repos, 1 documented no-package-by-design
  repo — 0 real failures), smoke-tested end-to-end against a second workspace mirror before shipping.
- **Repo-wide QG red** (`plan-discipline` / `B-issue-filename`): a sibling issue doc used a hyphen where the naming
  convention requires an underscore, blocking every commit to `unified-trading-pm`. Fixed via rename (pure `git mv`, no
  content change). Landed as `unified-trading-pm@cbe3ca5f21` (independently also fixed by slot-2 at nearly the same time
  — git's rebase correctly de-duplicated the identical change).

## Why it matters

`config-registry.json` / `unified-trading-system.openapi.json` feed UI/downstream consumers that are meant to represent
the system's actual config/API surface — the current committed versions are ~2-3 months stale (missing
`execution-service`'s configs entirely, among others) and have been silently wrong for that whole window. The venv fix
now makes a CORRECT regen possible for the first time; finding 1 is the last gate before that correct data can actually
ship.

## Recommended decision

- Finding 1: a follow-up pass (or this doc's own AO-dispatched todo below) should re-run the regen with today's fixed
  `.venv-workspace`, independently confirm the phantom-service-consolidation explanation against
  `workspace-manifest.json` / the `strategy_repo_consolidation` plan, and if confirmed, commit the outputs.
- Finding 2: either build a real extraction-count regression gate for `config-registry.json` /
  `unified-trading-system.openapi.json` (formalizing finding 1's manual check), or correct the parent doc's Gate text to
  stop citing the deprecated script.
- Findings 3-4: small, independent, bounded fixes — todos below.

## Todos

- [ ] 1. [SCRIPT] P1. Re-run `generate-unified-openapi.sh` against the now-fixed `.venv-workspace`, independently verify
      the phantom-service-consolidation explanation for `config-registry.json`'s `total_repos` drop (cross-check
      `workspace-manifest.json` + any `strategy_repo_consolidation` plan/codex doc), and if confirmed, commit the
      regenerated outputs (`config-registry.json`, `unified-trading-system.openapi.json`, `ui-reference-data.json`,
      `system-topology.json`) via quickmerge in `unified-api-contracts`. (repo: unified-api-contracts)
- [ ] 2. [SCRIPT] P2. Either build a real drift/regression gate comparing fresh vs. committed `config-registry.json` /
      `unified-trading-system.openapi.json` extraction counts (formalizing the manual checkpoint used in this session),
      or correct `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`'s Residual 1 text (and any other
      citing doc) to stop pointing at the deprecated `check_openapi_drift.py` as the closing Gate. (repo:
      unified-trading-pm)
- [ ] 3. [INFRA] P3. Investigate the `gs://instruments-store-cefi-central-element-323112` 404 in
      `generate_instrument_snapshot.py` (stale/renamed bucket? check `resolve_bucket_name`/bucket-isolation-model) and
      fix so `generate-unified-openapi.sh` can run genuinely end-to-end including the
      `audit_type_usage.py`/`audit_dead_code.py`/`audit_api_ui_coverage.py` steps. (repo: unified-trading-pm)
- [ ] 4. [SCRIPT] P3. Remove the stale `unified-market-interface` entry from `generate_config_registry.py`'s
      `CONFIG_REGISTRY` list (repo doesn't exist in this workspace; every regen run SKIPs it with a ModuleNotFoundError
      warning). (repo: unified-trading-pm)

## Progress Log

- **2026-08-09** — Filed by the batch11 infra worker (slot-10) per the Findings Closure HARD RULE, after root-causing
  and shipping the `.venv-workspace` fix but hitting a genuine BLOCKED-EXTRACTION-REGRESSION on the extraction-count
  checkpoint plus 3 smaller unrelated findings surfaced along the way.
