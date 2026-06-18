---
title: "AUDIT-03 — findings routed to Ikenna for decision / codex-intent"
created: 2026-05-22
priority: P1
status: active
locked_by: live-defi-rollout
source:
  - audits/audit-files/audit_03_defi_archetypes_e2e.md (§6 + §6.1 re-verification ledger)
---

# AUDIT-03 — findings routed to Ikenna

> **ARCHIVED 2026-06-01 (slot 7).** All 9 routed findings are decided + dispatched (issue-doc-lifecycle: acked →
> archive, no dual-track): F-22 ✅ shipped (mtds@`0716a544`); F-14 (1h price-move abort = P1 safety gap) + F-13/F-15 →
> `strategy_master`; F-34 (SUPPORTED_ARCHETYPES) → `strategy_master`; F-32 (MEV size-escalation post-cutover) →
> `execution_master`; F-45 + F-06 (Elysium scrub) → `codex_vs_repo_docs_ssot_audit`; F-25 (full ClientConfig) →
> `client_isolation_and_governance_master`. Operator decision ledger preserved below for provenance.

These AUDIT-03 findings are **Opus-confirmed real** but are NOT pure code fixes — each needs a judgment call,
cross-cutting architecture decision, or a codex-intent ruling that Ikenna owns (trading-judgment / governance /
cross-repo spec authority). They are deliberately kept OUT of the remediation plans (carry-safety, cron-provisioning,
drift-backlog) until the decision lands, so we don't ship a fix that contradicts the intended design.

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** Rulings below are FINAL. Execution assigned to
> **slot 7** (`tab/ikennaigboaka/7`) as issue-janitor + quick-fix; PM active plans/epics are SSOT. Slot 7 must NOT
> duplicate manifest-canonicalisation (slots 2/3), CI/CD-hardening (`cicd_contract_hardening` /
> `ci_canonical_v2_migration`), or codex-docs consolidation (`codex_vs_repo_docs_ssot_audit`). Codex-doc edits implied
> below are routed to that owner — slot 7 records the todo, does not edit codex.
>
> - **F-22** — ✅ SHIPPED 2026-06-01 (slot 7): `_make_session(headers=...)` optional param added,
>   market-tick-data-service@`0716a544` on LDR (fixes the Tardis-funding-path TypeError). [slot 7 code]
>   - **NOTE**: MTDS QG is **pre-existing-red** independent of F-22 — `migrate_prediction_to_pred_prd_v9.py`
>     deep-imports `gcs_copy_object`/`gcs_describe_object` (UTL does NOT re-export these top-level, only
>     `gcs_delete_object`) + ruff-format drift in `backfill_drift_v2_historical.py` / `backfill_solana_dex_state.py` /
>     `migrate_defi_full_v9_canonical.py`. Dispatch todo filed in `mtds_mdps_master`. Foreign (slots-2/3) → not swept by
>     slot 7.
> - **F-34** — 28 implemented archetypes = intended May-23 rollout subset. Add `SUPPORTED_ARCHETYPES` allowlist +
>   typed-error guard + fix docstring (strategy-service). [slot 7 code — small]
> - **F-13 / F-15** — reconcile codex strategy-spec → implemented mechanism (code is truth). Record codex-update todo in
>   `strategy_master` + route doc edit to `codex_vs_repo_docs`.
> - **F-14** — VERIFY whether `vol_cap_clamp` provides an equivalent 1h price-move abort. If yes → reconcile codex. If
>   NO → it is a **P1 safety gap** → file todo in `strategy_master` / `execution_master`. [slot 7 investigates + > > > >
>   reports]
> - **F-32** — MEV mode is **directive-driven** for May-23 → close F-32. Size-based auto-escalation = post-cutover P2
>   todo in `execution_master`.
> - **F-45** — **code wins**: keep `instance_id` in the events path; `correlation_id` is a column, not a path key. Route
>   codex-update todo to `codex_vs_repo_docs`.
> - **F-06** — declare `codex/04-architecture/custody-providers.md` the entity-governance SSOT; entities = **Odum
>   Research UK + Odum Group Cayman**; scrub stale **Elysium** refs (removed provider) — file as FIX-STALE todo in
>   `codex_vs_repo_docs`.
> - **F-25** — build the **FULL unified `ClientConfig`** type in `unified_api_contracts.internal` (not a minimal stub).
>   Record as todo in `client_isolation_and_governance_master`; slot 7 implements only if cleanly QG-green, else leaves
>   the todo for the epic VM.

> Cross-side ping: on next push, add a one-line entry to `plans/active/_agent_pings.md` pointing here. (Held back per
> "local commit only" instruction 2026-05-22.)

## 1. F-34 (XAS-01) — rollout-subset vs missing-engines decision **[DECISION]**

**What I found**: `ARCHETYPE_ENGINE_REGISTRY` has 28 entries; `StrategyArchetype` enum has 55 members (docstring stale
at "53"). 27 archetypes (18 `VOL_*`, 5 granular market-making, 2 `ARBITRAGE_*`, 4 `PORTFOLIO_*`) have no engine.
Dispatch (`factory.py:87-95`) raises a descriptive `KeyError` whose docstring says "every enum value must have an
engine" — i.e. the code treats the 27-gap as a BUG, and there is no `SUPPORTED_ARCHETYPES` allowlist marking the 28 as
an intended May-23 subset.

**Why it matters**: If these 27 are an intended phased rollout, the code is fine but needs an explicit allowlist +
docstring/count fix so the gap isn't read as a regression by the next auditor. If they are genuinely-missing engines,
they are 27 latent `KeyError`s waiting for a config that names them.

**Recommended decision (Ikenna)**: confirm "28 = intended May-23 rollout subset". If yes → add `SUPPORTED_ARCHETYPES`
allowlist + fix the "53"→55 docstring + a guard that returns a typed "archetype not in rollout" error. If no → file the
missing engines as their own epic.

**Existing partial coverage (dedup 2026-05-22)**: `plans/active/config_grid_archetype_extend_2026_05_20.md:59-70`
already flags ONE of the 27 (`ARBITRAGE_CROSS_DOMAIN_EVENT`) as having no factory engine ("Grid sweep would crash at
registration lookup") and asks for the same kind of decision (implement-engine-first vs defer). The systemic allowlist
decision here SUPERSEDES that per-archetype note — when ruled, update both. Not a duplicate; this is the umbrella
decision for all 27.

## 2. F-06 (ONB-07) — operating-entity governance **[DECISION]**

**What I found**: CLAUDE.md names Odum / Cayman as the operating legal entities; codex references "Elysium" only as a
DELETED-provider archived ref, "POD" as a custody-delivery party (not a legal entity), and no "BVI". So it is NOT a
clean active-entity conflict (§6.1 reframe) — the real issue is a stale archived Elysium reference + no single
entity-model SSOT.

**Why it matters**: onboarding + custody + audit trails key off the operating entity; ambiguity here touches client
funds isolation + reporting.

**Recommended decision (Ikenna)**: declare the canonical entity-model SSOT (which doc owns Odum/Cayman) + scrub the
stale Elysium reference. Governance call, not a code fix.

## 3. F-13 / F-14 / F-15 (APD) — codex strategy-spec phantom fields **[CODEX-INTENT]**

**What I found** (all confirmed): codex `arbitrage-price-dispersion.md` references config fields/values the engine does
NOT implement, and the engine uses different mechanisms:

- F-13: codex calls `dynamic-best-long-short` a `PairSelectionMode`; it is actually a `venue_selection_mode` value. The
  enum has only `single-best` / `top-k` / `all-above-threshold`.
- F-14: codex `max_underlying_move_pct: 3.0` is phantom; the engine guards via `vol_cap_clamp_*` instead.
- F-15: codex `react_to_equity_change` + `max_capital_per_opp_pct` are phantom; the engine auto-scales via
  `stake_fraction · target_equity` (functionally equivalent).

**Why it matters**: codex is the strategy SSOT; if it specifies fields that don't exist, either the engine is missing a
guard (F-14 is the only one with a possible safety implication — a raw price-move abort) or the codex is describing a
superseded design.

**Recommended decision (Ikenna)**: per field — reconcile codex to the implemented mechanism, OR rule that the engine
must implement it. F-14 (`max_underlying_move_pct`) is the one to look at first: is `vol_cap_clamp` an acceptable
substitute for a raw 1h price-move abort, or do we need both?

## 4. F-32 (EXE-02) — is MEV mode meant to be size-selected? **[CODEX-INTENT]**

**What I found**: there is NO code that selects an MEV-protection mode by trade notional (e.g. `>$10k → FLASHBOTS`).
`MevRouter.route(mode, chain)` (`mev_router.py:97`) takes the mode as a parameter; it is purely directive/config-driven.
BLOXROUTE is correctly excluded.

**Why it matters**: if codex intends auto-selection-by-size, this is a real GAP (a large swap could go to the public
mempool). If codex says the directive carries the mode, there is no defect and the finding closes.

**Recommended decision (Ikenna)**: rule on the EXE-02 oracle — directive-driven (close F-32) or size-driven (it becomes
a P1 fix in the carry-safety / execution plan).

## 5. F-45 (RPT-07) — events path: instance_id vs correlation_id **[CODEX-INTENT]**

**What I found**: `GcsEventSink` writes `events/{service}/{date}/{instance_id}/hour=.../` (`event_sink.py:128-131`);
codex `live-deployment-monitoring.md:38` specifies `correlation_id` as that 3rd segment. The code uses VM-scoped
`instance_id` (VM_NAME / host-pid); codex wants run-scoped `correlation_id`.

**Why it matters**: determines whether you can prefix-filter the events stream by correlation_id (per-run trace) vs
per-VM. Likely the codex doc is the stale side (post-2026-05-01 sink rev), but that's a canonical-side ruling.

**Recommended decision (Ikenna)**: declare which is canonical. If code wins → update the codex doc. If codex wins → add
`correlation_id` to the sink path (a code fix that then moves to the drift-backlog plan).

## 6. F-22 (incidental) — perp_funding_handler `_make_session()` missing headers param **[CODE-BUG, MTDS]**

**What I found** (AUDIT-03 incidental, confirmed P1): `perp_funding_handler._make_session()` accepts no `headers`
parameter but is called with `headers=...` at L1124 (Tardis auth path, not Lighter). This is a `TypeError` at runtime on
the Tardis funding-rate fetch path.

**Why it matters**: the Tardis path is the historical funding-rate data source; a TypeError here silently breaks funding
data ingestion for the affected instruments.

**Recommended action**: trivial one-liner fix — add `headers: dict | None = None` param to `_make_session()` and pass it
to the underlying `aiohttp.ClientSession`. Lives in MTDS (`market-tick-data-service`), not strategy-service. Route to
whoever next touches MTDS perp funding handler, or fix as a quick standalone commit.

## 7. F-25 (ONB-01) — UAC `ClientConfig` type missing: code vs codex reconciliation **[ARCHITECTURAL DECISION]**

**What I found** (confirmed P1): the codex references a unified `internal.client_config.ClientConfig` type with fields
`client_id / org_id / share_class / categories_enabled / max_total_notional_usd / max_drawdown_pct` plus per-asset-group
sub-configs. This type does NOT exist in UAC. What exists:

- `internal/reporting/client_config.py` — billing/fee `TypedDict` (no risk dims)
- `internal/domain/strategy_service/client_config.py` — `ClientStrategyOverride` (per-strategy overrides, not a unified
  onboarding record)
- `internal/risk.py` — risk dimensions scattered across multiple types

Additionally, codex's `categories_enabled` field uses the old vocabulary (should be `asset_group`).

**Why it matters**: the codex describes a type that doesn't exist; any new service expecting to instantiate
`ClientConfig` from UAC will fail. Also affects the client onboarding pipeline.

**Recommended decision (Ikenna)**: choose one:

1. Create the unified `ClientConfig` in `unified_api_contracts/internal/domain/client_config.py` with the correct
   `asset_group`-vocabulary fields — becomes a UAC PR.
2. Reconcile the codex to describe the actual fragmented reality + document the "intended unified type" as a future epic
   item.
3. Hybrid: create the minimal type with `client_id + asset_groups_enabled + max_notional_usd + max_drawdown_pct` now;
   leave full sub-configs for the onboarding epic.

---

## Routing summary

| Finding    | Type         | One-line decision needed                                        |
| ---------- | ------------ | --------------------------------------------------------------- |
| F-34       | DECISION     | Is the 28-engine set an intended May-23 rollout subset?         |
| F-06       | DECISION     | Canonical operating-entity SSOT + scrub stale Elysium ref       |
| F-13/14/15 | CODEX-INTENT | Reconcile APD codex phantom fields to code (F-14 first)         |
| F-32       | CODEX-INTENT | Is MEV mode directive-driven (close) or size-driven (fix)?      |
| F-45       | CODEX-INTENT | events path: instance_id (code) vs correlation_id (codex)?      |
| F-22       | CODE-BUG     | Quick fix in MTDS: add `headers` param to `_make_session()`     |
| F-25       | ARCHITECTURE | Create UAC `ClientConfig` unified type OR reconcile codex only? |
