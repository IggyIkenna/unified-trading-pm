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
status: resolved
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
  market-tick-data-service@21733255 (cloudbuild=316b0733-42e8-4b8e-82ab-4ad8f1695a84 SUCCESS) market-tick-data-service
  (cloudbuild.yaml stage-workspace-deps + image-import-smoke, Dockerfile workspace-dep refresh)
source: A3-3 tradfi T+1 job verification (slot-1)
---

> **✅ RESOLVED 2026-07-20 `[slot-1·laptop]`.** Root cause was NOT "the build stages a stale UAC" — MTDS's build stages
> no UAC at all. The Dockerfile is `FROM unified-trading-library@${BASE_IMAGE_DIGEST}` (`Dockerfile:115`) and the UTL
> BASE IMAGE bakes `/app/.deps/unified-api-contracts` (UTL `cloudbuild.yaml:92` `clone-uac-source`), so UAC/UTL inside
> every MTDS image are frozen at the LDR tip the BASE image was built from — never the ref MTDS is built from. Fixed by
> staging UAC+UTL at LDR tip in MTDS's own build and installing them over the base copies, plus a REQUIRED
> `image-import-smoke` step that gates `push`. Also found: the "REQUIRED" in-image `quality-gates` step was a SILENT
> NO-OP on every build. Shipped `market-tick-data-service@21733255`;
> `Evidence: cloudbuild=316b0733-42e8-4b8e-82ab-4ad8f1695a84` SUCCESS (built from the COMMITTED LDR source, all 14
> steps). **Tradfi verdict: `exit(0)` + 288,958 rows / 590 shards** (date=2026-07-17). See § Resolution.
>
> **Scope note (operator, 2026-07-20)**: this workstream's verification lane is the **tradfi** T+1 job ONLY. The
> fleet-wide blast radius below is documented for the owning workstreams; **verification of `cefi-t1-recon` and
> `fast-t1-recon` is explicitly left to their owners** and was not performed as a deliverable here.

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

## Resolution (2026-07-20, `[slot-1·laptop]`)

### Actual root cause — the base image, not the MTDS build

The original diagnosis above ("the image build is staging a UAC older than the LDR tip") was directionally right about
the SYMPTOM but wrong about the MECHANISM, and the difference matters because it explains why this recurs:

- `market-tick-data-service/Dockerfile:115-116` — `ARG BASE_IMAGE_DIGEST=sha256:111ae3fb…` +
  `FROM unified-trading-library@${BASE_IMAGE_DIGEST}`.
- `unified-trading-library/cloudbuild.yaml:92` (`clone-uac-source`) clones UAC into `/workspace/.deps/` and
  `unified-trading-library/Dockerfile:88` installs it — so **the UTL BASE IMAGE is what bakes
  `/app/.deps/unified-api-contracts`**. MTDS's own build staged NO UAC whatsoever.
- ⇒ UAC/UTL inside an MTDS image are pinned to whatever LDR tip the **base image** was built from. `BASE_IMAGE_DIGEST`
  sha256:111ae3fb was built 2026-07-19T18:09; `uac@7e179ae8` landed 2026-07-20T02:47. The image could not have had the
  symbol no matter how many times MTDS rebuilt.
- **A UAC-only commit never triggers a UTL base rebuild at all**, so hand-bumping `BASE_IMAGE_DIGEST` (the fix applied
  on 2026-07-16 for `venue_data_type_has_batch_source`, and ~8 times before that per the Dockerfile header) only
  re-freezes the skew at a newer instant. It is a workaround, not a fix — which is why the same outage recurred.

Measured on the deployed `:latest` (`sha256:724d8170`) BEFORE the fix:

```
is_recognized_tradfi_underlying: False
file: /app/.deps/unified-api-contracts/unified_api_contracts/__init__.py   # ← the base image's frozen copy
```

### Why it shipped silently — the REQUIRED gate was a no-op

`cloudbuild.yaml` step `quality-gates` runs `scripts/quality-gates.sh --no-fix --quick` inside the image. That script
resolves the PM base script via `git rev-parse` (`quality-gates.sh:139-140`), which does not exist in the image, and
then hits `quality-gates.sh:141-145`:

```bash
if [ ! -f "${BASE_QG_SCRIPT}" ]; then
    if [ "${CLOUD_BUILD:-false}" = "true" ]; then
        echo "quality-gates base script unavailable in image; skipping in-image gate pass"
        exit 0
```

Confirmed in the build log of `54919c59` (the last pre-fix build):

```
Step #6 - "quality-gates": fatal: not a git repository (or any of the parent directories): .git
Step #6 - "quality-gates": quality-gates base script unavailable in image; skipping in-image gate pass
```

So the step advertised as "REQUIRED: test the artifact you deploy" has been passing **vacuously on every build** — the
direct reason four dep-skewed images were pushed on 2026-07-20 while the whole fleet was dead.

### The fix (market-tick-data-service)

1. **`cloudbuild.yaml` — new `stage-workspace-deps` step** (gates `build`): full clone (NOT `--depth=1`, both repos are
   hatch-vcs and need tags to satisfy the `>=0.33.0` / `>=0.13.0` floors) of `unified-api-contracts` +
   `unified-trading-library` at `live-defi-rollout` tip into `.deps/`.
2. **`Dockerfile` — workspace-dep refresh block**: installs those staged copies over the base image's. UTL FIRST then
   UAC LAST (UTL depends on UAC; resolving it last would let uv satisfy UAC from an AR wheel and clobber the editable
   install); `--no-sources` on UTL (its `[tool.uv.sources]` points at a sibling path absent from this build context);
   placed BEFORE the `SETUPTOOLS_SCM_PRETEND_VERSION` ENV so MTDS's version does not stamp UAC/UTL. Both guarded by
   `if [ -d .deps/… ]` so a plain local `docker build` is unaffected.
3. **`cloudbuild.yaml` — new REQUIRED `image-import-smoke` step**, added to `push`'s `waitFor` so a skew CANNOT ship:
   `import market_tick_data_service.__main__` inside the built image walks the exact outage traceback. Deliberately a
   pure import, NOT `--help`: `--help` executes `main_service_cli()` → `ServiceBootstrap`, which is runtime-config
   dependent and would flake as a build gate. It also prints each dep's resolved `__file__` for provenance.

### Evidence

Shipped as `market-tick-data-service@21733255` (quickmerge → LDR).
`Evidence: cloudbuild=316b0733-42e8-4b8e-82ab-4ad8f1695a84` — **SUCCESS**, all 14 steps SUCCESS
(`gcloud builds describe`, region `asia-northeast1`), built from a clean clone of the **committed** LDR source (not a
local working tree), so the fix is proven reproducible from the branch. Image `:latest` → `sha256:30afa009…` (tag
`21733255`). Build log:

```
Step #2 - "stage-workspace-deps": staged unified-api-contracts @ 1663f6f7 (tag v0.72.0)
Step #2 - "stage-workspace-deps": staged unified-trading-library @ 51b73604 (tag v0.55.0)
Step #8 - "image-import-smoke": UAC 0.55.0 /app/market-tick-data-service/.deps/unified-api-contracts/…/__init__.py
Step #8 - "image-import-smoke": UTL 0.55.0 /app/market-tick-data-service/.deps/unified-trading-library/…/__init__.py
Step #8 - "image-import-smoke": IMPORT SMOKE OK: market_tick_data_service.__main__ imported cleanly
```

Resolved dep paths are now `/app/market-tick-data-service/.deps/…` (this build's staged copies) rather than the base
image's frozen `/app/.deps/…` — that path change IS the fix, visible in the build log. (An earlier identical build from
the pre-commit working tree, `cloudbuild=2bb2c71c-c43c-4e97-9613-cacdf81b6976`, also resolved SUCCESS.)

### Tradfi verification — IN LANE, PASSED (rows, not just an exit code)

| Execution               | Args                            | Exit        | Rows written                                                       |
| ----------------------- | ------------------------------- | ----------- | ------------------------------------------------------------------ |
| `…-nbbkx` (**verdict**) | date 2026-07-17, `--force`      | **exit(0)** | **288,958 rows / 590 shards / 4 venues** — `Manifest updated`      |
| `…-9c9nb`               | date 2026-07-17, no force       | SIGKILL     | 6,782 rows (pre-poisoning run)                                     |
| `…-8hfw7`               | dates 2026-07-16/17, no force   | SIGKILL     | 5,189 rows CBOE/VIX → canonical `…/day=2026-07-16/…/ticks.parquet` |
| `…-xfrvc`               | prod config (no dates/no force) | exit(1)     | 0 — crashes in `check_shard_freshness`, see finding 3 below        |

Per-venue on the passing run: NYSE **241,821 rows / 522 partitions**, CME 2,391 / 7, plus NASDAQ + CBOE. **The P0
ImportError is definitively gone** — the service now boots, authenticates, fetches from Databento, writes canonical
parquet and updates the manifest. A deliberate malformed-args probe (`…-78jp7`) exited 2 at **argparse**, which is
itself proof that module import now succeeds.

`--force` was required only to bypass the freshness-check crash in finding 3 (an unrelated, newly-surfaced data bug); it
does not weaken the row proof — the run performed real fetching and wrote a real manifest.

**T-1 caveat**: the completion criterion "writes rows for T-1" is unattainable _today_ for tradfi regardless of code —
today is Monday 2026-07-20, so T-1 = **Sunday 2026-07-19**, on which all 7 tradfi venues are closed and the correct
result is an honest-absence row with zero data rows. Row-writing was therefore proven on the most recent real trading
day (Friday 2026-07-17).

### Out of lane — left to the owning workstreams

Per the operator scope correction, non-tradfi jobs were **not** validated as a deliverable here:

- **`cefi-t1-recon` — NOT RUN, deliberately.** VM `cefi-queue-heavy-binancefutu-x17-20260720-102103`
  (`VM_TARDIS_CONSUMER=1`, all Tardis venues, 2026-02-27→2026-07-19) held the single-IP Tardis budget throughout. The
  cap is a **HARD 1 concurrent** (CLAUDE.md § VM/infra): N>1 measured ~94% 403s + **37,212 FALSE `attempted_failed`
  rows** — manifest CORRUPTION, strictly worse than not running. Left to the CeFi owner; re-run once that backfill
  finishes.
- **`fast-t1-recon`** was executed once BEFORE the scope correction landed and incidentally came back `exit(0)` with
  **969,536 rows / 2,494 shards / 24 venues** (day=2026-07-19). Recorded as a corroborating observation only — its
  formal verification belongs to its owner.

## Follow-on defects found while verifying (NEW — not the ImportError)

1. **P1 — `yfinance` is missing from the image; ICE/FX/KRX fail on EVERY tradfi run.** Both trading-day executions
   logged `3/7 venues failed: {'ICE': "No module named 'yfinance'", 'FX': …, 'KRX': …}`. `yfinance<1.0.0,>=0.2.66` IS
   declared (`pyproject.toml:60`) but `Dockerfile:152` installs with `uv pip install --system -e . --no-deps` — so
   MTDS's declared runtime deps are NEVER installed; they are inherited from the UTL base image, which does not carry
   yfinance. Same "deps come from the frozen base image" family as this issue, different symptom. The import smoke does
   NOT catch it because `yahoo_finance_adapter.py` imports yfinance lazily inside a function. NOT fixed here: dropping
   `--no-deps` changes dependency resolution for the whole image and must not ride along on a P0 hotfix verification.
2. **P1 — `tradfi-databento-t1-recon` SIGKILLs (signal 9) at 2cpu/8Gi on a real trading day, AFTER writing rows.** Both
   trading-day runs wrote their parquet + manifest, then idled at cpu≈0% / rss≈5,475 MiB for ~2 min and were killed.
   Data lands, but the execution is reported FAILED, so the job self-reports red on every trading day. The prod Sunday
   run exited 0 only because a non-trading day does no work. (The later `--force` run completed cleanly in ~11 min, so
   this is likely a hang in the freshness/consolidator read path rather than pure memory pressure.)
3. **P0 (data-correctness) — the ENTIRE tradfi availability index has `schema_version` typed as STRING, which hard-fails
   every un-forced MTDS tradfi run.** Measured directly on
   `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`: **5,208,844 / 5,208,844
   rows** have `schema_version == "9"` (Python `str`, column dtype `object`) instead of int `9`. UTL
   `manifest_writer/_queries.py:165` does `if row.get("schema_version", 1) < MANIFEST_SCHEMA_VERSION:` → `"9" < 9` →
   `TypeError: '<' not supported between instances of 'str' and 'int'`, which propagates out of `check_shard_freshness`
   and kills the job (`tick_data_handler.py:407` → `:178`). That UTL line is unchanged since 2026-06-24, so **this is a
   data regression, not a code regression** — something rewrote the index with a string column. Timeline brackets it
   tightly: prod-config execution `…-g24t7` succeeded at 12:44, `…-xfrvc` crashed on it at 14:49, and
   `canonical-migration-tradfi-catalogue-canon-20260720-132251` was running in between. NOT investigated further or
   fixed here: this session was explicitly instructed not to touch the migration / rebundle / recover scripts or the
   catalogue tooling, and that VM is another workstream's in-flight run. **Effect: the tradfi T+1 cron will fail every
   night until this is fixed**, because the scheduled invocation passes no `--force`.

All three are filed as todos on `tradfi_consolidated_closeout_2026_07_18.md` (§ A3).

## Not fixed in this session — why

Deliberately NOT fixed by slot-1: the fix lives in the MTDS image-build / UAC publication path, and
`unified-api-contracts` had **LIVE uncommitted WIP** (mtime <120s: `registry/__init__.py`,
`registry/tradfi_instrument_universe.py`, `internal/reference/instrument.py`,
`tests/unit/test_yahoo_indices_and_dxy_source.py`) from another agent in the same tradfi workstream throughout this
session. Rebuilding or editing UAC underneath a live agent is a collision risk. Escalated to the operator instead, per
the big-finding triage rule.
