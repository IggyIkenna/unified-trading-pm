---
doc_type: issue
title:
  QG sentinel is ENVIRONMENT-blind — quickmerge runs gates as ENVIRONMENT=development, standalone runs default to prod,
  and the standalone pass launders the failure green
summary: >-
  quickmerge exports `ENVIRONMENT=development` for any non-`main` branch (scripts/quickmerge.sh:1216-1222) — which is
  EVERY slot, since every slot lives on live-defi-rollout. UTL's bucket resolver defaults to **prod** when ENVIRONMENT
  is unset (unified_trading_library/cloud_interface/bucket_naming.py:162), and three repos hardcode prod bucket names in
  tests. Net: those tests FAIL DETERMINISTICALLY under quickmerge and PASS standalone. That alone is only an annoyance —
  the real problem is the documented recovery. Re-running `bash scripts/quality-gates.sh --no-fix` standalone passes
  (prod default) and WRITES THE SENTINEL; quickmerge then matches the sentinel hash and SKIPS the gate entirely, so a
  suite that genuinely fails in quickmerge's environment ships green. The sentinel is a bare sha256 of tree content with
  NO environment dimension, so it cannot distinguish "verified in dev" from "verified in prod". Same class as the
  2026-07-18 deployment-ui incident already documented at quickmerge.sh:1288-1300 (sentinel satisfied → Pass 2 skipped →
  tsc-red tree landed on LDR); that fix closed the tree-drift dimension but not the environment dimension.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library, deployment-api, strategy-service, market-tick-data-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, quality-gates, sentinel, test-isolation, environment, gate-bypass]
related:
  - /plans/archive/issues/staging_workflow_shutdown_2026_07_23.md
  - /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md
  - /plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md
created: 2026-07-23
author: unknown
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
locked_by:
resolved_by:
depends_on: []
source:
  - "observed twice during the 25-unit staging-shutdown rollout 2026-07-23 (unified-trading-library,
    market-tick-data-service)"
  - "reproduced deterministically: ENVIRONMENT unset => pass, ENVIRONMENT=development => fail, same tree/machine"
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md,
    /plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md,
    unified-trading-pm/scripts/quickmerge.sh,
    unified-trading-pm/scripts/quality-gates-base/base-service.sh,
  ]
---

# The QG sentinel cannot tell which environment verified the tree

## How it was found

During the 25-repo staging-shutdown rollout (2026-07-23), two ship agents hit "unrelated test failures" and both
reported them as **transient flakes under parallel xdist**. That diagnosis was repeated up the chain unverified. It is
**wrong** — the failures are deterministic and have nothing to do with xdist.

## The actual mechanism (reproduced, not inferred)

1. **quickmerge forces dev mode.** `scripts/quickmerge.sh:1216-1222`:

   ```bash
   if [ "$CURRENT_BRANCH" = "main" ] || [ "${PROD_FLAG:-false}" = "true" ]; then
     export ENVIRONMENT="production"
   else
     export ENVIRONMENT="development"      # ← every slot, always (all slots are on live-defi-rollout)
   ```

2. **The bucket resolver defaults to prod when unset.** `unified_trading_library/cloud_interface/bucket_naming.py:162` —
   reads `DEPLOYMENT_ENV`, then `ENVIRONMENT`, "defaulting to `prod` when unset".

3. **Three repos hardcode prod bucket names in tests** (`-prd-p`): `unified-trading-library`
   (`tests/cloud_interface/unit/test_constants.py`), `deployment-api`, `strategy-service`. market-tick-data-service
   fails the same family via `test_prediction_stays_prod_without_is_test_run` /
   `test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware`.

4. **Proof** — same tree, same machine, xdist disabled:

   ```
   ENVIRONMENT=            pytest -k instruments_bucket -p no:xdist  →  1 passed
   ENVIRONMENT=development pytest -k instruments_bucket -p no:xdist  →  1 failed
   ```

   Deterministic. Not flaky, not a race, not worker leakage.

## Why this is a gate-BYPASS, not just noise

The recovery everyone uses (and that this rollout's agent instructions explicitly taught) is:

> re-run `bash scripts/quality-gates.sh --no-fix`, then retry quickmerge

Standalone, `ENVIRONMENT` is unset → resolver returns prod → the suite passes → **the sentinel is written**. quickmerge
then finds a sentinel matching the tree hash and prints `✅ SHA sentinel verified — skipping Pass 2 QG re-runs` — **the
failing tests never run again.** The tree ships green having never passed in the environment quickmerge actually uses.

`.qg_content_sentinel` is a **bare sha256 of tree content**:

```
5442c1c262be8627cd3c4ae064ebd4e34f428518f36db48b2bbcdfdad146bbc2
```

No environment, no toolchain, no config dimension. It answers "was THIS TREE verified?" but not "verified under WHICH
configuration?" — so a pass in one environment is silently redeemable in another.

This is the **same class** as the incident already recorded at `scripts/quickmerge.sh:1288-1300` (deployment-ui
2026-07-18: sentinel satisfied → Pass 2 skipped → tsc-red tree landed on LDR). That fix hardened the **tree-drift**
dimension (ancestor-only + byte-identical tree). The **environment** dimension is still open.

## Which side is actually wrong?

Both readings are defensible and the operator should pick — they lead to different fixes:

- **The tests are wrong.** A unit test asserting a literal `-prd-p` name encodes an environment it does not control. It
  should either set the env explicitly (`monkeypatch.setenv("ENVIRONMENT", ...)`) or assert via the resolver's own
  contract rather than a hardcoded string. → smallest change, fixes 3-4 repos.
- **The gate is wrong.** If quickmerge's gate is the per-repo quality boundary, it should run in the environment the
  code actually ships to, not silently in `development`. → bigger blast radius, needs care.
- **The sentinel is wrong (independent of the above, and the real hazard).** It must bind the configuration it was
  produced under — e.g. hash `ENVIRONMENT` (+ any other gate-affecting env) into the sentinel so a dev-verified sentinel
  cannot satisfy a prod-context run, or vice-versa. **This one should be fixed regardless of the other two**, because it
  is what converts a loud failure into a silent pass.

### RULED 2026-07-28 (operator gate-cleanup pass) — BOTH, not a pick-one

No specific answer was on file for this item; applying the operator's standing general theme (full completions over
partial/cheap fixes; "do not allow anything to partially complete") to the analysis above: **fix the tests AND fix the
gate's environment inconsistency — not one or the other.** Reasoning:

- Fixing only the tests (the smaller, contained change) silences the SYMPTOM in 3-4 repos but leaves the actual root
  inconsistency standing: quickmerge always verifies in `development`, a standalone recovery run always verifies in the
  `prod` default, and any future test/config that happens to be environment-sensitive can reproduce this exact class of
  gate-bypass again. That is a shortcut, not a full completion.
- "Fix the gate" does NOT mean flip quickmerge itself to run as `ENVIRONMENT=production` — that would trade this hazard
  for a worse one (every slot's every commit touching real prod credentials/buckets during test runs), which is not what
  "do it properly" calls for. It means: **quickmerge's resolved environment and a standalone `quality-gates.sh --no-fix`
  run's resolved environment must agree, explicitly, for the same branch context** — no more silent divergence where one
  path defaults to `development` and the other defaults to `prod` for the identical tree. Making that binding explicit
  (rather than two independent ambient defaults) is the durable, canonicalization- grade fix, not a hack.
- The sentinel hardening (item 2 below) proceeds independently either way, per the doc's own "fix this regardless"
  finding — it closes the actual silent-bypass hazard on its own.

Full-completion mandate for the two retagged todos below: no partial coverage (all repos, not "the easy ones"), no
guessed/placeholder environment values, cost is not a blocker (this is code + CI config, not paid infra).

## Resolution checklist

- [x] ✅ [DOCS] P1. ~~Decide the split: fix the tests, the gate's environment, or both~~ — **RULED 2026-07-28 (operator
      gate-cleanup pass, general design-choice theme applied, no specific answer was on file): BOTH.** See "RULED
      2026-07-28" under § "Which side is actually wrong?" above for the full reasoning. Confirmed: the sentinel
      hardening below proceeds independently regardless. Retagged away from `[OPERATOR]` — the two concrete pieces of
      follow-on work are items 3 and 5 below.
- [x] ✅ [INFRA] P1. **Bind configuration into the sentinel** (`scripts/base-service.sh` / `scripts/quickmerge.sh`): mix
      `ENVIRONMENT` (and any other gate-affecting env var) into the sentinel hash so a sentinel produced under one
      configuration cannot satisfy a run under another. Add a regression test that a dev-written sentinel does NOT
      satisfy a prod-context quickmerge. **Shipped `unified-trading-pm@4545df4c6` via
      `ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 1(a)** — new `qg-environment.sh`/`qg_resolve_environment()`,
      `_qg_content_hash()` now folds `ENVIRONMENT`/`DEPLOYMENT_ENV` into the sentinel hash, 2 regression test files
      (5/5 + 6/6 assertions), verified live against real `quickmerge.sh`. Checkbox never flipped here when that landed —
      closing now, na-eligibility-audit 2026-07-31.
- [ ] [INFRA] P2. Fix the env-coupled tests in `unified-trading-library`
      (`tests/cloud_interface/unit/test_constants.py`), `deployment-api`, `strategy-service`, and the two
      `market-tick-data-service` cases — set the environment explicitly per-test instead of relying on the ambient
      default. **PARTIAL 2026-07-25 — 1 of 4 repos done; box stays open** (`/plan-reconcile ci`, 2026-07-26): the
      **`unified-trading-library` half is SHIPPED and verified live at the cited path** —
      `tests/cloud_interface/unit/test_constants.py:32-37`'s autouse `_clear_cache` fixture now does
      `monkeypatch.delenv("DEPLOYMENT_ENV", raising=False)` + `monkeypatch.delenv("ENVIRONMENT", raising=False)` with
      the in-file comment _"Isolate from ambient DEPLOYMENT_ENV/ENVIRONMENT (e.g. quickmerge.sh's branch-based …)"_,
      fixing `test_get_bucket_name_gcp` +4 siblings in one place. Full write-up + the 2 sibling test sites also fixed in
      that repo:
      [/plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md](/plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md)
      § Resolution. **DEFERRED — still open**: `deployment-api` and `strategy-service` (not verified this pass), and the
      two `market-tick-data-service` cases, which are demonstrably NOT fixed — they were still failing intermittently as
      late as 2026-07-24 per
      [/plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md](/plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md)
      (5 consecutive quickmerge re-gate hits, `1/1 worker` serial). **Sequencing ruled 2026-07-26** (resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #29, option A): hold the MTDS half specifically until
      that doc's own next step (instrument quickmerge's cascade/pull step, diffing `os.environ` before/after
      `STAGE 0: Cascade`) actually runs — those 2 tests are the ONLY known reproducer of a real leak, and fixing them
      first (silencing the symptom) risks making the leak permanently invisible before its cause is confirmed.
      `deployment-api`/`strategy-service` are NOT the reproducer and are not gated by this — proceed on those two
      independently whenever convenient. **`deployment-api`/`strategy-service` half CONFIRMED CLEAN 2026-07-31 (no fix
      needed)** — full reproduction (both repos' actual `quality-gates.sh`-scoped test suites, `ENVIRONMENT` unset vs
      `development`, byte-identical pass counts both ways) plus a real green `bash scripts/quality-gates.sh` run in each
      repo found no reproducible ambient-`ENVIRONMENT` failure in either repo today — the original claim (grep-derived
      from `-prd-` literals, unlike MTDS's 2 explicitly-named/verified reproducers) does not hold up under direct
      verification; `git log` in both repos shows no intervening fix commit, so this wasn't silently patched elsewhere
      either. Box stays open only because the MTDS half (E7 above) remains genuinely unresolved. Full write-up:
      `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 3.
- [x] ✅ [DOC] P2. Correct the "re-run quality-gates.sh --no-fix then retry" guidance wherever it is taught (agent
      prompts, runbooks): as written it is a sentinel-laundering step, not a fix. It is only safe once the sentinel
      binds configuration. — **Verified 2026-07-31: already done as a byproduct of the sentinel-binding fix above
      (`unified-trading-pm@4545df4c6`).** Full-corpus sweep (every agent/_.md, cursor-configs/_.md + symlinked copies in
      all repos, codex/**/_.md, codex/15-runbooks/, quickmerge.sh, quality-gates-base/_.sh) found no file teaching the
      unsafe pattern as live guidance — the phrase only appears in THIS doc, as the historical bug description. The 3
      SSOT docs describing the recovery flow (`ci-cd-flow.md`, `quality-gates.md`, `quickmerge-architecture.md`) already
      reflect the post-fix, genuinely-safe behavior (sentinel binds `ENVIRONMENT`/`DEPLOYMENT_ENV`; a config mismatch is
      refused with `Re-run: bash scripts/quality-gates.sh`, not silently laundered). Full write-up:
      `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo (same item).
- [x] ✅ [INFRA] P2. **The "fix the gate" half of the 2026-07-28 BOTH ruling — make quickmerge's and a standalone
      `quality-gates.sh --no-fix` run resolve the SAME explicit `ENVIRONMENT` for the same branch context**, so the two
      invocation paths can never again silently diverge (today: quickmerge always exports `development` for any
      non-`main` branch per `scripts/quickmerge.sh:1216-1222`; a standalone run leaves `ENVIRONMENT` unset and the
      bucket resolver defaults to `prod`). Do NOT flip quickmerge itself to `production` — that introduces a new hazard
      (every slot's every commit would touch real prod credentials/buckets during test runs) and is explicitly not the
      intent of this ruling. Instead: make the standalone `quality-gates.sh` entrypoint export the SAME
      branch-conditional `ENVIRONMENT` value quickmerge would use for the current branch (mirroring
      `scripts/quickmerge.sh:1216-1222`'s own branch check), so a developer/agent running the gate standalone always
      verifies under the identical configuration quickmerge will actually gate on — closing the divergence at the source
      rather than only downstream at the sentinel. **Full-completion mandate**: cover every repo's
      `quality-gates.sh`/`base-service.sh` entrypoint, not just the 3-4 repos currently affected by hardcoded prod
      bucket names in tests — this is a shared-script fix, so it protects every repo going forward, not only today's
      known offenders. Add a regression test asserting standalone and quickmerge-invoked runs resolve identical
      `ENVIRONMENT` for the same branch. **Done when**: `scripts/base-service.sh` (or the equivalent shared entrypoint)
      derives `ENVIRONMENT` from the same branch-conditional logic quickmerge uses regardless of invocation path, the
      regression test passes, and `quality-gates.sh` is green in every repo touched. **Shipped
      `unified-trading-pm@4545df4c6` via `ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 1(b)** —
      `qg_resolve_environment()` sourced from BOTH `qg-common.sh` and `quickmerge.sh`'s AUTO-DETECT block; regression
      test `test-qg-environment-resolution-parity.sh` (6/6 assertions); verified live in 2 separate consumer repos.
      Checkbox never flipped here when that landed — closing now, na-eligibility-audit 2026-07-31.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): **KEEP-NA-STALE (already-duplicated)** — all four open
items are extracted into `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md`: Resolution-checklist
items 2 and 5 into its todo 1 (sentinel config-binding + quickmerge/standalone `ENVIRONMENT` alignment), item 4 into its
todo 2 (recovery-guidance correction), and item 3's non-MTDS half into its todo 3 (`deployment-api` +
`strategy-service`). Item 3's MTDS half stays deliberately sequenced behind that batch's Deferred **E7**. Citation
recorded; `assigned_vm` deliberately NOT flipped — that would dispatch a duplicate.

**na-eligibility-audit 2026-07-31** (tranche `ci`, autonomous): **KEEP-NA-STALE bucket confirmed, checkbox gap closed.**
Items 2, 4, and 5 (all confirmed shipped via `ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 1 parts (a)/(b),
`unified-trading-pm@4545df4c6`) are now flipped `[x]` directly in this doc with citations — the citation-gap this bucket
exists for is now closed for those three. Item 3's non-MTDS half (`deployment-api` + `strategy-service`) is CONFIRMED
CLEAN 2026-07-31 (no fix needed, inline-documented) but the box stays open, correctly — the MTDS half remains genuinely
unresolved, still sequenced behind Deferred **E7** (unchanged: "NOT bounded as currently framed" after 5 independent
investigation sessions). 1 open item remains, verdict on it is **KEEP-NA, valid** (genuine unbounded investigation, not
duplicated/stale) — not an archive candidate.

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): **CONFIRMS the verdict above, unchanged.**
Re-read end-to-end; only change since the last marker is the 2026-08-03 context-scout `context_scope` backfill (12
insertions, metadata-only, verified via diff — zero content movement). The residual open item (MTDS half of
Resolution-checklist item 3) is deliberately sequenced behind the shared blocker documented in
`mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md` /
`mtds_deployment_env_race_survives_single_worker_2026_07_23.md` (both re-confirmed KEEP-NA this same run), per the
explicit 2026-07-26 operator sequencing ruling cited above. Still KEEP-NA, valid — not KEEP-NA-STALE (the citation gap
was already closed 2026-07-31). No RECLASSIFY, no ARCHIVE.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 5 entries resolve on disk and
  remain the minimal-correct set (SSOT + 1 related issue doc + 2 source scripts) — no changes.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator sequencing ruling, cross-doc MTDS blockers, prior
verdicts stand

**round-11 RECLASSIFY sweep 2026-08-09** (tranche `ci`): KEEP-NA, valid — re-checked against today's accumulated
precedents (IAM self-service, D16 all-repos, S5.1 tiering, AO-dispatch-by-default, escalation-N=3-days,
reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks); none apply. The one residual open
item (Resolution-checklist item 3's MTDS half) remains deliberately sequenced behind the same unresolved MTDS
DEPLOYMENT_ENV race documented in `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md` /
`mtds_deployment_env_race_survives_single_worker_2026_07_23.md` (both re-confirmed KEEP-NA in this same round-11 pass) —
a 2026-07-26 operator sequencing ruling, not a stale gate any of today's precedents touch. No RECLASSIFY, no
satellite-extraction. No ARCHIVE.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:a75fad86ecf310c3]: KEEP-NA,
valid — Resolution-checklist item 3's unified-trading-library half is shipped+verified; deployment-api/strategy-service
half is confirmed clean (no fix needed, 2026-07-31). The sole remaining open sub-item is the market-tick-data-service
half, deliberately sequenced behind an explicit dated 2026-07-26 operator sequencing ruling (cited: 'resolved
autonomous_session_operator_decisions_2026_07_25.md entry #29, option A') that holds this half until the MTDS
DEPLOYMENT_ENV race investigation's own next step runs, since the 2 MTDS tests are the only known reproducer of a real
env-leak and fixing them first risks masking the leak before its cause is confirmed. Verified both cited blocker docs
are real and still open: mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md (status: open) and
mtds_deployment_env_race_survives_single_worker_2026_07_23.md (status: open).
