---
doc_type: issue
title: MTDS image missing yfinance (`pip install -e . --no-deps`) — ICE/FX/KRX tradfi MVP venues fail every run
summary: >-
  market-tick-data-service declares `yfinance>=0.2.66,<1.0.0` (pyproject.toml:60) but the Dockerfile installs the
  service with `uv pip install --system -e . --no-deps` (Dockerfile:189), so NONE of MTDS's own declared runtime deps
  are installed into the image — they rely entirely on what the base image bakes, and yfinance is absent. The Yahoo
  Finance adapter (market_interface/adapters/tradfi/yahoo_finance_adapter.py) imports yfinance LAZILY inside a function,
  so the import smoke test (`import market_tick_data_service`) passes and never catches it. Result: every ICE / FX / KRX
  fetch (all Yahoo-routed) fails at runtime with a missing-module error — these are tradfi MVP venues, so MVP coverage
  is directly suppressed (corroborated live 2026-07-20: an un-forced tradfi T+1 freshness check reports ICE/FX/KRX as
  `missing`).
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
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
parent_epic: tradfi_master
locked_by:
resolved_by:
  "market-tick-data-service@d8dc04e1 — cloudbuild=ce814d53-1648-4cf4-b2dc-7ac6bffefecd SUCCESS; see RESOLVED banner"
source:
  - tradfi_consolidated_closeout_2026_07_18.md (P1 dispatched alongside the schema_version P0)
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
---

> **🟢 RESOLVED 2026-07-20 — `market-tick-data-service@d8dc04e1`.** Targeted pinned `yfinance==0.2.66` install added to
> the Dockerfile after the `-e . --no-deps` line (NOT removing `--no-deps`); `import yfinance` added to the cloudbuild
> `image-import-smoke` so a missing lazily-imported dep now fails the BUILD. Runtime-verified end to end:
> `Evidence: cloudbuild=ce814d53-1648-4cf4-b2dc-7ac6bffefecd` (SUCCESS, built the shipped sha `d8dc04e1`) — the in-image
> smoke printed `YFINANCE OK 0.2.66 /usr/local/lib/python3.13/site-packages/yfinance/__init__.py` and
> `IMPORT SMOKE OK: market_tick_data_service.__main__ imported cleanly` (UAC/UTL 0.55.0 from the staged `.deps`), and
> the smoke gates the `push` step so the image cannot ship without yfinance. (Corroborating first build of the same
> edits: `cloudbuild=ce527e9f-d8fd-4538-b8b7-e0b8e7687de7`, SUCCESS, same `YFINANCE OK 0.2.66`.) A live KRX/ICE/FX venue
> fetch was deliberately NOT run — it writes the prod tick bucket + manifest, which concurrent agents were actively
> touching; the in-image import proof is the closing evidence.

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

## Other-absent-deps audit result (2026-07-20)

The `-e . --no-deps` install silently skips **every** declared MTDS dependency, but the build-time
`import market_tick_data_service.__main__` smoke already transitively imports every dep that is a **top-level** import
in the runtime module chain — so a top-level-imported missing dep would already fail the (now-run) build. The only
silently-degradable class is therefore **lazily** (in-function) imported declared deps. Enumerating those
(`rg '^\s+import (…)' + qg-inside-import`): `yfinance`, `databento`, `web3`, `ccxt` — plus `polars` (benchmark script
only, no runtime top-level import) and `ib_insync` (NOT declared in `pyproject.toml` at all — undeclared optional IBKR
dep, a separate class, non-MVP). Of the lazily-imported **declared** deps, only `yfinance` is genuinely absent:
`databento`/`web3`/`ccxt` are provided by the UTL base image (their venues — databento-tradfi, DeFi-Alchemy, CeFi-ccxt —
collect fine in prod; only the Yahoo-routed venues were `missing`). Confirmed empirically: the built image's
`image-import-smoke` imports `market_tick_data_service.__main__` (which pulls the databento/ccxt/web3 chains) cleanly.
**Conclusion: `yfinance` was the sole silently-absent declared runtime dep** — a single pinned install closes the gap;
no other declared runtime dep needed adding.

## Todos

- [x] [INFRA] P1. Add targeted pinned `uv pip install "yfinance==0.2.66"` to the Dockerfile after the `-e . --no-deps`
      line (do NOT remove `--no-deps`; NOT `--no-deps` on the yfinance install so its small new transitive deps come
      along). — `market-tick-data-service@d8dc04e1` (Dockerfile).
- [x] [INFRA] P1. Audit `pyproject.toml` deps vs what `-e . --no-deps` + base image provide — see the audit above;
      `yfinance` is the only genuinely-absent declared runtime dep. — `market-tick-data-service@d8dc04e1`.
- [x] [VERIFY] P1. Cloud Build SUCCESS + import proof. — `Evidence: cloudbuild=ce814d53-1648-4cf4-b2dc-7ac6bffefecd`
      (SUCCESS, shipped sha `d8dc04e1`); in-image smoke `YFINANCE OK 0.2.66` + `IMPORT SMOKE OK`. Live venue fetch not
      run (prod tick bucket / manifest under concurrent-agent contention); in-image import proof is the closing
      evidence.
