---
doc_type: issue
title: Batch-4 archived-plan (strategy/UI) residual open items — successor mapping + verification gaps
summary: >-
  Plan-discipline audit of 5 archived strategy/UI plans (part of the batch-4 P3 sweep in
  pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md) whose residual `- [ ] ` items don't have an obvious
  1:1 active-plan owner. Two are HUMAN-gated confirmations pending operator sign-off; three have code that appears to
  have shipped since the plan was archived but the specific residual checkboxes were never verified/flipped or split
  across multiple current owners.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-discipline, governance, strategy, ui, dart, mtds]
related: []
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: planning
resolved_by:
locked_by:
source: [pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

Auditing 5 of the 8 archived strategy/UI plans in the batch-4 sweep, none of their residual open `- [ ]` items has a
clean, verifiable, single active-plan successor — each needs a distinct follow-up:

## 1. `plans/archive/leveraged_leg_controller_2026_05_01.plan.md` (2 open items)

- Phase A/B/C formal unit tests (holding_wallet override precedence, Solana inner-instruction walk, L2 book shape
  projection) — currently smoke-tested only via the surrounding chain, plan itself calls this "recommended next session"
  but no session picked it up.
- features-onchain-service Docker image rebuild so the Cloud Run cron picks up the Phase B inner-instruction walker —
  operator/deployment-side, not a code change.

No active plan references either item today (grepped `holding_wallet`, `inner-instruction`, `LST reward` across
`plans/active/`).

## 2. `plans/archive/transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22.plan.md` (2 open items)

Both are `[HUMAN] P2` gates: (a) post-merge validation re-run of the TM backfill VM comparing cold vs warm-cache
wall-clock, (b) approving `[unlock-plan]` once (a) confirms the cache-hit speedup. Neither can be honestly checked off
by an agent — they require an operator to actually run the comparison and sign off. Per the parent issue doc's own note,
these need "operator confirmation ... before checking them off" — I have no evidence either happened, so I'm not
fabricating a checkmark.

## 3. `plans/archive/ui_quality_gates_parity_2026_03_16.plan.md` (25 open items)

Phase 1-2 SSOT artifacts this plan proposed (`scripts/quality-gates-base/base-ui.sh`,
`scripts/quality-gates-base/eslint.config.base.js`) **already exist in the repo today** — the core hardening shipped,
just not via this plan's tracked commits, and the checkboxes were never flipped.
`codex/06-coding-standards/ui-testing-layers.md` is now the living UI-testing SSOT (post-dates this plan by 4 months).
But the granular residual items (any-type cleanup, console.log removal, per-UI test-depth floors, coverage-exclusion
audit, cursor rule, codex doc) can't be trusted as done-by-osmosis without re-auditing against current UI repos — 4
months of drift is too long to blind-close.

## 4. `plans/archive/combo_bundle_aggregation_2026_04_30.plan.md` (16 open items)

The core writer-side bundling **shipped in code**:
`market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py:256` —
`_UNDERLYING_PARTITIONED_TYPES` includes `"combo"` with an inline comment confirming "Now bundle by underlying (one
combos.parquet per (date, data_type, underlying))". But the migration-script items (`rebundle_combo_parquets.py`,
dry-run, cutover, reader-compat-shim removal, manifest reconciler for stale per-combo rows) have no evidence of having
run — `tradfi_consolidated_closeout_2026_07_18.md` (active) already tracks adjacent combo/manifest defects (1,154,976
tick-side `UD_*` manifest combos) and is the natural current owner to fold this residual verification into, but I did
not find explicit confirmation the 2026-04-30 migration itself ran.

## 5. `plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md` (67 open items, genuinely mixed

domain)

Frontmatter declares `superseded_by: marketing_site_three_route_consolidation_2026_04_26.md` (active, `plans/ai/`),
which is real and does own the client-onboarding/questionnaire/FOMO-funnel work streams (A + B early phases). But the
plan's tail (Phase 9: `archetype_capability.py` VOL/MARKET_MAKING/PORTFOLIO archetype additions, `bespoke_capable`
field, admin-assignment model) is a completely different domain — strategy archetype-capability taxonomy — which is
owned today by `plans/active/capability_wizard_and_manifest_2026_06_11.md` (active; its `ARCHETYPE_CAPABILITY_REGISTRY`
extraction work directly overlaps). A single successor reference would misrepresent one of the two halves, so this needs
a real owner audit of which of the 67 items landed under which of the two active plans before either can be honestly
closed.

# Why it matters

These are the checker's `C-archive-no-successor` violations — the archived plans have DEFERRED/out-of-scope language but
no successor reference, so `check_plan_discipline.py` counts them against the ratchet. A banner naming a wrong or
partial successor would be false documentation (worse than the missing banner); a generic "not applicable" banner would
be fabricated completion for these 5 (none has zero open items). Real closure needs the todos below actioned.

# Recommended decision

Add the `## Deferred work — migrated to:` banner on each of the 5 source plans pointing at this issue doc (accurate —
this doc is where the real follow-up now lives), then work the todos below to resolve them properly, at which point this
issue doc can point to whichever plan actually ends up owning each thread.

## Todos

- [x] ✅ [SCRIPT] P3. Write Phase A/B/C formal unit tests for `LeveragedLegController`'s holding_wallet override
      precedence, Solana inner-instruction walk, and L2 book shape projection (currently only smoke-tested via the
      surrounding chain) — see `plans/archive/leveraged_leg_controller_2026_05_01.plan.md` § "Outstanding". (repo:
      features-onchain-service) — **done-by-osmosis, verified, no new code needed.** `features-onchain-service` no
      longer exists as a repo (consolidated into `features-service`, confirmed via
      `unified-trading-pm/workspace-manifest.json`'s `removedEntries.features-onchain-service`
      `archived_into: features-service`); the actual code lives at
      `features-service/features_service/onchain/collectors/{parquet_dust_loader,chain_event_scanners}.py` and
      `execution-service/execution_service/algo_library/mtds_book_provider.py` (Phase C, per the archived plan's own
      text — it was never in features-onchain-service to begin with). All three phases already have comprehensive,
      formal, pinned unit tests, added by later general coverage-raising waves that never got linked back to this
      residual item: - **Phase A** (holding_wallet precedence):
      `features-service/tests/onchain/unit/test_parquet_dust_loader.py` `TestLstHoldingWalletFromParams` (6 tests:
      identity-wins, params-fallback-when-identity-missing, params-fallback-when-identity-empty, no-wallet-anywhere,
      empty-params-dict, params-not-a-dict) — pins the exact 3-level precedence documented in
      `lst_holding_wallet_from_params`'s docstring. - **Phase B** (Solana inner-instruction walk):
      `features-service/tests/onchain/unit/test_chain_event_scanners.py` `TestSolanaChainEventScanner` +
      `TestSplTransferGate` (89 `def test_` total in the file) — covers `transferChecked` + legacy `transfer` types, the
      inner-instructions pass, the post-balance-diff fallback pass, malformed/non-dict/non-list skip branches,
      mint/decimals extraction, amount parsing, and the distributor-address gate. Last touched
      `features-service@1a249e23` (2026-06-10, "raise unit coverage 81.3->86.2%, +955 tests"). - **Phase C** (L2 book
      shape): `execution-service/tests/unit/algorithms/test_mtds_book_provider.py`, section explicitly labelled
      `# L2 (mbp_10) book shape — Phase C` (8 tests: schema detection via `bid_px_00`/`ask_px_00`, default `l2_levels=5`
      walk, the `l2_levels` knob, schema-smaller-than-knob capping, null-price skip, top-level-null → None, decimal
      precision, L0/tbbo fallback).

      **Verification run**: `execution-service`'s full unit suite (`quality-gates.sh --test`) completed clean —
                          7876 passed, 21 skipped, 1 xpassed, 0 failed (includes the Phase C tests above).
                          `features-service`'s full suite (16k+ tests) could not be driven to a clean finish in-session — two attempts
                          both died to shared-host resource contention (other slots' concurrent QG runs observed on the same host) at
                          ~66-94% progress with **zero** `FAILED`/`F` markers in either partial run; both target test files were also
                          confirmed importable and syntactically sound by direct read. Re-running `features-service` QG to full green is
                          left as a lightweight follow-up for whoever next touches that repo — it is a verification-only gap (no code
                          change pending), not a code gap.

- [x] ✅ [HUMAN] P3. **RESOLVED 2026-07-21 — premise moot, not a manual action.** `features-onchain-service` no longer
      exists as a standalone repo (`git subtree`-merged into `features-service` at `b0e63608` "feat(onchain): import
      features-onchain-service into features-service via git subtree", 2026-05-08, imports rewritten
      `features_onchain_service`→`features_service.onchain` at `b5c4b721`), and `features-service`'s own Cloud Build
      trigger (`features-service-build`, `cloudbuild.yaml`) auto-rebuilds + pushes
      `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/features-service:latest` on every
      merge to `main` — there is no manual `:latest` push step to trigger. Verified the currently-live `:latest` image
      already contains the Phase B inner-instruction walker: the last SUCCESSFUL Cloud Build
      (`69789dfb-aacc-407a-85b4-1fc9ce330880`, finished 2026-07-21T16:10:28Z, pushed `:latest`) built commit `889ce87`
      on `main`, and `git merge-base --is-ancestor b0e63608 889ce87` confirms the subtree-merge (carrying
      `tests/onchain/unit/test_solana_inner_instruction_walk.py` +
      `features_service/onchain/collectors/chain_event_scanners.py`) is an ancestor — the image the cron would pull
      today already has this code, and has for the ~2.5 months since the merge (every successful build since included
      it). (Not blocking this item, noted for transparency: the _next_ build after 69789dfb,
      `a2c85a95-55ae-436f-92de-7793a736fc24` at 16:29:01Z, FAILED on an unrelated
      `ImportError: cannot import name     'candle_read_prefixes' from 'unified_trading_library'` in
      `tests/delta_one/unit/*` — confirmed transient cross-repo version-skew, not a real break: the symbol exists
      correctly in UTL's current source (`unified_trading_library/config_interface/paths/registry.py:429`, landed
      `af3dc71` at 16:23:16Z — published just ahead of that build's dependency pull); since Cloud Build only pushes
      `:latest` after quality-gates passes, that failed build never overwrote the good image — `:latest` today is still
      889ce87.) (repo: features-service)
- [x] ✅ [HUMAN] P3. **Measurement done — agent-executed per operator's explicit blocked-answer authorization
      (`BLK-f76f2ad0`, "run the VM comparison and report real numbers, but STOP HARD before [unlock-plan]").** Ran
      `launch-transfermarkt-backfill-vm.sh --entity PLAYER_VALUES 2025-06-01 2025-06-14` TWICE back-to-back (the
      original April fix's own before/after tarball comparison point is long gone — it shipped 3 months ago and has been
      baked into every tarball since; today's meaningful test is run-1-vs-run-2 on the SAME window).

      **Run 1** (`tm-backfill-20260721-195637`, cold except for 4 already-cached lead dates): task-start
              19:59:24Z → `Batch complete: 13 results collected` at 21:10:09.936Z = **4245.9s (1h10m46s)**. Of the 14 dates,
              7 were genuine "trigger days" needing real multi-league RapidAPI fetches (06-05 alone took ~16min/594 teams;
              06-07/10/11/12/13 each took several more minutes), 6 were non-trigger fast-skips, and **06-09 hit a real infra
              error** (`ManifestConsolidatorStaleError` — filed separately, see
              `manifest_consolidator_stale_sports_bucket_2026_07_21.md`) caught cleanly by shard-level failure isolation
              (run continued to 06-10 without crashing) but left 06-09 uncaptured.

              **Run 2** (`tm-backfill-20260721-211655`, launched immediately after run 1 finished): task-start
              21:19:36.647Z → `Batch complete: 14 results collected` at 21:33:47.626Z = **851.0s (14m11s)**. Decisive
              result: EVERY date that took real multi-minute API work in run 1 (05/06/07/10/11/12/13) fast-skipped in
              seconds in run 2 — the cache-hit fix correctly triggers off "has this actually been captured", not off the
              trigger-day schedule, so freshly-captured data short-circuits regardless of what day it is. The only real work
              in run 2 was re-fetching 06-09 (2m45s — legitimately necessary, since run 1 never actually captured it due to
              the infra error, not a caching failure).

              **Speedup, reported both ways (honestly, not cherry-picked)**:
              - Raw run1-vs-run2 total: 1 − (851.0 / 4245.9) = **79.95% reduction — technically just under the archived
                plan's ≥80% bar** (by 0.05 percentage points).
              - Excluding the one legitimately-necessary 06-09 re-fetch (851.0 − 165.3 = 685.7s vs 4245.9s): **83.85%
                reduction — clearly exceeds ≥80%.**

              **My read, not a decision**: the raw number missing 80% by a hair is fully explained by one date's real,
              necessary catch-up work from an unrelated infra hiccup, not by the cache mechanism underperforming — every
              other previously-slow date sped up by >99%. But this is exactly the judgment call that belongs to a human,
              not an agent self-grading its own validation. **`[unlock-plan]` on
              `transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22.plan.md` is explicitly NOT granted here
              — operator approval needed as a separate, distinct action`, citing whichever of the two speedup
              numbers above you find dispositive.** (repo: instruments-service, deployment-service)

- [x] ✅ [DOCS] P3. Re-audit `ui_quality_gates_parity_2026_03_16.plan.md`'s 25 residual items against the CURRENT state
      of `codex/06-coding-standards/ui-testing-layers.md` + the 11 consumer UI repos (any-type violations, console.log
      usage, per-UI test-depth floors, coverage-exclusion comments, cursor rule, codex doc) — the SSOT artifacts
      (base-ui.sh, eslint.config.base.js) already shipped but the granular items were never verified. (repo:
      unified-trading-system-ui) — **audited all 25 against current reality: 12 DONE, 8 MOOT, 5 STILL-OPEN (one of which
      surfaced a real, live, workspace-wide gate bug, filed separately).**

      Of the "11 consumer UI repos" the plan targeted, only 2 (`deployment-ui`, `unified-trading-system-ui`) still
                  exist as live surfaces — everything else (`unified-trading-ui-kit`, client-reporting-ui,
                  execution-analytics-ui, live-health-monitor-ui, etc.) was archived/consolidated per
                  `unified-trading-pm/workspace-manifest.json`, which is why 8 of the 25 items are MOOT (targeted a
                  now-nonexistent repo/artifact: `p3-uikit-tests-deployment`, `p6-setup-sh-ui-kit-dist`,
                  `p6-manifest-uikit-testing-level`, `p7-qg-uikit`, `p7-qg-consumer-parallel`, plus 3 more).

                  **DONE (12)**: `p1-typecheck-step-rename`/`p1-build-step-rename` (evolved into a different but equivalent 8-stage
                  `[0/6]…[5/6]` numbering, `base-ui.sh` current), `p1-eslint-version-check` (`base-ui.sh:202-203` captures +
                  prints `ESLINT_VER`), `p2-propagate-eslint` (both live repos carry `eslint.config.base.js`),
                  `p4-fix-ts-ignore` (0 hits, both repos), `p4-page-test-depth` (far exceeded — 75 + 286 test files),
                  `p5-coverage-audit`/`p5-coverage-exclusion-comment` (`deployment-ui`'s exclusions are reason-commented;
                  `unified-trading-system-ui` has no exclusions to audit), `p6-rollout-eslint-in-unified` (mechanism shipped +
                  ran), `p6-cursor-rule` (shipped under a different filename,
                  `.cursor/rules/ui/ui-quality-gates-typescript.mdc` + 4 sibling rules), `p6-codex-doc` (absorbed into
                  `codex/06-coding-standards/ui-testing-layers.md` rather than the originally-proposed filename), `p7-qg-pm`
                  + `p7-rollout-first` + `p7-setup-all-ui` (artifacts they'd produce are present and working in both live repos).

                  **STILL-OPEN (5, low-value except the flagged one)**: `p6-setup-sh-ui-vitest-check` (no `UI.5` step in
                  `setup.sh`), `p6-rollout-vitest-template` (no propagation mechanism, but moot in practice — both live repos
                  already have valid configs), `p6-run-all-setup-ui-flag` (`--ui-only` literal flag absent, but `--repos=` already
                  achieves the same effect with only 2 UI repos left) — none of these three block anything today, not worth
                  independent follow-up at P3. The remaining two (`p4-fix-any-types`, `p4-fix-console-log`) plus
                  `p4-chart-theme-check` are DONE for `deployment-ui` but genuinely open for `unified-trading-system-ui` — **and
                  the reason they're open is a real bug, not neglect**: `base-ui.sh:337` gates its whole codex-compliance block on
                  `[ -d "src" ]`, and `unified-trading-system-ui` uses the Next.js `app/` router (no `src/` at all), so the gate
                  has silently never run for that repo. Filed as its own issue doc (workspace-wide gate bug, not just a
                  per-repo cleanup item):
                  `plans/active/issues/ui_codex_gate_blind_to_app_router_layout_2026_07_21.md`. (repo: unified-trading-system-ui)

- [ ] [SCRIPT] P3. Verify whether the CME combo-parquet migration (`rebundle_combo_parquets.py` dry-run + production
      cutover + reader-compat-shim removal + manifest reconciler for stale per-combo rows) from
      `combo_bundle_aggregation_2026_04_30.plan.md` actually ran — the writer-side bundling shipped
      (`symbol_rules.py:256`) but the historical re-bundle + cleanup steps have no found evidence. Fold into
      `tradfi_consolidated_closeout_2026_07_18.md` if still outstanding. (repo: market-tick-data-service)
- [ ] [DOCS] P3. Split `dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`'s 67 residual items between
      `marketing_site_three_route_consolidation_2026_04_26.plan.md` (onboarding/questionnaire/FOMO funnel, Phases 0-8)
      and `capability_wizard_and_manifest_2026_06_11.md` (Phase 9 archetype-capability taxonomy) — name each item's real
      owner (or a fresh issue doc for whatever lands in neither) instead of a single blanket successor. (repo:
      unified-trading-pm)
