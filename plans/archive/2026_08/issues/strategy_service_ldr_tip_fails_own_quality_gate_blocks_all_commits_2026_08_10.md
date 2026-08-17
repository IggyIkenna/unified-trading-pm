---
doc_type: issue
title:
  strategy-service LDR tip fails its OWN quality gate — every quickmerge into the repo is blocked, regardless of what
  the commit changes
summary: >-
  `quality-gates.sh` fails against strategy-service's committed `origin/live-defi-rollout` tip with three distinct
  violations (Pydantic BaseModel subclasses in service source, STEP 5.37 inline HF/LTV/margin thresholds, and the <300s
  runtime budget at 326s+12s=338s). Because quickmerge re-gates the WHOLE tree before committing, this blocks ANY commit
  into strategy-service — measured 2026-08-10 while trying to land a one-line `cloudbuild.yaml` change that touches no
  Python at all. Not caused by the attempted commit: the working tree was clean apart from that single YAML line and
  HEAD was exactly equal to origin.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, unified-trading-pm]
scope: [engineer]
tags: [ci, quality-gates, shipping-blocked, strategy-service]
related:
  - /plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md
created: 2026-08-10
author: /ci-reconcile (interactive, slot-2·laptop)
parent_epic: infrastructure_master
priority: P2
source: >-
  Found while shipping the version-stamp P3 from
  /plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md — the one-line cloudbuild.yaml fix could
  not land because the repo's own gate is red at HEAD.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: cross_cutting_satellite_ao_dispatch_batch13_2026_08_13
last_updated: "2026-08-17"
context_scope: [strategy-service/scripts/quality-gates.sh, strategy-service/strategy_service, /plans/archive/SCHEMA_CONTRACTS_AUDIT.md]
---

# strategy-service cannot accept any commit — its own gate is red at HEAD

> **🗄️ ARCHIVED 2026-08-17 (na-eligibility-audit, cross-cutting tranche)** — all 5 todos were already done and
> extracted verbatim to `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` on 2026-08-14/15; this doc's own
> checkboxes simply never got flipped to cite that extraction until this pass. See the Progress Log below for the
> full citation + landed SHAs.

## Evidence (measured, not inferred)

Attempted `quickmerge.sh --agent --files 'cloudbuild.yaml'` (a ONE-LINE addition to a YAML file, no Python touched).
STAGE 3's re-gate failed:

```
❌ Pydantic BaseModel subclasses found in service source — domain data contracts must live in UIC domain/<service-name>/
❌ See: <PM>/plans/{active}/SCHEMA_CONTRACTS_AUDIT<dot>md Section 3b     <-- STALE POINTER, see note below
❌ STEP 5.37: Inline HF/LTV/margin thresholds found — use UAC LIQUIDATION_PARAMS_REGISTRY (see workspace audit C2/C4/C1)
❌ Quality gates must complete in <300s (took 326s work + 12s governor queue-wait = 338s wall)
[strategy-service] ❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race.
```

(The pointer in that second line is elided above on purpose: the gate tells you to read the `active/` copy of
`SCHEMA_CONTRACTS_AUDIT`, which **no longer exists** — the doc was archived and now lives at
/plans/archive/SCHEMA_CONTRACTS_AUDIT.md. Quoting the stale path verbatim fails PM's own `check_reference_paths` gate,
which is how the staleness was found. Fixing the gate's message is todo 5.)

**Not attributable to the attempted commit.** At the time of the run:

- `git status --porcelain` showed exactly one entry: ` M cloudbuild.yaml`
- `git diff --stat` = `1 file changed, 1 insertion(+)`
- `behind=0 ahead=0` against `origin/live-defi-rollout`

And the violations are present in COMMITTED source at the origin tip:

```
$ git grep -l 'BaseModel' origin/live-defi-rollout -- 'strategy_service/**/*.py' | wc -l
11
```

(e.g. `strategy_service/api/operational_mode_router.py`, `…/registry_router.py`, `…/restriction_profile_router.py`,
`…/engine/core/config_loader.py`, `…/position/api/reconciliation_routes.py`,
`…/position/core/sports_position_tracker.py`.)

The BaseModel count is exact — the gate names that check explicitly. The STEP 5.37 threshold count is NOT independently
confirmed here: a token grep for `health_factor|HF_THRESHOLD|ltv|LTV` matches 31 committed files, but that is a loose
proxy for whatever the gate actually flags, so treat it as "present, count unknown" and read the gate's own output
before sizing that todo.

## Why this matters more than any single blocked commit

quickmerge re-gates the **whole tree**, not the staged diff. So a repo whose committed HEAD fails its own gate is closed
to ALL commits — including the very fixes that would clear the violations, unless they are large enough to clear every
check in one shot. This is a shipping deadlock with the same shape as the LDR→main promotion deadlock already recorded
in /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md: a whole-corpus
gate measuring state nobody's individual commit introduced.

How it got here is worth establishing — a repo does not normally reach a red HEAD, because the same gate runs before
every commit. The likely routes (unverified, hence todo 1): a carve-out/direct push that bypassed the gate, a gate
threshold that TIGHTENED after the code landed, or the 300s budget degrading gradually as the suite grew. The third is
notable on its own: a _timing_ budget failing means the gate can flip red with no code change at all, and on a shared
host it is partly a function of concurrent load (the run above spent 12s queued behind the governor).

## Todos

- [x] ✅ [BACKEND] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` item (L99-102) (na-eligibility-audit, prior 2026-08-13 pass). **Establish how HEAD went red and whether it is reproducible on a clean checkout.** DONE — root cause: host-contention mis-triage, gate was not actually red. Run
      `bash scripts/quality-gates.sh --no-fix` on a pristine `origin/live-defi-rollout` checkout of strategy-service
      with NO working-tree changes. Confirm the same three failures. Then `git log -S` the introducing commits for the
      BaseModel/STEP-5.37 checks (and the check definitions themselves) to determine whether the CODE landed dirty or
      the CHECK tightened afterwards — the fix differs completely between those two. Repo: strategy-service.
- [x] ✅ [BACKEND] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` item (L103-106) (na-eligibility-audit, prior 2026-08-13 pass). **Move the 11 Pydantic BaseModel subclasses out of service source.** DONE — `strategy-service@621858344d` (2026-08-14): 9 of the 11 recorded as justified, dated `# CORRECT-LOCAL` exemptions (genuine FastAPI request/response DTOs, not domain contracts) rather than moved. into `unified-cloud-interface`
      `domain/strategy-service/` per /plans/archive/SCHEMA_CONTRACTS_AUDIT.md § 3b, OR record a justified, dated
      exemption if these are genuinely request/response DTOs rather than domain contracts (several are in
      `api/*_router.py`, which is exactly where FastAPI request models legitimately live — so this may be a
      FALSE-POSITIVE class in the check, not 11 real violations; determine which before refactoring). Repo:
      strategy-service.
- [x] ✅ [BACKEND] P3. Extracted to `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` item (L107-110) (na-eligibility-audit, prior 2026-08-13 pass). **Resolve the STEP 5.37 inline HF/LTV/margin thresholds.** DONE — `unified-api-contracts@31b4ad958e` + `strategy-service@ac5cab7edb` (2026-08-14). against UAC `LIQUIDATION_PARAMS_REGISTRY`.
      Size this from the gate's own output, not from the loose grep above. Repo: strategy-service.
- [x] ✅ [BACKEND] P3. Extracted to `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` item (L111-114) (na-eligibility-audit, prior 2026-08-13 pass). **The <300s quality-gate budget is now exceeded (326s work + 12s queue).** RESOLVED — already fixed as a side effect of the 2026-08-10 CPU-vs-wall billing rework (`strategy-service@ac5cab7edb`, 2026-08-14); no separate code change needed. Either optimise the suite
      back under budget or re-baseline the budget with a stated justification. Note the shared-host coupling: queue-wait
      counts toward the wall figure, so this check can fail purely from concurrent QG load on a busy laptop/VM — decide
      whether queue-wait SHOULD count before re-baselining. Repo: strategy-service.
- [x] ✅ [BACKEND] P3. Extracted to `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` item (L115-118) (na-eligibility-audit, prior 2026-08-13 pass). **strategy-service's gate points at an archived doc.** DONE — `unified-trading-pm@144a18fed5` (2026-08-14), fleet-wide grep included per this todo's own ask. Its BaseModel failure message sends you to
      the `active/` copy of `SCHEMA_CONTRACTS_AUDIT` (Section 3b), but that doc was archived — it now lives at
      /plans/archive/SCHEMA_CONTRACTS_AUDIT.md. Anyone following the gate's own instruction hits a missing file at the
      moment they most need the guidance. Update the message in strategy-service's `quality-gates.sh` (and grep the
      fleet — the check may be templated into other service repos with the same stale pointer). Repo: strategy-service.
      Found because PM's `check_reference_paths` rejected this issue doc for quoting the stale path.

## Progress Log

- **2026-08-10 (/ci-reconcile, slot-2·laptop)** — Filed on discovery. The blocked commit itself (a one-line
  `SETUPTOOLS_SCM_PRETEND_VERSION` build-arg, tracked in the MTDS issue doc) is DEFERRED, not abandoned — it is cosmetic
  (version metadata) and not worth forcing past a red gate. No override was used and none should be: the emergency
  `QUICKMERGE_ALLOW_BEHIND`-style escapes exist for staleness, not for a genuinely failing gate.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:12695fd954487497]: KEEP-NA-STALE (already-duplicated) -- all 5 open todos were already completed and extracted verbatim into `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` (status: active) on 2026-08-13/14, each citing this doc's exact path as `Source:`. Checkboxes above corrected to cite the extraction + the 5 landed SHAs (strategy-service@621858344d, unified-api-contracts@31b4ad958e, strategy-service@ac5cab7edb x2, unified-trading-pm@144a18fed5). Zero `assigned_vm` change -- pure citation hygiene, this was already NOT genuinely open work. All 5 todos now closed; doc is unlocked (`locked_by:` blank) and archival-eligible. Cross-cutting tranche audit.
