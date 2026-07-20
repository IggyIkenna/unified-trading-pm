---
doc_type: issue
title: MTDS image missing yfinance (`pip install -e . --no-deps`) — ICE/FX/KRX tradfi MVP venues fail every run
summary:
  market-tick-data-service declares `yfinance>=0.2.66,<1.0.0` (pyproject.toml:60) but the Dockerfile installs the
  service with `uv pip install --system -e . --no-deps` (Dockerfile:189), so NONE of MTDS's own declared runtime deps
  are installed into the image — they rely entirely on what the base image bakes, and yfinance is absent. The Yahoo
  Finance adapter (market_interface/adapters/tradfi/yahoo_finance_adapter.py) imports yfinance LAZILY inside a function,
  so the import smoke test (`import market_tick_data_service`) passes and never catches it. Result: every ICE / FX / KRX
  fetch (all Yahoo-routed) fails at runtime with a missing-module error — these are tradfi MVP venues, so MVP coverage
  is directly suppressed (corroborated live 2026-07-20: an un-forced tradfi T+1 freshness check reports ICE/FX/KRX as
  `missing`).
status: open
nature: issue
asset_group: [tradfi]
stage: [data, infra]
repos: [market-tick-data-service]
scope: [engineer]
tags: [docker, dependencies, tradfi, mvp, production, big-finding]
related:
  [
    mtds_image_uac_dep_skew_breaks_all_cloud_run_jobs_2026_07_20.md,
    tradfi_schema_version_string_regression_2026_07_20.md,
    tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-20
source:
  - tradfi_consolidated_closeout_2026_07_18.md (P1 dispatched alongside the schema_version P0)
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
---

> **🟡 OPEN — needs a Cloud Build to verify.** Deliberately NOT shipped alongside the schema_version P0 (an unverifiable
> image change must not destabilise a P0 restore; gcloud CLI reauth was broken in the P0 session so no Cloud Build could
> be triggered/cited).

# yfinance absent from the MTDS image

## Root cause (file:line)

- `market-tick-data-service/Dockerfile:189` — `RUN uv pip install --system -e . --no-deps`. `--no-deps` installs the
  MTDS package WITHOUT its declared dependencies; the image relies on the base image (which bakes UTL + UAC + common
  deps) for everything else. `yfinance` is an MTDS-specific dep the base image does not provide.
- `market-tick-data-service/pyproject.toml:60` — `"yfinance<1.0.0,>=0.2.66"` is declared but therefore never installed.
- `market_tick_data_service/market_interface/adapters/tradfi/yahoo_finance_adapter.py` — `import yfinance as yf` is a
  lazy in-function import (`# noqa: qg-inside-import`), so `import market_tick_data_service` (the image import smoke)
  succeeds; the failure only surfaces at fetch time for ICE/FX/KRX.

## Blast-radius assessment (why NOT just drop `--no-deps`)

Removing `--no-deps` makes `uv` re-resolve and install MTDS's ENTIRE declared dependency tree fresh, which can conflict
with the base-image-baked, LDR-tip editable installs of UTL/UAC and their pinned transitive deps (the base image is
frozen at `BASE_IMAGE_DIGEST`; a full re-resolve can pull incompatible versions, bloat the image, or fail the build).
That is a whole-image dependency-resolution change — higher risk than the P0 it was dispatched beside.

## Recommended fix (targeted, low blast-radius)

Add an explicit install of ONLY the missing runtime dep(s), leaving line 189's `-e . --no-deps` untouched, immediately
after it in the Dockerfile:

```dockerfile
# MTDS-specific runtime deps NOT baked into the base image (the `-e . --no-deps` above
# skips ALL declared deps). yfinance is Yahoo-routed ICE/FX/KRX (tradfi MVP) — absent it,
# those venues fail every run. See mtds_image_missing_yfinance_no_deps_2026_07_20.md.
RUN uv pip install --system --no-cache-dir "yfinance>=0.2.66,<1.0.0"
```

yfinance's own transitive deps (pandas/numpy/requests/…) are already in the base image, so this adds only yfinance + a
few small packages — no whole-tree re-resolution.

Then **audit whether other declared MTDS deps are also absent** (the `--no-deps` install means any dep the base image
doesn't bake is missing): diff `pyproject.toml`'s dependency list against the image's `uv pip freeze` and add explicit
installs for every genuinely-missing runtime dep (or, if the set is large, reconsider the `--no-deps` posture with a
pinned constraints file).

## Verification required before closing

Runtime-verification hard rule: build the image via Cloud Build and cite `Evidence: cloudbuild=<id>` SUCCESS, then
confirm a real ICE/FX/KRX tradfi fetch no longer fails on the missing import (or that `uv pip freeze` in the built image
lists yfinance). This was NOT completed in the P0 session (broken gcloud CLI reauth → no Cloud Build).

## Todos

- [ ] [INFRA] P1. Add targeted `uv pip install yfinance` to the Dockerfile after line 189 (do NOT remove `--no-deps`).
- [ ] [INFRA] P1. Audit `pyproject.toml` deps vs the built image's `uv pip freeze` for other absent runtime deps.
- [ ] [VERIFY] P1. Cloud Build + cite SUCCESS id; confirm ICE/FX/KRX fetch imports yfinance (or freeze lists it).
