---
title: "AUDIT-03 — Phase 1 READ results: §2.8 PIPE + §2.9 DATA"
audit_id: AUDIT-03
run_phase: "Phase 1 — static drift, READ checkpoints (code-presence only; GCS coverage = Phase 2)"
section: "§2.8 pipeline invariants (PIPE-*) + §2.9 data coverage (DATA-*)"
date: 2026-05-22
method: "sonnet sub-agent first-pass (evidence-required) → Opus reviewer consolidation"
auditor: Harsh + Claude Opus 4.7 (reviewer)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - market-tick-data-service handlers {lst_rates, perp_funding, dex_pools, lending_indices}
  - .extra/features-onchain-service (staking_apy_total, dependency_checker, batch_handler)
  - .extra/features-delta-one-service (funding_oi, cli/parser)
  - strategy-service@b303a358 engines (live-only branching check)
oracle: codex/02-data/{availability-manifest-and-data-status.md, honest-absence-downstream-handling.md} + writegate batch=live
---

# AUDIT-03 — Phase 1 READ — §2.8 PIPE + §2.9 DATA

Sub-agent first pass, Opus-reviewed. **3 findings (F-20…F-22)**, incl. one incidental P0 runtime bug. GCS coverage
(DATA-01/05/06/09/10, PIPE-02/06/07) is Phase 2 — here only code-presence + honest-coverage wiring.

## Per-checkpoint verdicts

| ID | Verdict | Evidence |
| -- | ------- | -------- |
| PIPE-01 | PASS | only `mode==live` hits are PnL-stream env labels (staked_basis.py:547, price_dispersion.py:164) — not signal gating. No live-only branching in handlers ✓ |
| PIPE-04 | PASS (handlers) / VERIFY (features) | 4 MTDS handlers use `record_empty(reason=<typed>)` (SOURCE_RETURNED_ZERO / EXPECTED_*) + `record_failed`. features-onchain `batch_handler.py:86` fail-fast on missing deps. staking_apy_total = pure compute (no manifest emit) |
| PIPE-05 | **CODE-DRIFT** | features-onchain `dependency_checker.py:366-379` checks GCS **blob presence only**, NOT manifest `capture_status` — an upstream `attempted_failed` shard (empty parquet) reads as "present" → features-onchain silently computes on bad data instead of `record_failed(UPSTREAM_*)`. Same in features-delta-one → F-20 |
| PIPE-09 | **CODE-DRIFT** | hardcoded venue API URLs in `perp_funding_handler.py:84-107` (HYPERLIQUID/ASTER/PACIFICA) — IS→MTDS SSOT violation. (The-Graph gateway + Tardis-datasets URLs are data-provider *infra*, not venue URLs — arguably exempt; HL/Aster/Pacifica are the genuine violations.) `lst_rates_handler` PASS (Alchemy URL via IS-first `get_rpc_url()`) → F-21 |
| DATA-04 | PASS (KD-02) | `staked_basis.py:250` `features.get("usdc_idle_yield_apy_bps", 0.0)`; no producer emits it (workspace grep) — confirmed unwired ✓ |
| DATA-01/02/03/07/08 | PASS (producer present) | lst_rates_handler, staking_apy_total aggregator, funding_oi calculator, dex_pools_handler, lending_indices_handler all exist + wire `record_captured/empty/failed`. **Coverage itself = Phase 2** |
| PIPE-02/06/07, DATA-05/06/09/10 | PHASE2 | require GCS/manifest inspection |

## Findings

| ID | Checkpoint | Class | Finding | Sev | Status |
| -- | --------- | ----- | ------- | --- | ------ |
| F-20 | PIPE-05 | CODE-DRIFT | features-onchain (+ features-delta-one) dependency checker uses GCS blob-presence only, not manifest `capture_status` — upstream `attempted_failed`/empty shards are indistinguishable from captured → silent compute on bad input. `dependency_checker.py:366-379` | P1 | AGENT-FOUND |
| F-21 | PIPE-09 | CODE-DRIFT | hardcoded venue API URLs (Hyperliquid/Aster/Pacifica) in `perp_funding_handler.py:84-107` business logic — violates IS-SSOT (QG STEP 5.70 `no_hardcoded_venue_urls.sh` should flag). Confirm Graph/Tardis infra-URL exemption. | P2 | AGENT-FOUND |
| F-22 | (incidental) | CODE-BUG | `perp_funding_handler._make_session()` (def L76) has no `headers` param but is called `_make_session(headers={"Authorization":...})` at L1124 (Lighter path) → `TypeError` at runtime. Out of strict §2.x scope but a real P0 crash on a funding-data path. | P0 | **NEEDS-CONFIRM** (Opus re-verify signature/call) |

## Open VERIFY

- features-delta-one `funding_oi` `mode` param + `cli/parser.py:181` `if mode != "live"` branch — confirm it does NOT gate feature-compute logic (would be a PIPE-01 batch=live breach). VERIFY next pass.
