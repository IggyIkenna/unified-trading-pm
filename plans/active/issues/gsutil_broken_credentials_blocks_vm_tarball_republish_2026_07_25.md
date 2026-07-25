---
doc_type: issue
title: gsutil has no working credentials on this host — blocks code-tarball republish before any VM launch
summary: >-
  `gsutil` (used internally by deployment-service's `create-code-tarballs.sh` + `launcher_common.sh`'s
  `lc_verify_tarball_freshness`/`lc_resolve_tarball_sha`) authenticates as an anonymous caller on this host regardless
  of active gcloud account: the workload-identity-federation service account
  (`github-actions-deploy@central-element-323112.iam.gserviceaccount.com`) has an expired Identity Pool subject token
  with no visible refresh path, and the human account (`ikenna@odum-research.com`) requires an interactive 2FA reauth
  challenge (`ReauthUnattendedError: ... not in an interactive session`) that cannot be answered headlessly. Neither
  `CLOUDSDK_AUTH_ACCESS_TOKEN` (derived from a working ADC token) nor unsetting the active account gets gsutil to pick
  up valid credentials — it falls back to `Anonymous caller` either way. By contrast, the modern `gcloud
  storage`/`gcloud compute` CLI (not gsutil) DOES work correctly with a `CLOUDSDK_AUTH_ACCESS_TOKEN` derived from
  `gcloud auth application-default print-access-token` — confirmed via `gcloud storage ls` and a real `gcloud compute
  instances create` launch both succeeding. This blocks any VM launcher that republishes/verifies code tarballs before
  launch (the standard pattern for MDPS/sports/etc. backfill VMs) until either the service-account federation is
  refreshed or a human runs an interactive `gcloud auth login` once.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [gcloud, gsutil, credentials, vm-launcher, infra, blocked-credentials]
related: []
created: 2026-07-25
assigned_vm: NA
parent_epic: infrastructure_master
execution_scope: local-only
priority: P1
estimate_class: infra
source: >-
  Hit while trying to launch mdps-sports-bucket-vm for sports_satellite_ao_dispatch_batch2_2026_07_24.md's league_id
  casing migration todo (odds_horizon_bucket MDPS reprocess step) — needed a fresh tarball republish first since the
  deployed tarballs predate `unified-trading-library@14301571` (the TOCTOU consolidator-race fix), and the reprocess
  script's `ManifestWriter` writes directly to the canonical index (no `MANIFEST_PER_VM_SHARDS`), so stale code would
  re-expose the exact race that already silently reverted the league_id manifest swap once this session.
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# gsutil has no working credentials on this host

## What happened

Launched `mdps-sports-bucket-20260725-012214` via `deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh` for a
real reprocess job. The launcher warned: 5 STALE code tarball(s) (market-data-processing-service,
market-tick-data-service, unified-api-contracts, unified-trading-library, deployment-service) — the VM would fetch
pre-fix code, specifically predating `unified-trading-library@14301571` (2026-07-24), which is load-bearing for this
exact job (the reprocess script's `ManifestWriter` is constructed plain — `service_name` + `catalogue_bucket`, no
`MANIFEST_PER_VM_SHARDS`/`VM_NAME` sharding — so its writes go through the same canonical-index CAS path that already
silently reverted once this session; see
`/plans/active/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`). **Deleted the VM immediately**
(launched <1 min earlier, zero real work done) rather than let it run on stale code.

## Root cause — gsutil auth broken, gcloud/gcloud-storage auth fine

Attempted `bash scripts/vm/create-code-tarballs.sh --include <5 repos>` to republish. All 5 repos were git-clean at
recent HEADs (verified via `git status --porcelain` + `git log -1` per repo before running). The LOCAL tarball-build
step succeeded every time; every UPLOAD attempt (`gsutil -m cp ...`) failed:

1. First attempt (default account = the service account): `ResumableUploadAbortException` /
   `('Unable to retrieve Identity Pool subject token', '{"source":"actions-run-service","statusCode":401, "errorMessage":"token has invalid claims: token is expired"}')`.
2. `gcloud config set account ikenna@odum-research.com` then `gcloud auth print-access-token`:
   `ReauthUnattendedError: Reauthentication challenge could not be answered because you are not in an interactive session`
   — this account has a 2FA/session reauth policy that cannot be satisfied headlessly.
3. `export CLOUDSDK_AUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)` — the ADC token itself IS
   valid (confirmed: `gcloud storage ls gs://.../code/` succeeded, listing real objects). But `gsutil cp` with this same
   env var set still failed: `401 Anonymous caller does not have storage.objects.create access`.
4. `gcloud config unset account` + retry `gsutil` — same `Anonymous caller` result; gsutil does not fall back to
   `GOOGLE_APPLICATION_CREDENTIALS`/ADC the way `gcloud storage` does.

**Conclusion**: `gsutil` (the legacy Python tool, distinct auth stack from the modern `gcloud` CLI) has no working
credential path on this host at all right now — not the service account (federation token expired), not the human
account (needs interactive reauth), not ADC via the access-token env var. `gcloud storage`/`gcloud compute` (the modern
replacements) DO work correctly with the ADC-derived `CLOUDSDK_AUTH_ACCESS_TOKEN` — confirmed via both
`gcloud storage ls` and a real `gcloud compute instances create` (the VM launch itself succeeded on the first attempt,
before I deleted it for the stale-tarball reason above — the CREATE call itself is not gsutil-dependent).

## Why this matters beyond my immediate task

`launcher_common.sh`'s `lc_verify_tarball_freshness`, `lc_resolve_tarball_sha`, and `lc_verify_setup_script_freshness`
(called automatically by `lc_gcloud_create`, i.e. inside every `launch-*.sh` that uses the shared library) all shell out
to `gsutil` internally (`command -v gsutil` gate + `gsutil -q cp`/`gsutil cat`). Any worker on this host attempting to
launch a VM via the standard launcher pattern will hit the same silent-stale-tarball risk (the freshness check itself
can't run, so launches proceed with whatever warning-only behavior the script defaults to) until this is fixed.

## What would fix it (not attempted — needs a human or a working service-account credential)

- **Fastest**: a human runs `gcloud auth login` interactively once (answers the 2FA/reauth challenge for
  `ikenna@odum-research.com`), which should refresh gsutil's credential store for that account.
- **Alternative**: refresh/reissue the `github-actions-deploy@...` service account's workload-identity-federation token
  (source: `actions-run-service`) — root cause of why it's expired with "invalid claims" wasn't investigated further,
  out of scope for this finding.
- **Workaround for future launches** (not implemented here): patch `launcher_common.sh`'s `gsutil` call sites to use
  `gcloud storage`/`gcloud compute` equivalents instead, which are confirmed working with ADC on this host — would
  remove the gsutil dependency entirely, not just work around today's expired token. Flagged as a follow-up, not
  attempted here (out of scope for a single blocked-credentials finding; a real code change to a shared infra library
  needs its own review, not a rushed patch under a credential deadline).

## What I did instead

Given the reprocess step (MDPS `odds_horizon_bucket` regeneration) is genuinely credential-blocked, completed the other
two achievable sub-goals of the parent todo directly (no VM/gsutil needed — both read-only against GCS via the working
`google-cloud-storage`/ADC path, proven throughout this session):

- **Coverage-registry refresh** — ran `refresh_sports_bookmaker_league_coverage_2026_06_21.py` (diff mode, no
  `--write`): "No drift vs committed coverage map" — already current. Directly confirmed the todo's own done-when
  criterion: `is_bookmaker_league_covered("BETFAIR_EX_EU", "EPL")` = `True`,
  `is_bookmaker_league_covered("BETFAIR_EX_EU", "PREMIER_LEAGUE")` = `False` — the exact False→True flip the todo asked
  for is already satisfied (done by earlier work, not by me — just verified it's real and current).
- Everything else already documented in the sibling issue doc (the manifest-swap re-fix).

**Still genuinely outstanding, blocked on this credential issue**: the MDPS `odds_horizon_bucket` reprocess (109,312+
objects, needs the sanctioned `launch-mdps-sports-bucket-vm.sh` launcher, needs fresh tarballs first) and the
`batch_footystats` copy+swap extension (16,970 objects, same launcher family).
