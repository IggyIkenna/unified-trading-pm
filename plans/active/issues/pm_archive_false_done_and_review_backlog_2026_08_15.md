---
doc_type: issue
title: Archive False-Done Sweep + Unresolved "Chunks 1/2 + Phase B" Reference
summary:
  Two findings from a read-only production-verification audit's item 8 — a second confirmed false-"done" claim in the
  plans/archive corpus (same fabricated PortfolioRebalancer/DeFiVaultRebalancer subsystem as an already-known 2026-03-27
  example, now also found in a 2026-03-10 doc), and an unresolved "Chunks 1/2 and Phase B full code review" reference
  that an exhaustive corpus + git-log search could not locate. The pytest-wrong-venv sub-finding traced to its
  March-2026 origin incident and the hard rule it already produced — no new action needed, historical only.
status: open
nature: process
archive_exempt: true
resolved_by:
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [audit, verification-debt, plan-hygiene, false-done, archive]
related:
  [
    /plans/archive/2026_08/issues/execution_service_verification_debt_findings_2026_08_15.md,
    /plans/archive/2026_08/issues/strategy_service_verification_debt_findings_2026_08_15.md,
    /plans/archive/recon_rebalancing_order_recovery_2026_03_10.plan.md,
    /plans/archive/defi_transfers_and_gas_fees_2026_03_27.plan.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
effort: medium
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/recon_rebalancing_order_recovery_2026_03_10.plan.md,
    /plans/archive/defi_transfers_and_gas_fees_2026_03_27.plan.md,
    /plans/archive/unit_tests_and_test_failure_action.plan.md,
  ]
supersedes:
superseded_by:
depends_on:
source: production_verification_debt_audit_2026_08_15
assigned_role: review
drift_direction: advance-code
---

# PM Archive False-Done Sweep + Unresolved Reference (2026-08-15 Audit)

> Read-only production-verification audit, item 8. No fixes applied — findings scoped below for AO/operator to decide
> next steps. Small plan (2 todos); archival folded into the audit todo's own done-when rather than a separate companion
> finalize plan.

## Findings → todos

- [x] [REVIEW] P2. Sweep `plans/archive/*_2026_03_*.plan.md` (~160 docs) for further false-"done" claims following the
      exact pattern already confirmed TWICE: `plans/archive/recon_rebalancing_order_recovery_2026_03_10.plan.md`
      (2026-03-10) and `plans/archive/defi_transfers_and_gas_fees_2026_03_27.plan.md` (2026-03-27) both claim a
      `PortfolioRebalancer`/`DeFiVaultRebalancer` implementation that never existed anywhere in the codebase
      (`rg -l 'class PortfolioRebalancer'` returns only the plan files themselves). An initial spot-check of 16 archived
      plans from this era found these 2 hits and no other false-done claims (everything else checked out or was a
      legitimate, evidenced relocation/refactor) — a fuller sweep of the full ~160-doc March-2026 cluster was explicitly
      out of scope for that spot-check. Repo: unified-trading-pm. Done-when: a report artifact (or this todo's own
      Progress Log entry) lists every doc checked, the specific deliverable(s) spot-checked per doc, and either confirms
      no further false-done claims exist in the cluster or lists each new one found (class/file name claimed + confirmed
      absent); once done, run the standard archival ritual on this doc's own checkbox reconciliation in the same commit.
      ✅ DONE 2026-08-15 — full 178-doc corpus swept (see Progress Log for method + coverage). 3 new candidate
      false-done instances found (2 caveated, pending verification — filed as follow-up todos below); everything else
      checked out clean or was a legitimate rename/relocation.

- [x] [REVIEW] P2. Correct the false-done claim in
      `plans/archive/sports_integration_06_strategy_execution_gcs_migration_2026_03_25.plan.md` (id
      `p2-ml-strategy-wiring`) — claims `MLSportsStrategy` (`strategy_service/engine/strategies/sports/ml_sports_strategy.py`)
      exists and reads ml-inference output; confirmed absent workspace-wide
      (`grep -rlP 'class MLSportsStrategy\b' --include='*.py'` and `find . -iname ml_sports_strategy.py` both 0 hits).
      The actual sports strategies directory (`strategy-service/strategy_service/engine/strategies/v2/`) contains
      `sports_arb_dutching.py`/`sports_value_betting.py` instead — not a rename, a different (non-ML) strategy set was
      built. Repo: unified-trading-pm. Done-when: annotate the archived doc's entry
      (`REVERTED/CORRECTED by review 2026-08-15 — class never implemented`) and note in this doc's Progress Log whether
      an ML-probability-based sports strategy is still-needed-and-missing (file a fresh AO-eligible build todo) or
      superseded by the existing rule-based strategies (no further action).
      ✅ DONE 2026-08-15 — annotated `plans/archive/sports_integration_06_strategy_execution_gcs_migration_2026_03_25.plan.md`'s
      `p2-ml-strategy-wiring` entry (same commit). NOT missing and NOT superseded by the rule-based strategies
      specifically — superseded by a different, also-ML-based architecture-v2 archetype (`ML_DIRECTIONAL_EVENT_SETTLED`,
      real + substantive/169 lines/no stubs, wired to 3 prod-labeled sports slots). See Progress Log for full evidence.

- [x] [REVIEW] P3. Verify + correct the claim in `plans/archive/contract_completeness_checker_2026_03_10.plan.md` (id
      `write-check-uic-completeness`) that `unified-internal-contracts/scripts/check_uic_completeness.py` was created
      (commit `94411e6` cited) — the `unified-internal-contracts` repo/dir is absent from the current workspace
      entirely, and `find . -name check_uic_completeness.py` returns 0 hits. Lower confidence than the item above:
      `codex/10-audit/_archive/unified-internal-contracts.yaml` suggests the repo was later formally retired, which
      could legitimately explain the absence (deleted-on-retirement, not fabricated) rather than a genuine false-done.
      Repo: unified-trading-pm. Done-when: confirm via git history (a non-shallow clone or `gh api` commit lookup for
      `94411e6`) whether the script genuinely existed pre-retirement; annotate the archived doc accordingly either way
      (confirmed-built-then-retired vs. confirmed-fabricated).
      ✅ DONE 2026-08-15 — CONFIRMED-BUILT-THEN-RETIRED, not fabricated. `gh api repos/IggyIkenna/unified-internal-contracts`
      confirms the repo still exists on GitHub (private; simply not cloned into this workspace), and
      `gh api repos/IggyIkenna/unified-internal-contracts/commits/94411e6` confirms commit
      `94411e6c71b833e7db059d12d4347a40630a9cd0` (2026-03-10T13:35:53Z) genuinely added
      `scripts/check_uic_completeness.py` (178 lines, file status "added"). The repo was later formally eliminated —
      merged into unified-api-contracts as the `unified_api_contracts.internal` subpackage (2026-03-26, per
      `codex/10-audit/_archive/unified-internal-contracts.yaml`) — which explains the absence. Annotated the archived
      doc's `write-check-uic-completeness` entry with a `verified:` field recording this evidence (same commit).

- [x] ✅ [REVIEW] P3. Verify + correct the claim in `plans/archive/operational_config_migration_2026_03_11.plan.md` (id
      `update-code-references`) citing `catalogue_updater.py` in instruments-service plus commits
      `c12c35e`/`824e723`/`07e1044`/`3a41740`/`3ba90bf` — no `catalogue_updater.py` (or an obvious rename) found
      anywhere in the workspace. Repo: unified-trading-pm. Done-when: check the cited commits against instruments-service's
      full git history (shallow clone was inconclusive) to confirm whether the path was renamed/deleted post-hoc
      (legitimate) or the claim was fabricated (genuine false-done); annotate the archived doc accordingly.
      ✅ DONE 2026-08-15 — CONFIRMED-BUILT-THEN-SUPERSEDED-VIA-REFACTOR, not fabricated. `gh api` against
      instruments-service on GitHub confirms both `c12c35e` and `824e723` genuinely made the claimed edits
      (2026-03-11). `catalogue_updater.py` was created 2026-03-08 and deleted 2026-03-24 (commit `29f34ff083`,
      "production-ready instruments-service ... per-bucket ManifestWriter catalogue") as part of a documented
      refactor, not fabricated or silently dropped. Annotated the archived doc's `update-code-references` entry with
      a `verified:` field (same commit).

- **[OPERATOR] P3. CANCELLED — SUPERSEDED 2026-08-22 (D115 ruling: operator did not locate the "Chunks 1/2 and Phase
      B full code review" artifact either — closed as chat-only/unresolvable; the search was exhaustive, no pointer
      exists).**

## Progress Log

- **2026-08-15**: Filed from a read-only production-verification-debt audit (8-item priority list, this doc covers item
  8's PM-archive/plan-hygiene sub-findings). Sub-task B of the original item 8 (an agent running pytest directly against
  the wrong venv, twice) traced to its origin incident, `plans/archive/unit_tests_and_test_failure_action.plan.md`
  (2026-03-09/10) — 3 documented wrong-workspace-venv false-pass/false-fail incidents that directly produced today's
  "never run pytest directly" hard rule — plus a distinct, later 2026-07-29 CI-capacity-crisis incident of other slots
  bypassing `quality-gates.sh`. Both are already resolved/historical; no new todo filed for that sub-finding. Companion
  docs from the same audit: `execution_service_verification_debt_findings_2026_08_15.md`,
  `strategy_service_verification_debt_findings_2026_08_15.md`.

- **2026-08-15 (full sweep)**: Ran the full ~178-doc `plans/archive/*_2026_03_*.plan.md` sweep (via a delegated
  research agent for the mechanical extraction/verification pass; results re-read and reconciled here). **Method**: (1)
  `grep -l "status: done"` across all 178 docs → 79 docs actually carry `status: done` stream entries (the other ~99
  have none of this shape, so carry no falsifiable "implemented X" claim); (2) extracted all 340 `status: done` entries
  from those 79 docs; (3) regex-mined every entry for `class X` mentions, `Create|Add|Implement <PascalCaseName>`
  patterns, and `*.py` file-path tokens (13 class candidates + 236 file-path tokens ≈ 249 distinct named artifacts); (4)
  existence-checked every one workspace-wide (`grep -rP 'class <Name>\b' --include='*.py'` / `find … -iname <path>`,
  excluding `.venv` and the plan files themselves); (5) manually triaged every MISSING result against its doc's full
  context to separate genuine creation-claims from delete-lists / "port FROM this archived file" references (several
  sports-integration docs had MISSING hits that were actually delete-list or port-source references, correctly
  excluded).
  **Result**: 3 new candidate false-done instances found (1 high-confidence — `MLSportsStrategy`, filed as a P2
  follow-up above; 2 lower-confidence/caveated — `check_uic_completeness.py` and `catalogue_updater.py`, both
  plausibly explained by later repo retirement/rename that a shallow clone's git history can't disambiguate, filed as
  P3 follow-ups pending git-history verification). Everything else spot-checked (13 class candidates fully resolved,
  incl. `PnLResidualEmitter`, `BestExecutionEvent`, and 13 PBMS/strategy-service cross-venue-aggregation classes — all
  present, some legitimately relocated to `strategy-service/strategy_service/position/core/`) came back clean.
  **Coverage caveat (stated honestly, not closed as 100%)**: the 249-artifact regex-mining pass covered the full
  corpus, not a sample — but it only catches claims phrased with a matchable class/file-path token. A "done" claim
  written as pure prose with no code-span (e.g. "wired the aggregator into the pipeline") would not have been caught by
  this pass and was not separately hunted per-doc. This closes the falsifiable-artifact-pattern sweep the todo asked
  for; a residual risk of prose-only false-done claims remains un-swept, noted here rather than silently claimed clean.
  This doc stays `active` (not archived) — 3 new open follow-up todos above, plus the pre-existing OPERATOR todo.

- **2026-08-15 (todo `p2-ml-strategy-wiring`, review slot 7)**: independently re-verified the absence before touching
  anything (0 hits, same two commands the audit already ran) — the false-done claim is real. Annotated
  `plans/archive/sports_integration_06_strategy_execution_gcs_migration_2026_03_25.plan.md`'s `p2-ml-strategy-wiring`
  entry with a `correction:` field (`REVERTED/CORRECTED by review 2026-08-15 — class never implemented`), mirroring
  the exact style already established on the sibling `defi_transfers_and_gas_fees_2026_03_27.plan.md` false-done
  fix.
  **Resolved the still-needed-vs-superseded question — neither offered box, a third answer**: an ML-probability-based
  sports strategy is NOT still-needed-and-missing (no build todo filed), but it is also not simply "superseded by the
  existing RULE-based strategies" as the todo's own phrasing assumed — it is superseded by a *different*, also
  ML-based system: the architecture-v2 `ML_DIRECTIONAL_EVENT_SETTLED` archetype
  (`strategy_service/engine/strategies/v2/ml_directional/event_settled.py::MLDirectionalEventSettledEngine`).
  Verified substantive, not a stub: 169 lines, 0 `NotImplementedError`/`TODO`/`FIXME` markers, real
  `on_tick`/`_select_outcome`/`_evaluate_edge`/`_compute_stake` methods — and wired to 3 production-labeled sports
  slots in `archetype_slots_sports.py` (`unity-epl-1x2-gbp-v5-prod`, `unity-epl-matchwinner-gbp-v5-prod`,
  `betfair-epl-halftime-gbp-v5-prod`). The described logic matches closely: model P(outcome) vs vig-free implied
  odds, confidence/max-odds gates, fractional Kelly stake, covering 1X2/O-U/BTTS/1H markets — the same shape the
  2026-03-25 plan described for the never-built `MLSportsStrategy`.
  **Adjacent fix (same commit, per the misleading-doc hard rule)**:
  `/codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md` carried a stale
  `implementation_status: design` (corrected to `code-shipped`, the value this corpus uses for "real code exists")
  and cited a superseded "(target)" code-module path (`.../ml_directional_event_settled_engine.py`, which does not
  exist) instead of the real shipped path — both corrected.
  **Checked but not corrected**: the issue doc's own claim above (that the v2 directory "contains
  `sports_arb_dutching.py`/`sports_value_betting.py`") is directionally right but imprecise — both files exist, just
  nested one level down in `arbitrage_structural/` and `rules_directional/` respectively, not directly in `v2/`.
  Trivial and not misleading enough to warrant a further edit.
  **Not independently re-verified**: whether the 3 sports slots are *currently live-trading* in production vs. just
  configured (the `-prod` slot-label suffix is suggestive but not proof of live trading status) — `code-shipped` was
  chosen over `live` in the codex fix specifically to avoid over-claiming a runtime fact I did not check.

- **2026-08-15 (todo `write-check-uic-completeness`, review slot 7)**: verified via `gh api` against the still-extant
  (but no-longer-locally-cloned) `IggyIkenna/unified-internal-contracts` GitHub repo — commit
  `94411e6c71b833e7db059d12d4347a40630a9cd0` (2026-03-10T13:35:53Z) genuinely added
  `scripts/check_uic_completeness.py` (178 lines, confirmed via the commit's `files[].status: "added"`). This is
  CONFIRMED-BUILT-THEN-RETIRED, not a false-done: the repo was later formally eliminated (merged into
  unified-api-contracts as `unified_api_contracts.internal`, 2026-03-26, per
  `codex/10-audit/_archive/unified-internal-contracts.yaml`), which is why `find` and a workspace grep return 0 hits
  today. Annotated `plans/archive/contract_completeness_checker_2026_03_10.plan.md`'s `write-check-uic-completeness`
  entry with a `verified:` field capturing this evidence (same commit). No correction to the archived doc's
  substantive DONE claim was needed — only the confirmation itself. The doc stays `status: open` — 2 todos remain
  (the `operational_config_migration` P3 `catalogue_updater.py` verification, and the `[OPERATOR]` "Chunks 1/2 and
  Phase B" naming ask).

- **2026-08-15 (todo `update-code-references`, review slot 3)**: verified via `gh api` against instruments-service on
  GitHub (the local clone is shallow and inconclusive, per this todo's own text) — both cited commits are genuine.
  `c12c35e` (a pre-history-rewrite SHA — this repo underwent a documented history rewrite on 2026-08-05, per the
  `instruments-service.stale-pre-history-rewrite-20260805T112618Z` clone directory seen elsewhere in this workspace;
  the identical change is reachable post-rewrite as `9e752677d4`, same date/message) genuinely modified
  `instruments_service/catalogue_updater.py` + `pyproject.toml` on 2026-03-11T21:41:12Z ("fix: update catalogue path
  to unified-trading-pm/configs/"); `824e723` genuinely modified `.github/workflows/quality-gates.yml` the same day.
  Traced the file's full lifecycle via a path-filtered commit-history query (`gh api
  repos/.../commits?path=instruments_service/catalogue_updater.py`): CREATED 2026-03-08 (`724990c60e`,
  "feat(catalogue): add catalogue_updater post-batch hook"), correctly updated 2026-03-11 exactly as claimed, then
  REMOVED — not renamed (`previous_filename: null`) — 2026-03-24 by `29f34ff083` ("feat: production-ready
  instruments-service — ... per-bucket ManifestWriter catalogue ..."), which deleted both `catalogue_updater.py`
  and its test file as part of a documented architectural refactor superseding it with a `ManifestWriter`-based
  catalogue. **CONFIRMED-BUILT-THEN-SUPERSEDED-VIA-REFACTOR, not fabrication** — mirrors the sibling
  `write-check-uic-completeness` pattern exactly. Annotated
  `plans/archive/operational_config_migration_2026_03_11.plan.md`'s `update-code-references` entry with a
  `verified:` field (same commit). This doc stays `status: open` — only the `[OPERATOR]` "Chunks 1/2 and Phase B"
  naming ask remains, and it cannot be resolved by a dispatched worker per its own text (genuine ambiguity, no
  data-derivable answer).

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **2026-08-22 — ruling D115 ("Chunks 1/2" review artifact)**: OPERATOR-RULED 2026-08-21 — operator did not locate
  the artifact either. Close as chat-only/unresolvable (the search was exhaustive; no pointer exists). Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **2026-08-22 — archive_exempt justification**: D115's ruling converts this doc's sole remaining open todo
  ([OPERATOR] P3, "Chunks 1/2") to CANCELLED, leaving 0 open todos. Per the ruling-sweep task's own scope, doc
  archival is a separate ritual not performed here — `archive_exempt: true` added to frontmatter so this
  intentional 0-open-todos state doesn't trip `check_archive_candidates`; a future archival pass may still pick
  this doc up on its own schedule.
