---
title:
  client-reporting-api Cloud Build RED fleet-wide — UTL base image carries UAC 0.23.0 but pyproject floor is
  unified-api-contracts>=0.24.0 (Dockerfile uv pip install cannot satisfy the floor)
created: 2026-06-20
source:
  - client-reporting-api Cloud Build 38a9d442 (FAILURE, head d6b70e4) — Step build, uv pip install resolution
  - client-reporting-api Cloud Build f4567a16 (FAILURE, head 1523a26 @ 10:11) — same step, same error
  - last SUCCESS = a9e59d3d (golive-9968cb1 @ 2026-06-20 01:57); every build since is RED
  - base image unified-trading-library:latest sha256:385c507… carries UAC 0.22.0;
    digest-pinned base sha256:56bbd50… (client-reporting-api Dockerfile) carries UAC 0.23.0
  - AR Python index (asia-northeast1-python.pkg.dev/.../unified-libraries) DOES carry UAC up to 0.27.0
locked_by: live-defi-rollout
priority: P0
status: resolved
parent_epic: deployment_and_user_management_master
---

> **✅ RESOLVED 2026-06-21 — client-reporting-api Cloud Builds GREEN again.** The UTL Docker base image was republished
> carrying UAC ≥ 0.24 (consumer Dockerfile now pins `BASE_IMAGE_DIGEST=sha256:dac7c8f6…`); **3 consecutive SUCCESS
> builds today** (10:40 / 11:16 / 12:27 UTC, latest `c8d1c78`) vs the last FAILURE 2026-06-20 13:23 — verified via
> `gcloud builds list`. Resolution = "Recommended decision" option 1 (republish the base, landed via the
> dependency-update fan-out). The reader-side P&L marks wiring (`d6b70e4`) can now rebuild + deploy. Archived
> 2026-06-21.

## What I found

Every `client-reporting-api` Cloud Build has FAILED since ~02:00 UTC 2026-06-20 (last SUCCESS = `golive-9968cb1` @
01:57). The failing step is the Docker `build` step, at the Dockerfile line:

```
RUN sed -i '/\[tool\.uv\.sources/,/^$/d' pyproject.toml && uv pip install --system .
```

with:

```
× No solution found when resolving dependencies:
  ╰─▶ Because unified-api-contracts was not found in the package registry and
      client-reporting-api==0.13.0 depends on unified-api-contracts>=0.24.0,<1.0.0 …
      → requirements are unsatisfiable.
```

Root cause — a **base-image dependency lag during an in-flight UAC promotion**:

- `client-reporting-api/pyproject.toml` floor is `unified-api-contracts>=0.24.0,<1.0.0` (bumped onto LDR `91ce99c`,
  2026-06-19 23:18).
- The Dockerfile strips `[tool.uv.sources]` (the local path deps) and relies on `uv pip install .` finding UAC either
  (a) **already installed in the UTL base image** (the fast path) or (b) in the AR Python index.
- The **digest-pinned UTL base image** the Dockerfile uses (`ARG BASE_IMAGE_DIGEST=sha256:56bbd50…`) carries
  **UAC 0.23.0** (verified: `docker run … python -c "import importlib.metadata as m; m.version('unified-api-contracts')"`
  → `0.23.0`). `unified-trading-library:latest` (`sha256:385c507…`, 2026-06-20 01:06) is even older — **UAC 0.22.0**.
- So path (a) fails (0.23.0 < 0.24.0 floor), and path (b) fails because the **inner `cloud-builders/docker` build layer
  has no auth/config to reach the AR Python index** (the cloudbuild `auth-precheck` only validates the OUTER build SA,
  not the inner `uv` in the docker layer) → `uv` reports "not found in the package registry".

The AR Python index itself **does** carry UAC 0.24.0–0.27.0, so the floor is satisfiable *in principle* — the gap is
purely that **no published UTL Docker base image (`:latest` or the pinned digest) has been republished with UAC ≥ 0.24**,
and the in-image `uv pip install` can't fall back to the index.

The last green build (`golive-9968cb1` @ 01:57) succeeded because the base image at THAT time pre-installed UAC ≥ 0.24;
the base has since regressed/re-pinned to 0.23.0.

## Why it matters

- **P0, May-23 critical path, cross-repo, fleet-wide.** client-reporting-api cannot be rebuilt or redeployed AT ALL —
  the live Cloud Run rev (`client-reporting-api-00004`, image `golive-1523a26`) is frozen; no fix can ship to it. This
  blocked the paper-trading P&L marks-wiring redeploy (`d6b70e4`, code shipped + QG-green on LDR) and blocks the parallel
  producer agent's strategy-service / ledger writes from being verified end-to-end against the live reporting service.
- It almost certainly affects **other consumer services** that floor `unified-api-contracts>=0.24.0` and build the same
  `uv pip install --system .` Dockerfile pattern against the same UTL base digest. (Worth a fleet check.)
- It is a **silent CI red** — the `golive-*` Cloud Run revision is live and serving, masking that every NEW build fails;
  there was no alert on the build going red at 02:00.

## Recommended decision

One of (dep-governance / base-image-publish owners — NOT a client-reporting-api-local fix; lowering the UAC floor or
pinning an older base from the consumer would be wrong):

1. **Republish the UTL Docker base image with UAC ≥ 0.24** (the dependency-update fan-out's job — a UTL/UAC promote that
   rebuilds + repushes `unified-trading-library:latest` and resolves a fresh digest), then bump the
   `BASE_IMAGE_DIGEST` ARG in consumer Dockerfiles via `update-dependency-version.yml`. **Preferred** — fixes the whole
   fleet at the base layer. OR
2. **Make the in-image `uv pip install` able to reach the AR Python index** (configure UV index URL + an
   access-token/keyring in the docker build layer, e.g. via a `--mount=type=secret` GH/AR token or a build-arg), so a
   consumer can pull a newer UAC than the base ships. Structural fix for the recurring base-lag class.

Until one lands, client-reporting-api (and any same-floor consumer) cannot rebuild. Composes with the related in-flight
UAC-promotion skew tracked in `utl_main_red_dep_resolution_skew_2026_06_11.md`.

## Status of the work this blocked (reader-side P&L marks wiring)

- **Code shipped + QG-green on LDR**: client-reporting-api `d6b70e4` — `read_marks()` reads the canonical run's
  `ledger_type=pricing` JSONL into `{asset_canonical_id -> Decimal}` and feeds `compute_pnl_entries(marks=...)` /
  `compute_ledger_views`; honest `marks_status="no_marks"` + `unrealized_pnl_total=null` fallback when no PricingLedger
  exists. Unit tests cover read_marks + the marks-driven and no-marks `/pnl` paths (54 tests green, full
  `quality-gates.sh` exit 0).
- **Redeploy BLOCKED** by this base-image lag. Once a buildable base lands, rebuild + deploy client-reporting-api and
  the marks-driven unrealized P&L goes live.
- At verify time (2026-06-20 ~13:00) the producer's `ledger_type=pricing` and `pnl_attribution/` objects were **NOT yet
  on GCS** for `firm-paper-determinism`, so the live behaviour to expect first is the honest no-marks path; non-zero
  unrealized populates once the producer's next run writes the PricingLedger.
