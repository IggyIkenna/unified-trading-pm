---
title: UAC weekly-validation workflow failing — WIF_PROVIDER/WIF_SERVICE_ACCOUNT secrets not configured
created: 2026-05-17
source:
  - "gh run 25660560812 (2026-05-11 cron) + 4 prior failures back to 2026-04-13"
  - unified-api-contracts/.github/workflows/weekly-validation.yml:42-45
locked_by: live-defi-rollout
locked_since: 2026-05-17
severity: P3 — non-blocking (cron schema-validation only; per-PR CI unaffected)
status: RESOLVED 2026-05-20
resolved_by: ikenna-slot-1
resolved_via:
  - "unified-api-contracts@18c74a56 (canary scripts)"
  - "WIF pool github-pool + provider github-actions in central-element-323112"
  - "SA uac-weekly-validation-ci@central-element-323112.iam.gserviceaccount.com (roles/secretmanager.secretAccessor +
    workloadIdentityUser bound to IggyIkenna/unified-api-contracts repo principal set)"
  - "GH secrets WIF_PROVIDER + WIF_SERVICE_ACCOUNT + GCP_PROJECT_ID set on UAC repo"
verified_via:
  "gh run 26157265855 (workflow_dispatch on live-defi-rollout, all 17 steps green; auto-filed UAC issue #45 with 11/44
  drift findings)"
priority: P2
---

## Resolution (2026-05-20)

Shipped Option A (Workload Identity Federation) **plus** the missing scripts the workflow was pointing at — the original
issue doc surfaced only the WIF secret gap, but mid-execution it emerged that `scripts/collect_responses.py` and
`scripts/validate_schemas.py` had never existed in git history (only `tests/test_schema_validation.py` shipped). So WIF
alone would have produced a vacuous-green workflow. Both were built end-to-end.

**Canary design (post-resolution SSOT)**: rather than a hand-built endpoint registry, the canary walks the existing VCR
cassettes in `unified_api_contracts/external/*/mocks/*.yaml` and replays each cassette's first interaction against the
live API (subject to a safe-replay filter that skips Authorization-headered cassettes, POST writes, internal hosts,
negative-test cassettes, etc.). Validation is a structural diff of the live response vs the cassette's recorded body.
See script docstrings for the full policy.

**Follow-ups** (filed as separate issue docs):

- `defunct_uac_provider_dirs_cleanup_2026_05_20.md` — 12 dirs operator flagged as defunct (glassnode, cryptoquant,
  coinglass, cryptopanic, hyblock, lunarcrush, fear_greed, coingecko, sharpapi, dydx, prime_broker, regulatory).
  Cross-repo because MTDS has a `sharpapi_adapter.py` and tests referencing fear_greed + dydx.
- The auto-filed UAC issue **#45** ("Schema Validation Failed: 11/44 endpoints") captures live drift findings the canary
  surfaced on first run: kalshi API migrated to `api.elections.kalshi.com`, manifold/polymarket/tardis schema changes,
  yahoo_finance crumb issues. These are the canary doing its intended job, not bugs in the canary.

## What I found

`unified-api-contracts/.github/workflows/weekly-validation.yml` has been failing every Monday cron since at least
**2026-04-13** (5 consecutive weekly runs):

```
##[error]google-github-actions/auth failed with: the GitHub Action workflow must specify
exactly one of "workload_identity_provider" or "credentials_json"! ... ensure the secret
is being injected into the environment.
```

The workflow declares:

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
    service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
```

But `WIF_PROVIDER` and `WIF_SERVICE_ACCOUNT` aren't set in the repo's GitHub secrets, so the auth action receives empty
strings → exits with the error above. No GCP calls fire; the validation script never runs; the workflow exits 1 every
Monday morning.

## Why it matters

This is **not a May-23 critical-path blocker** — the weekly schema validation is informational (catches provider API
drift over time; the per-PR `Schema Health` workflow shipped 2026-05-17 ikenna-slot-3 at UAC@`ddbe7ad` is the gating
one). But:

1. **Noise**: weekly red badge on UAC repo for ~5 weeks, masking real failures.
2. **Drift detection lost**: providers (Databento, Tardis, Polygon, etc.) may have shipped breaking schema changes since
   2026-04-13 that the cassette-based per-PR Schema Health check can't catch (cassettes are replays; weekly is the only
   live-API canary).
3. **Cassette staleness blind-spot**: without periodic live validation, cassettes get progressively more out-of-date vs.
   live API responses → schema-health.svg lies about provider freshness.

## Recommended decision

Operator picks one of three paths:

**Option A — Provision Workload Identity Federation** (CLEANEST, ~30 min operator):

1. Create WIF pool + provider in GCP project `central-element-323112` trusting GitHub Actions OIDC for
   `IggyIkenna/unified-api-contracts`.
2. Bind a service account (e.g. `uac-weekly-validation-ci@central-element-323112.iam.gserviceaccount.com`) with
   read-only access to Secret Manager (to fetch provider API keys).
3. Set GitHub secrets `WIF_PROVIDER`
   (`projects/<num>/locations/global/workloadIdentityPools/<pool>/providers/<provider>`) + `WIF_SERVICE_ACCOUNT` (the SA
   email).
4. Manually-dispatch the workflow to verify green.

**Option B — Switch to credentials_json secret** (FASTER, weaker security):

1. Create a service-account JSON key (read-only Secret Manager access).
2. Set GitHub secret `GCP_SA_KEY` to the JSON contents.
3. Edit workflow to use `credentials_json: ${{ secrets.GCP_SA_KEY }}` instead of WIF.

**Option C — Disable the workflow** (HONEST, accepts lost canary):

1. Remove the cron trigger (`workflow_dispatch` only).
2. Add explanatory comment that live API validation runs manually before each UAC release.

Slot-3 cannot ship any of these without operator decision on (a) which option + (b) GCP IAM ops authority for Option
A/B.

## Cross-references

- Companion `Schema Health` workflow fixed 2026-05-17 at UAC@`ddbe7ad` (cassette-replay, not live API).
- Per CLAUDE.md "External Data Is Always Available — Never Silently Defer Adapters": this is a **CI-credential**
  concern, not a data-availability one — provider APIs are reachable, just GHA-side auth isn't configured.
