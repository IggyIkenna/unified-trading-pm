---
doc_type: issue
title: MTDS image bundles a STALE unified-api-contracts — ImportError kills EVERY market-tick-data-service Cloud Run job
summary:
  Every `market-tick-data-service` Cloud Run job (cefi-t1-recon, fast-t1-recon, and the new tradfi-databento-t1-recon)
  dies at interpreter start with an ImportError — cannot import name `is_recognized_tradfi_underlying` from
  `unified_api_contracts`. The image bundles MTDS code from `mtds@f645ea02` (2026-07-20 02:48:29), which imports that
  symbol, alongside a `.deps/unified-api-contracts` that PREDATES `uac@7e179ae8` (2026-07-20 02:47:03), which added it.
  The two commits landed 86 seconds apart; UAC is correctly pushed to LDR, but the image's bundled copy is stale. The
  failure is at module import in `__main__.py`, BEFORE any CLI arg parsing, so no job on this image can run regardless
  of its args. All MTDS T+1 batch collection is DOWN — cefi-t1-recon has been failing since at least 2026-07-19.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [mtds, uac, dep-skew, cloud-run, image-build, data-correctness, t1-batch, p0]
related: [./tradfi_t1_no_working_mtds_job_2026_07_17.md, ../tradfi_consolidated_closeout_2026_07_18.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
resolved_by:
source: A3-3 tradfi T+1 job verification (slot-1)
---

# MTDS image ships a stale UAC — every MTDS Cloud Run job fails at import

## Measured (2026-07-20, `[slot-1·laptop]`)

Found while verifying the new TradFi T+1 job (A3-3). The new job was created + scheduled correctly, but its first real
execution failed — and the root cause turned out to be fleet-wide, not job-specific.

```
ImportError: cannot import name 'is_recognized_tradfi_underlying' from 'unified_api_contracts'
  (/app/.deps/unified-api-contracts/unified_api_contracts/__init__.py)
Container called exit(1).
```

Traceback path (identical in all three jobs): `__main__.py` → `cli/main.py` → `cli/handlers/__init__.py` →
`dex_swaps_handler.py` → `market_interface/__init__.py` → `adapters/cefi/__init__.py` → `upbit_adapter.py` →
`adapters/tradfi/__init__.py` → `databento_adapter.py` → `databento_enrichment.py:20`.

It fires at **module import inside `__main__.py`**, before argparse — so **no** MTDS job on this image can run, whatever
its `--operation/--asset-group/--source`.

## Blast radius — ALL MTDS Cloud Run jobs (verified)

| Job                                                                 | Recent executions                    | Result              |
| ------------------------------------------------------------------- | ------------------------------------ | ------------------- |
| `uts-prod-market-tick-data-service-cefi-t1-recon`                   | 07-19 06:00/09:00, 07-20 06:00/09:00 | ALL `failedCount=1` |
| `uts-prod-market-tick-data-service-fast-t1-recon`                   | 4× on 07-20 11:40                    | ALL `failedCount=1` |
| `uts-prod-market-tick-data-service-tradfi-databento-t1-recon` (new) | 07-20 11:33, 12:4x                   | ALL `failedCount=1` |

Confirmed same `ImportError` in the logs of `cefi-t1-recon-p5gnb` and `fast-t1-recon-274jp`. **CeFi T+1 tick collection
has been silently failing since at least 2026-07-19.**

## Root cause — coupled cross-repo change, stale bundled dep

- `uac@7e179ae8` (2026-07-20 **02:47:03**) ADDED `is_recognized_tradfi_underlying` (defined
  `registry/tradfi_symbology.py`, re-exported top-level in `unified_api_contracts/__init__.py`).
- `mtds@f645ea02` (2026-07-20 **02:48:29**, 86s later) began IMPORTING it in `databento_enrichment.py:20`.
- UAC is **correctly pushed**: `7e179ae8` is an ancestor of `origin/live-defi-rollout`; local UAC HEAD ==
  `origin/live-defi-rollout` == `34580d92`. So the SOURCE is fine — the **image** is not.
- The Cloud Run jobs reference the mutable tag `:latest` (not a pinned digest). `latest` currently resolves to
  `sha256:724d8170…` (tags `0.92.0, e639c71`), pushed **12:32:23** today. `mtds@f645ea02` IS an ancestor of `e639c71`,
  so the image's MTDS code has the import — but its bundled `.deps/unified-api-contracts` still lacks the symbol.
- MTDS declares UAC as a **path** source (`pyproject.toml`
  `[tool.uv.sources.unified-api-contracts] path = "../unified-api-contracts"`) while the version pin is
  `>=0.33.0,<1.0.0`. The Dockerfile is a plain `COPY . .` of the build context, so `.deps/` is pre-populated by the
  build's dep-staging step. **That staged copy is what is stale** — every image built today (pushes at 11:40, 12:07,
  12:08, 12:32) carries the skew.

⇒ The image build is staging a `unified-api-contracts` older than the LDR tip it should track.

## Why it was not caught

The in-image `quality-gates` cloudbuild step is a REQUIRED gate ("test the artifact you deploy"), yet four skewed images
were built and pushed today. Either that step does not exercise an import of `market_tick_data_service.__main__` / the
CLI entrypoint, or it runs against a different dep set than the shipped layer. A one-line
`python -m market_tick_data_service --help` smoke inside the image would have failed the build. **That gap is the reason
a 2-day fleet outage went unnoticed.**

## Fix (NOT done here — needs its own workstream)

1. Make the image build stage `unified-api-contracts` at the SAME ref as the MTDS commit being built (or fail the build
   when the staged dep is behind the service's declared minimum).
2. Add an import smoke to the in-image `quality-gates` step: `python -m market_tick_data_service --help` (catches EVERY
   dep-skew class at build time, not at 00:35 cron time).
3. Rebuild + repush MTDS `:latest`, then re-run the three jobs and confirm `succeededCount=1`.
4. Consider pinning jobs to an immutable digest rather than `:latest` (a mutable-tag incident is already documented in
   `cloudbuild.yaml:209`, deployment-api 7da9baf 2026-07-13).

## Not fixed in this session — why

Deliberately NOT fixed by slot-1: the fix lives in the MTDS image-build / UAC publication path, and
`unified-api-contracts` had **LIVE uncommitted WIP** (mtime <120s: `registry/__init__.py`,
`registry/tradfi_instrument_universe.py`, `internal/reference/instrument.py`,
`tests/unit/test_yahoo_indices_and_dxy_source.py`) from another agent in the same tradfi workstream throughout this
session. Rebuilding or editing UAC underneath a live agent is a collision risk. Escalated to the operator instead, per
the big-finding triage rule.
