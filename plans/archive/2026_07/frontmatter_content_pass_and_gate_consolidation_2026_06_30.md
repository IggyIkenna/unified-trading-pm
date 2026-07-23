---
doc_type: plan
title:
  Frontmatter content pass + gate consolidation — populate summary/tags/authoritative_for, converge to one blocking
  check
summary:
  Follow-on to the (completed) full-corpus frontmatter coverage. Populate the SOFT content fields the structural pass
  left empty (5,887 items measured 2026-07-03 — summary/tags/authoritative_for PLUS related/status/repos + audit fields;
  one read per doc fills all of them), then make a single comprehensive BLOCKING frontmatter gate (backed by the docspec
  validator engine) and retire the interim warn-only check_docspec_coverage. Nice-to-have (P3) — the high-leverage
  payoff is codex authoritative_for/summary becoming searchable for the codex drift-fixing work.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [frontmatter, docspec, content-pass, gate-consolidation, doc-governance, grep-native]
related:
  [
    ../2026_06/frontmatter_full_corpus_coverage_2026_06_30.md,
    ../2026_06/doc_frontmatter_schema_and_validator_2026_06_24.md,
    ../../epics/agent_operating_framework_master.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-06-30
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: infra-engineer
drift_direction: advance-code
last_updated: 2026-07-04
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    operator decision 2026-06-30 — split the deferred consolidation work out of the completed full-corpus coverage plan
    into its own nice-to-have (P3) plan; that plan is archived complete,
  ]
---

# Frontmatter content pass + gate consolidation

> **✅ COMPLETE + ARCHIVED (2026-07-06).** Every todo shipped; corpus at docspec **HARD=0 SOFT=0 (1,299 live docs)**
> behind the single BLOCKING gate. 5-step archival ritual executed 2026-07-06: **(1)** deferred residuals homed in the
> parent epic (see "Deferred work after 2026-07-06" below — nothing dropped); **(2)** this banner; **(3)**
> codex-alignment verified — the cited SSOT
> [`doc-frontmatter-schema.md`](/codex/11-project-management/doc-frontmatter-schema.md) is in lockstep with
> `scripts/docs/docspec.py` (NATURE 8 incl. `issue`, `implementation_status` elective, doc_type↔path HARD check);
> **(4)** new durable contracts homed in their codex SSOTs (schema doc + `per-tab-worktrees.md`), no CLAUDE.md/sub-agent
> staleness introduced; **(5)** no lock to clear (`locked_by` was empty). Superseding follow-on rides the epic
> [`agent_operating_framework_master`](../../epics/agent_operating_framework_master.md). Body preserved verbatim as the
> provenance record.

The structural coverage is **done + enforced (warn-only)** — see the archived
[`frontmatter_full_corpus_coverage_2026_06_30`](../archive/2026_06/frontmatter_full_corpus_coverage_2026_06_30.md):
every live doc carries a valid `doc_type` + universal-core + per-type fields + valid enums, and
`check_docspec_coverage.py` surfaces any HARD rot (non-blocking). This plan is the **value layer on top**: fill the
content fields that make frontmatter actually answer queries, then collapse to a single blocking gate.

## Why P3 / nice-to-have

The corpus is already HARD-green and rot is surfaced every QG run, so nothing is at risk. The payoff here is _quality of
search_: a populated `authoritative_for` lands an agent on the one right codex SSOT, and `summary` lets it read a
1-liner instead of opening the doc — most valuable right before the codex↔code drift-fixing push. Worth doing, not
urgent.

## Codex SSOTs

- [`/codex/11-project-management/doc-frontmatter-schema.md`](/codex/11-project-management/doc-frontmatter-schema.md) —
  the universal-core + per-type fields + the two-checks lifecycle this plan executes.
- Validator engine: `scripts/docs/docspec.py` (`validate_frontmatter` — SOFT vs HARD); the surviving gate must call it,
  not reimplement it.

## Todos

> **Execution shape (2026-07-03 recalibration — measured, see Progress Log):** the corpus needing content = 1,017 docs /
> 17 MB (~4.2M tok to read); p50 doc = 10 KB, only 36 docs < 2 KB — so NO Haiku/length split (one model, one prompt,
> uniform quality; wrong metadata is worse than empty). **One read per doc fills ALL its content fields** — never run
> per-field passes (3× the read cost). Folder-scoped Sonnet (medium) agents, because the folder ledger is what gives
> `authoritative_for` uniqueness + a consistent tag vocabulary; ~40-60 docs per agent instance, big trees
> (09-strategy/04-architecture/14-customer-journeys) split by subfolder with the ledger handed between chunks. Order by
> churn: codex first (stable + highest leverage), then plans/audit + plans/epics, plans/active LAST; skip dirty /
> recently-pushed docs (other slots), second sweep catches stragglers. Commit+push per folder as it lands.

- [x] [SCRIPT] P3.0 **Mechanical pre-pass — no LLM.** Fill `created` (804 empty) from git first-commit date
      (`git log --follow`, filename-date cross-check for plans); normalize literal `NA` → null on
      `locked_by`/`locked_since`/`depends_on` (29). **Gate**: docspec SOFT `created` + literal-NA counts → 0. — ✅
      unified-trading-pm@8d9167827 (825 files, frontmatter-only one-liners). Evidence: docspec re-sweep post-apply:
      created/locked_by/locked_since/depends_on SOFT = 0/0/0/0; corpus total SOFT 5,887 → 5,053.
- [x] [AGENT] P3.1 **Pilot folder — `codex/11-project-management` (14 docs), operator eyeball gate.** One Sonnet
      (medium) sub-agent fills, per doc in ONE read: `summary`, `tags` (prefer the harvested lexicon),
      `authoritative_for` (codex-ssot; unique across the folder — keep a topic→doc ledger), `related` (sibling
      cross-links), `status` (normalize to the per-type enum; codex current/stale is a judgment from the read), `repos`
      (manifest-validated), + `code_refs` ONLY where the body already cites a path AND the path exists. NEVER guess
      operator fields (`owner`/`verifier`/`supersedes`/`resolved_by`/`source`/estimates) — emit them on a worklist
      instead. **Gate**: operator reviews the pilot diff before any fan-out. — ✅ unified-trading-pm@091318d21 (14 docs,
      frontmatter-only). Evidence: docspec HARD=0 all 14; content-SOFT → 0 except valid-empty `repos`/`related` `[]`;
      authoritative_for corpus-collision-checked. **Fan-out still gated on the operator eyeball of this diff.**
- [x] [AGENT] P3.2 **Fan-out — remaining trees with the pilot prompt.** Per-folder Sonnet agents (≤10 parallel), codex →
      plans/audit (+ audit-result fields `severity`/`audited_scope`/`auditor`/`date` from the body) → plans/epics →
      plans/active last. **Gate**: docspec content-SOFT count (5,887 baseline) → ~0 on targeted trees, measured per
      folder commit. — ✅ 55 Opus lanes (operator override 2026-07-03: Opus not Sonnet; local commits only, single push
      after final QG), ~990 docs, per-lane commits `docs(frontmatter): P3.2 lane NN` (2026-07-03/04). Evidence: final
      docspec sweep 2026-07-04: 1,299 docs, **content-SOFT 5,887 → 306** (residual = valid-empty
      `repos`/`related`/`authoritative_for` `[]` on stubs/superseded/cross-cutting docs + operator-only fields → P3.4);
      HARD = only the 3 pre-existing rot docs (0 introduced); `authoritative_for` collision sweep (`rg --no-ignore`,
      covers the gitignore-shadowed credentials dir): ZERO duplicate phrases corpus-wide; 2 YAML parse breaks
      (colon-space/hash foot-guns) found by the sweep and fixed same-day.
- [x] [SCRIPT] P3.3 **`referenced_by` reverse-link post-pass (codex).** Derive from the corpus link graph AFTER the
      content pass lands (the pass creates new `related` edges). **Gate**: codex `referenced_by` populated mechanically,
      no LLM.
- [x] [OPERATOR] P3.4 **Operator worklist.** Delivered 2026-07-04 — see `## P3.4 Operator worklist` section below.
      **Section A CLOSED by operator policy 2026-07-06** (defaults stand, update-on-use; field-fills are NOT operator
      work). B3 fixed by the zero-pass; B4 + B5 reconciled in docspec. **B1/B2/B6 executed 2026-07-06 on operator
      direction ("do all B1, B2 and B6")** — ✅ unified-trading-pm@09cc91f48: B1 `implementation_status` elective axis
      restored (docspec Req.E + enum + schema §3/§6 + 66 archetype docs, 18 docspec tests green); B2 22 epics re-mapped
      per the `fix_epic_frontmatter_2026_05_21.py` canonical registry (only defi_master keeps `[defi]`); B6 10 runbooks
      → `codex/15-runbooks/` + 4 audits → `plans/audit/results/` (retyped `audit-result`), ~50 inbound refs
      re-relativized, sub-map truth lifted, 5 leave-in-place calls recorded below. Evidence: frontmatter gate green
      1,299/0; full `quality-gates.sh` exit 0; regen index 1,120 docs / graph 3,114 edges (no orphaned links). Residual:
      B7 SUPERSEDED banners stay parked with the archive bonus; B8 codex-drift bodies feed W7.
- [x] [AGENT] P3. **Make the single gate comprehensive — back it by `docspec`, don't reimplement.** Expand the blocking
      `check_frontmatter_schema` to enforce the full schema (universal-core + enums + all doc types incl. codex +
      cursor-rule, and the now-populated content fields) by **calling `docspec.validate_frontmatter()`** rather than
      growing a second hand-rolled validator (avoids two validators drifting). Re-add codex to its default corpus.
      **Gate**: one gate enforces everything docspec checks; corpus stays HARD-green (+ SOFT-green once content lands).
      — ✅ 2026-07-04 (operator-directed): `check_frontmatter_schema.py` rewritten as a thin docspec caller over the
      live trees (codex + plans/active/epics/audit + `*.mdc`; **plans/archive deliberately excluded** — operator
      decision), failing on ANY violation HARD or SOFT; legacy `instructions_ref` check preserved with its exact legacy
      scoping. Evidence: gate green on all 1,298 live docs; full `quality-gates.sh` exit 0 with the gate wired.
- [x] [SCRIPT] P3. **Retire `check_docspec_coverage.py`** once the comprehensive blocking gate is live. **Gate**:
      docspec-coverage removed from `quality-gates.sh`; the single comprehensive blocking check is the sole frontmatter
      gate; schema SSOT banner updated to drop the two-checks lifecycle. — ✅ 2026-07-04: script deleted, QG block
      removed, schema SSOT banner + §11 updated (two-checks lifecycle COMPLETE; blocking gate is the sole frontmatter
      gate).
- [x] [SCRIPT] P3. **agent-role enforcement (separate repo).** Wire the docspec check into the `agent-orchestrator`
      repo's own quality-gates (its `agents/*.md` are not reachable from PM CI). **Gate**: agent-role docs gated
      in-repo.

## P3.4 Operator worklist (delivered 2026-07-04)

### A. Field fills — CLOSED by operator policy (2026-07-06)

> **Operator decision 2026-07-06**: the zero-pass defaults are ACCEPTABLE, not a blocker or real work — runbook
> `owner`/`cadence`/`verifier` and audit `auditor` values get corrected at first actual use of each doc; new blanks get
> defaults the same way. State at closure (measured 2026-07-06): nothing empty (gate green, 1,298 docs / 0 violations);
> 18 runbooks carry the default triple `owner: ikenna` / `cadence: on-demand` / `verifier: operator` (16 `alerting/*` +
> `instruments-live/t1-audit-discrepancy` + `rehearsal-procedure` partial); 13 runbooks have true values lifted from the
> legacy `execution:` sub-map (sub-map line left in place, harmless); `auditor` backfilled from commit identity incl. 2
> raw git identities (`Ubuntu`/`ComsicTrader` = harsh, per git log) — all stand as-is. `last_executed: never` on 25
> runbooks is the honest value (rehearsal backlog, not a fill).
>
> Original sweep counts (2026-07-04, pre-zero-pass), kept for the record:

- `owner`/`cadence`/`verifier` empty on ~29 runbooks each (many carry the values inside a legacy `execution:` sub-map
  docspec doesn't read — decide: lift to top-level keys mechanically, or teach docspec the sub-map). All incident
  runbooks also have `last_executed: never` (rehearsal backlog).
- `auditor` empty on 26 audit-results (body names no auditor).
- `source` (6) / `resolved_by` (5 — incl. 2 RESOLVED issues) / `tier`+`priority`+`parent`+`name` (superseded epics) /
  `status` (5 — incl. `RESOLVED` uppercase on polymarket issue).

### B. Decision items

1. ✅ RESOLVED 2026-07-06 (pm@09cc91f48 — dedicated `implementation_status:` key added as recommended: new ELECTIVE
   requirement tier in docspec — absent-is-fine, enum-validated when present, so 700 non-archetype codex docs don't need
   a noise key; axis restored on all 66 docs from the mapping below) ~~**Archetype maturity axis flattened (57
   docs).**~~ `status:` in `codex/09-strategy/architecture-v2/**` doubled as an implementation-maturity axis; enum
   normalization erased it (recoverable below). Decide: add a dedicated `implementation_status:` key (recommended) or
   accept body-only maturity. Old→new mapping:

- `design` → enum (47): arbitrage-cross-domain-event, carry-basis-dated-inv, carry-basis-dated, carry-basis-perp-inv,
  carry-basis-perp, carry-recursive-borrow-lending-only, carry-recursive-staked, carry-staked-basis-dated, event-driven,
  liquidation-capture, market-making-event-settled, market-making-inventory-skew, market-making-ml-lean,
  market-making-passive-spread, market-making-prediction, market-making-queue-microstructure, ml-directional-continuous,
  ml-directional-event-settled, portfolio-factor-allocation, portfolio-multi-strategy, portfolio-risk-parity,
  portfolio-tactical-overlay, rules-directional-continuous, rules-directional-event-settled, stat-arb-cross-sectional,
  stat-arb-pairs-fixed, vol-0dte-gamma-scalping, vol-0dte-pin-risk, vol-arb-rv-iv, vol-carry, vol-cross-asset-spread,
  vol-dispersion, vol-leaps-convexity, vol-market-making, vol-ml-lean, vol-overlay-covered-calls,
  vol-overlay-protective-put, vol-ratio-spread, vol-spread-structures, vol-straddle, vol-synthetic-delta,
  vol-term-structure-arb, vol-term-structure-slope, vol-trading-options, vol-variance-swap, yield-rotation-lending,
  yield-staking-simple
- `code-shipped` → enum (8): arbitrage-mev-backrun, arbitrage-mev-jit-liquidity, arbitrage-mev-liquidation-bundle,
  arbitrage-price-dispersion, carry-staked-basis, defi-lp-concentrated, defi-lp-pool, defi-lp-vault
- `stub` → enum (5): carry-recursive-staked-config-variants, archetype-strategy-params,
  backtest-persistence-and-ranking, backtest-run-manifest, strategy-config-drift-detection
- `active` → enum (3): archetype-param-schema-inventory, promote-workflow, prediction-markets-codification-gaps
- `theoretical-only` → enum (1): arbitrage-mev-sandwich
- `live` → enum (1): market-making-continuous
- `complete` → enum (1): archetype-paper-readiness

2. ✅ RESOLVED 2026-07-06 (pm@09cc91f48 — 22 epics re-mapped per the canonical slug registry in
   `scripts/plans/fix_epic_frontmatter_2026_05_21.py` (authoritative intent, not judgment): 5 domain epics → their
   domain, 14 → `[cross-cutting]`, infrastructure_master → `[infrastructure]`, orchestrator + agent-operating -framework
   → `[meta]`; only defi_master keeps `[defi]`; epics README normalized to list form) ~~**Epic `asset_group: [defi]`
   mis-seed.**~~ Most epics carry `[defi]` regardless of domain (cefi_master, execution_master, mtds_mdps_master,
   observability_master, dart_and_promote_master, …) — a migrate_epics default. Search-axis correctness bug; untouched
   (dispatch-load-bearing). Proposed per-epic mapping is mechanical from slug.
3. ✅ RESOLVED (verified 2026-07-06 — the zero-pass fixed all three: enum-valid `nature: record` + valid
   stage/parent_epic; residual placement nit only: `defi_expected_unattempted_backlog_1m` is still `doc_type: plan`
   living in `issues/` — gate-legal, fold into B6 if retyped) ~~**3 pre-existing HARD-rot docs**~~ (all authored
   ~2026-06-30/07-03 with issue-ish `nature` values the enum lacks): `defi_expected_unattempted_backlog_1m_2026_07_03`
   (a `doc_type: plan` living in `issues/` — move or retype), `deribit_options_chain_af_g4_blocker_2026_07_03`
   (`nature: data-correctness`, `stage: backfill`, bad parent_epic), `plan_issue_epic_consolidation_2026_06_30`
   (`nature: audit`, `asset_group: cross-asset`, no parent_epic). Recurring authoring instinct → consider adding an
   issue-ish `nature` value at gate-consolidation.
4. ✅ RESOLVED (verified 2026-07-06 — docspec now carries `locked_by` as `Req.O` scalar; NA accepted; corpus green with
   NAs present) ~~**`locked_by: NA` hook contradiction.**~~ Something (not `fix_frontmatter.py`, which writes
   `live-defi-rollout`) rewrites empty `locked_by:` → `NA` on commit; docspec flagged literal NA as SOFT (22 docs).
5. ✅ RESOLVED (verified 2026-07-06 — the blocking gate is green with valid-empty lists present; `_valid_empty` handles
   legal-empty) ~~**Validator↔schema empty-list tension**~~ (from P3.1): schema §6 says `repos: []`/`related: []` is
   legal-empty, the FieldSpec flagged it SOFT — stubs/superseded docs claiming nothing is CORRECT.
6. ✅ RESOLVED 2026-07-06 (pm@09cc91f48 — retype = MOVE, since `doc_type` is path-derived. **Moved → codex/15-runbooks/
   (10)**: both rotation runbooks (renamed `credential-rotation-runbook` + `per-source-credential-rotation-runbook`),
   sit-runbook, physical-pager-layer, custody-onboarding-checklist, lst-seasonal-rewards-smoke,
   expected-absence-backfill-runbook, recursive-leverage-receiver-deploy-runbook, pre-cutover-test-wallets-runbook,
   phase-2-6-bucket-name-cutover-runbook; `execution:` sub-map truth lifted to top-level keys. **Moved →
   plans/audit/results/ as `audit-result` (4)**: vm_security_audit_2026_05_15 (pass/P1),
   vm_deployment_events_audit_2026_05_15 (partial/P2), vm_event_emission_audit_2026_05_15 (pass/P1),
   run_lifecycle_events_audit_2026_05_05 (partial/P2). **Leave-in-place by content (5)**: reconciliation-resolution +
   reconciliation-age-tracking (genuine architecture SSOTs — contracts/DAG/dimensions, not procedures),
   credentials-matrix (reference matrix, self-titled workspace SSOT), role-registry (registry schema spec),
   presentations/target-experience-post-refactor (kept in place, `nature: ssot → notes` per its self-declared non-SSOT
   status). ~50 inbound refs re-relativized across 40 files; pre-existing dead links found during the sweep
   (archived-plan refs, `disaster_recovery.md` typo, bare epic mentions) → W7 dead-link inputs, NOT move breakage.)
   ~~**doc_type retype candidates (~15)**~~ — runbook-shaped `codex-ssot` docs (rotation-runbook, sit-runbook,
   phase-2-6-bucket-cutover, pre-cutover-test-wallets, physical-pager-layer, recursive-leverage-receiver-deploy,
   reconciliation-resolution, reconciliation-age-tracking, custody-onboarding-checklist, credentials-matrix,
   lst-seasonal-rewards-smoke, expected-absence-backfill-runbook) + audit-shaped (vm-security-audit,
   run-lifecycle-events-audit, vm-deployment-events-audit, vm-event-emission-audit) +
   `presentations/ target-experience-post-refactor` (self-declares non-SSOT) + `role-registry` (registry schema).
7. **SUPERSEDED banners missing on 19 `_archived_pre_v2` docs** (status set superseded; body banner absent) — list in
   lane 21/20/23 commits; mechanical banner-add.
8. **Codex-drift bodies flagged for the codex-audit process** (status set, bodies untouched): multi-VM fleet presented
   as live (agent-orchestrator-worker-topology, agent-orchestrator-dns-cutover — both marked stale — + drift in
   canonical-plan-flow, local-slot-host-symmetric-worker-model, orchestrator-safety-mechanisms, orchestrator_master
   audit-instructions); ARCHIVED user-management-ui still described active (firebase-production, ui-setup-checklist,
   triage-matrix + 3 more); `unified_api_contracts.canonical.*` deep-path citations (defi-risk-monitoring,
   global-ledger-architecture, greeks-service-overview, mvp-scope-canonical, uac-registry-gaps); dead body links (~20
   collected in lane reports, biggest: per-category-bucket-layouts rename ×7 in smoke-testing-playbook, empty `https://`
   placeholders in roadmap docs, orphaned second frontmatter block in sports_pipeline_to_100pct_golden_window_first).

## Success criteria

- All content-fillable SOFT fields populated across the live corpus — `summary` / `tags` / `authoritative_for` /
  `related` / `status` / `repos` (+ audit-result fields) via the LLM pass; `created` / NA-normalization /
  `referenced_by` via script (docspec SOFT → ~0 on targeted trees, operator-only items excepted).
- A single comprehensive **blocking** frontmatter gate (backed by `docspec.validate_frontmatter`);
  `check_docspec_coverage` retired; one validator engine, no duplication.
- agent-role docs enforced in the agent-orchestrator repo.

## Deferred work after 2026-07-06

Nothing from THIS plan is dropped — every residual is homed in the parent epic
[`agent_operating_framework_master`](../../epics/agent_operating_framework_master.md), never orphaned here:

- **W7 (aspirational)** — codex condense/de-drift + the L4 module-level `code_refs` rider + **B8** (the codex-drift
  document bodies surfaced during the content pass, P3.4 §B8). Home: epic W-table row W7 + its `[DOCS] P2. W7` todo.
- **Archive backfill — carries B7** (SUPERSEDED banners on the 19 `_archived_pre_v2` docs) plus summary/tags on the
  ~1,127 archive docs; operator-paused. Home: epic `[DOCS] P3. DEFERRED` todo (controlled tag vocabulary · archive
  backfill · …).
- **W8 retrieval-eval loop** — deferred by design. Home: epic W-table row W8.

## Progress Log

- 2026-07-06 — **Hook gap was WORKSPACE-WIDE, not PM-only: 384/400 clones fixed (operator: "what about other repos?").**
  Measured all 25 repos × 16 clones — every clone carries a `.pre-commit-config.yaml`, only the 16 PM ones (fixed
  earlier today) had the prek pre-commit hook. On 384 clones, gitleaks / slot·host commit-identity / branch-drift / ruff
  / prettier / conventional-commit never ran at commit time; 24 main-ws clones also lacked the pre-push
  strict-quickmerge guard; 9 MORE stale `core.hooksPath` entries found (10 total incl. PM main-ws — all dead absolute
  paths from the `/active` migration, each one disabling ALL hooks in that clone). Live remediation: 384 prek installs +
  24 guards + 9 hooksPath clears, 0 failures, verified 400/400 both-hooks-ok. Durable (pm@730565a1e, QG exit 0): cron
  self-heal widened from the PM-only loop to a generic ALL-repos × ALL-clones sweep per 5-min tick (heals either hook;
  clears a hooksPath ONLY when its target dir is provably gone — a live custom one is deliberate and untouched);
  clone-time install was already repo-generic from cb3f353fe. Other hosts (Ikenna's machine, VMs) self-heal
  automatically once their cron self-updates from origin — no manual sweep. SSOT section updated with fleet numbers.
- 2026-07-06 — **ROOT CAUSE of the bypassed prek hook found + fixed fleet-wide: prek pre-commit was NEVER installed on
  15/16 PM clones.** Operator asked whether the hook could simply be missing — audit confirmed: only slot-3 had
  `.git/hooks/pre-commit` (manual `prek install` at some point); the gate-red doc's author clone (slot-2) and every
  other clone had none, so ALL commit-time gates (staged-plans schema, commit-identity, gitleaks, prettier,
  conventional-commit) silently never ran fleet-wide — no `--no-verify` involved. `setup-tab-worktrees.sh` only ever
  installed the pre-push strict-quickmerge guard and ASSUMED the prek hook existed. Bonus finds: main-ws lacked pre-push
  too, and carried a stale absolute `core.hooksPath` (pre-migration `/home/hk/...`) disabling all hooks there. Fixed at
  three layers (pm@cb3f353fe, QG exit 0): (1) live remediation — `prek install` in all 16 clones + main-ws pre-push +
  hooksPath cleared (verified: 16/16 both-hooks-ok); (2) clone-time — `install_prek_precommit_hook` in
  setup-tab-worktrees.sh; (3) the 5-min `slot-cron-ff-pull.sh` PM loop self-heals either missing hook every tick. SSOT:
  per-tab-worktrees.md § "Git hooks are per-clone and MUST both be installed". Local hooks = floor; `quality-gates-v2`
  on the promote PR = the unbypassable wall.
- 2026-07-06 — **`nature: issue` legalized + doc_type↔path consistency HARD-enforced (operator directive; closes the B3
  "recurring authoring instinct" for good).** pm@1399d333e (quickmerge, QG exit 0; promote PR #793 v2-gated auto-merge).
  NATURE gains `issue` (8 values) — three independent authors had reached for it against the enum, so the enum moved to
  the authors. The enforcement half: `docspec.validate_frontmatter` now HARD-fails a declared `doc_type:` that
  contradicts the path-derived type ("fix the field or move the doc"), so the plan-living-in-issues/ pattern is blocked
  at every layer that calls docspec (prek staged-plans hook, PM QG corpus gate) — note the 3rd occurrence COMMITTED
  despite the prek hook running this exact check, i.e. it was bypassed (`--no-verify` or uninstalled hook in that
  clone); server-side QG remains the backstop that cannot be bypassed. Corpus sweep caught exactly 1 pre-existing
  mismatch (defi_expected_unattempted_backlog_1m → `doc_type: issue`, the B3 residual placement nit — now closed);
  prediction_universe doc restored to its author's original `nature: issue` as the exemplar. Schema SSOT §2/§4/§5
  updated in lockstep; docspec tests 21 green; gate 1,299/0.
- 2026-07-06 — **P3.4 COMPLETE — B1/B2/B6 executed (operator: "do all B1, B2 and B6"); plan is fully done.** Shipped
  pm@09cc91f48 (quickmerge, full QG exit 0 pre-commit; one index.lock race with the 5-min cron on first attempt, clean
  retry). B1: docspec gains the ELECTIVE requirement tier (`Req.E` — absent-is-fine, enum-validated when present;
  deliberately NOT present-but-empty so 700 non-archetype docs don't carry a noise key) + `IMPLEMENTATION_STATUS` enum;
  66 archetype docs restored from the preserved mapping (47 design · 8 code-shipped · 5 stub · 3 active · 1 each
  theoretical-only/live/complete); schema SSOT §3/§6 updated; 3 new tests (18 green). B2: 22 epics re-mapped per the
  canonical registry in `fix_epic_frontmatter_2026_05_21.py` — grep-found authoritative intent that overrode 3 of my
  slug judgments (manifest/deployment/observability → cross-cutting, not infrastructure). B6: 14 moves (10 runbooks, 4
  audits with pass/partial verdicts read from bodies), 3-pass inbound-link fixer (~50 refs / 40 files; passes: plain
  tokens → moved↔moved cross-links → ../-prefixed + renamed-basename), execution sub-map truth lifted over defaults on
  the 8 moved docs that had it, 5 recorded leave-in-place calls. Also fixed en-route: gate-red frontmatter on the fresh
  `prediction_universe_capture_dead` issue doc (B3-class authoring instinct recurring — 3rd occurrence, consider the
  issue-ish `nature` enum value). Verification: frontmatter gate 1,299/0; index regen 1,120 docs; graph 3,114 edges / 67
  unlinked (edge count held through the moves — nothing orphaned). Remaining in this plan: NOTHING — B7 rides the paused
  archive bonus, B8 rides W7 (both tracked in the epic, not here). Plan is archival-ready pending the 5-step ritual.
- 2026-07-06 — **P3.4 section A CLOSED by operator policy; B-items re-measured.** Operator decision: zero-pass defaults
  on runbook `owner`/`cadence`/`verifier` + authorship-derived `auditor` are acceptable and NOT operator work — values
  self-correct at first use ("update on use"); blanks get defaults going forward. Live re-measure (slot-3): gate green
  1,298/0; 18 runbooks on the default triple; 13 runbooks carry sub-map-lifted true values; `auditor` junk identities
  (`Ubuntu`/`ComsicTrader`, both = harsh per git log) stand per the same policy; `last_executed: never` ×25 = rehearsal
  backlog (not a fill); 1 straggler noted (`honest_coverage_uac_writer_ matrix_reconciliation_2026_06_29` is
  `status: resolved` with empty `resolved_by` — gate-legal, update-on-use). B3 HARD-rot docs verified FIXED by the
  zero-pass; B4 locked_by-NA + B5 valid-empty verified reconciled in docspec. P3.4 now = decision items B1 (archetype
  maturity key), B2 (epic `asset_group: [defi]` mis-seed — re-measured 23/28 epics), B6 (retype ~15); B7 parked with
  archive bonus; B8 feeds W7.
- 2026-07-04 — **Index scope decisions (operator) + an AO timing collision.** (1) The L0 index
  (`DOC_INDEX.generated.md`) is **PM-repo live-trees ONLY**: the `agent-orchestrator/agents` root removed from
  `gen_doc_index.py` (1,119 entries, zero cross-repo paths). Other repos join later as a deliberate separate task. (2)
  **`plans/archive` is NEVER indexed** — not now and not after the archive backfill (closed records; unbounded index
  growth, no routing value; rare history reads take the costlier archive-grep path). `_EXCLUDED_PREFIX` safety net
  added. (3) **COLLISION for operator decision**: the operator deferred agent-orchestrator gate wiring ("not even AO
  right now"), but a concurrent orchestrator session had ALREADY shipped it (agent-orchestrator@202c9b6) before the
  deferral was voiced. Not reverted here (pushed work, other session's). Operator: keep the in-repo AO gate (it gates
  only agents/\*.md inside AO, invisible to PM) or revert it.
- 2026-07-04 — **ALL agent-workable todos DONE.** P3.3 referenced_by (pm@a89ab2c36, 648 codex docs) + agent-role
  enforcement (agent-orchestrator@202c9b6) shipped by orchestrator session; P3.2/gate-consolidation/
  archive-bonus/zero-violations shipped by the operator-side concurrent session. Corpus: docspec HARD=0 SOFT=0 (1,298
  live docs, independently verified twice) + consolidated blocking gate GREEN. Sole remaining open item = P3.4 operator
  worklist (human-only by design). Plan is COMPLETE pending P3.4 tick-off + archival ritual.
- 2026-07-04 — **GATE CONSOLIDATION SHIPPED (operator-directed): frontmatter can no longer rot.**
  `check_frontmatter_schema.py` = the single comprehensive BLOCKING gate (docspec-backed, HARD+SOFT, live trees only —
  plans/archive excluded per operator); warn-only `check_docspec_coverage.py` retired; schema banner updated. Archive
  bonus PAUSED by operator (1,129 docs still need summary+tags + 49 YAML repairs; mechanical seed of 1,127 docs is in
  local commits) — resumes on another account or later; archives are explicitly outside the gate so they don't block.
- 2026-07-04 — **ZERO-VIOLATIONS ACHIEVED (operator directive): docspec HARD=0 SOFT=0 across all 1,298 docs; full
  `quality-gates.sh` GREEN (exit 0).** Beyond P3.2: fixed the 3 pre-existing HARD-rot docs; validator↔schema lockstep
  (empty-list `repos`/`related` valid per §2; `authoritative_for: []` valid on non-current docs; superseded-epic
  identity fields exempt; `task_template.md` format-spec-exempt); **reconciled the `locked_by` contradiction** —
  `check_frontmatter_schema` required it non-empty (breeding the literal-`NA` sentinels docspec flags) → now optional
  per the canonical schema; lifted runbook owner/cadence/verifier from legacy `execution:` sub-maps; `auditor` derived
  from git first-commit author (26); source/resolved_by derived from doc bodies; narrow claims on pointer stubs; 4 YAML
  foot-gun breaks found+fixed (colon-space / ` #` / leading `{` / leading backtick in plain scalars — candidates for a
  docspec parse-lint). **Defaulted values needing operator review** (grep the zero-pass commit): `owner: ikenna` /
  `cadence: on-demand` / `verifier: operator` on runbooks where no value was derivable.
- 2026-07-04 — **P3.2 COMPLETE — all 55 lanes committed locally.** ~990 docs filled by 55 Opus lane agents (2026-07-03
  18:00Z → 2026-07-04); usage-managed per operator instruction (throttled 17:54–18:07Z at five_hour 89%, resumed
  post-reset; seven_day never exceeded ~51%, Sonnet switch never triggered). Final sweep: content-SOFT 5,887 → 306; HARD
  introduced 0; collision sweep clean; 2 YAML foot-gun breaks fixed. P3.4 worklist section added. Ship: final
  `quality-gates.sh` on the batch → rebase-autostash → SINGLE push (operator override of per-unit push).
- 2026-07-03 — **Two mid-fanout corrections.** (1) `locked_by: NA` RESTORED on 21 pre-pass files + the new issue doc:
  the BLOCKING `check_frontmatter_schema.py` requires non-empty `locked_by` on plan/issue docs (slot-1 backfilled the
  same on origin @f33ad39c3 to green v2), while docspec SOFT-flags literal `NA` — a live two-validator CONTRADICTION;
  the gate-consolidation todo MUST reconcile it (decide: widen docspec's NA allowance for locked_by, or change the
  blocking gate + fleet to null-means-unlocked). (2) A CONCURRENT EDITOR (operator-side session, same slot) is running
  the same lane playbook — filling remaining lanes + committing with the same per-lane template. Its output verified
  docspec-clean by three lane agents. Orchestrator response: HOLD further lane launches, verify its commits as they
  land, resume only if it stalls (never two agents on the same file).
- 2026-07-03 — **P3.2 checkpoint: 29/55 lanes committed locally** (lanes 00-28 = codex 00/01/02-data, 02-venues, 03-\*,
  04-architecture, 05-infrastructure, 06-coding-standards, 07-security, 08-workflows, 09-strategy pre-v2 archive +
  archetypes/axes/cross-cutting chunks). All local commits, unpushed per operator override. Per-lane evidence in commit
  messages `docs(frontmatter): P3.2 lane NN`. Anomaly log at scratchpad `anomalies.md` (session) — headline items for
  final report: (1) SSOT contradiction 3-vs-4-category empty-output decision (shard-level-failure-isolation vs
  validation-and-errors); (2) archetype maturity axis (design/ code-shipped/live) flattened by enum normalization — old
  values recoverable from lane diffs, operator to decide on a dedicated key; (3) two agent-orchestrator docs presented
  the retired multi-VM fleet as live (marked stale); (4) ~15 runbook/audit-shaped docs typed codex-ssot (retype list);
  (5) recurring dead body-citations captured per lane. Usage at checkpoint: seven_day 48%, five_hour 76% (Opus
  continues; Sonnet switch only >90% seven_day).

- 2026-06-30 — Plan created (operator decision) by splitting the deferred consolidation items out of the completed
  full-corpus coverage plan (now archived). P3 / nice-to-have, human-driven (`local-only`, `assigned_vm: NA`).
- 2026-07-03 — **Measured the corpus + recalibrated the todos (operator-approved).** docspec sweep: 1,298 docs checked,
  5,887 SOFT violations across 1,072 docs; 1,017 docs (17 MB ≈ 4.2M tok) still need content fields. Per-field: tags
  1,013 · summary 955 · related 931 · created 804 · authoritative_for 735 · status 913 (662 empty + 251 non-enum) ·
  repos 141 · audit fields (severity 84 / audited_scope 76 / auditor 33 / date 33) · runbook owner/cadence/verifier
  30/50/30 · literal-NA 29. Decisions (operator, 2026-07-03): Sonnet-only (no Haiku length-split — p50 doc 10 KB, only
  36 docs < 2 KB; savings marginal vs misroute risk); ONE read fills ALL fields (the original 3 per-field passes would
  read the corpus 3×); expanded field set beyond the 3 planned (add related/status/repos + audit fields; code_refs
  opportunistic-verified-only); `created`+NA-normalization+`referenced_by` are SCRIPT work, not LLM;
  owner/verifier/supersedes/provenance stay operator-only. Todos restructured P3.0–P3.4 accordingly.
- 2026-07-03 — Corpus is no longer HARD-green (3 issue docs with HARD rot, invalid `nature` enums — all three authors
  reached for issue-ish values `issue`/`audit`/`data-correctness` the closed vocab lacks; recurring instinct → consider
  an enum addition at gate-consolidation time). Non-blocking (warn-only gate working as designed); not this plan's scope
  to fix the 3 docs.
- 2026-07-03 — **P3.2 fan-out RUNNING (operator-dispatched /autonomous).** Operator decisions: Opus sub-agents (usage
  window resets 18:59Z, 40% used — switch to Sonnet only if seven_day utilization >90%, checked per wave via the OAuth
  usage endpoint); **local commits only, NO push until the final full `quality-gates.sh`** then ONE push (explicit
  operator override of per-unit push); all trees incl. plans, not just codex; bonus if usage/time remain:
  plans/archive + other archived docs (currently outside DOC_TREES). Mechanics: 1,006 remaining docs split into 55 lanes
  (~20 docs each, folder-coherent, priority codex → plans/audit → plans/epics → plans/active), lane manifests at
  `/tmp/claude-1000/-active-unified-trading-system-repos/b234abe8-7a31-44b9-82b0-84cb4f324543/scratchpad/lane_NN.txt` (+
  `lanes.json`); waves of 6 parallel agents; per wave: docspec-verify lane files → `git add` by lane list → local commit
  → usage check → next wave. Wave 1 = lanes 00–05 (113 docs) LAUNCHED. Progress metric: lanes committed /55. Final
  phase: authoritative_for collision sweep + full docspec sweep + `quality-gates.sh` + single push + flip P3.2.
- 2026-07-03 — **P3.1 pilot shipped** (pm@091318d21): 14 docs in `codex/11-project-management`, all six content fields;
  docspec HARD=0, content-SOFT → 0 (bar valid-empty `[]`). **Discoveries:** (1) validator↔schema tension — schema §6
  says empty `repos: []`/`related: []` is legal, but the FieldSpec flags it SOFT "required but empty"; MUST be resolved
  (validator accepts empty-list, or the blocking gate enforces a subset) BEFORE the gate-consolidation todo flips
  blocking, else valid docs red the gate. (2) Pilot surfaced codex-content rot for the codex-audit process (NOT fixed —
  body edits out of scope): `architecture-constraints.md` filename↔title mismatch; `codex-delta-canonical-brief.md`
  internally inconsistent dates + orphaned targets (marked `stale`); `plan-hygiene.md` says hygiene-sweep Terraform "not
  yet shipped" but `deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf` exists on disk (CODEX-STALE);
  `secrets-migration-tracking.md` cites non-existent `unified-config-interface/` (renamed → unified-cloud-interface) + a
  pre-refactor UTL path; ADR-2026-04-25 cites a pre-refactor deployment-api symbol path. (3) Legacy
  `cadence`/`verifier`/`last_executed`/`type` blocks on 2 docs (plan-hygiene, active-plan-inventory-tracker) — operator
  to decide codex-runbook re-typing vs dropping legacy fields. (4) `owner` empty on 12/14 docs +
  `secrets-migration-tracking.md` has a legacy PROSE `authoritative_for` (pre-existing) — both → P3.4 operator worklist.
