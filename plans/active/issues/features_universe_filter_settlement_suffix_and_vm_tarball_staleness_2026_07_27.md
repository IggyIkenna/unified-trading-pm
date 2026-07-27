---
doc_type: issue
title:
  "features-service MVP universe filter dropped every CeFi perpetual (unstripped @LIN/@INV suffix) + VM code-tarball
  staleness gap"
summary:
  Two independent findings from running /data-pipeline-check-features against CEFI:delta_one. (1) mvp_universe_filter.py
  never stripped the canonical @LIN/@INV settlement suffix, so the quote-suffix match failed for every real CeFi
  perpetual/future — universe_filter retained 0/588 instruments, silently zeroing out CEFI feature computation. Fixed +
  shipped. (2) VMs deploy from a pre-built code tarball that is NOT rebuilt on every push — a VM launched minutes after
  the fix landed still ran the pre-fix code because the tarball was 5+ hours stale. Manually rebuilt; the propagation
  gap itself remains open as a workspace-wide risk.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [universe-filter, canonical-id, vm-tarball, deployment-propagation, data-correctness]
related: [data_pipeline_check_mdps_features_2026_07_20]
created: 2026-07-27
priority: P0
parent_epic: infrastructure_master
source: "/data-pipeline-check-features driver run against CEFI:delta_one, 2026-07-27 (slot-3)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# features-service universe filter + VM tarball staleness (2026-07-27)

## Finding 1 — universe filter dropped every real CeFi instrument (FIXED, shipped)

`features_service/delta_one/universe/mvp_universe_filter.py::_extract_base_asset()` matched a symbol against a set of
known bare quote suffixes (`USDT`, `USD`, ...) to derive the base asset. It never accounted for the canonical
`BASE-QUOTE@LIN|@INV[-YYYYMMDD]` shape that `build_instrument_id()` actually produces for CeFi perpetuals/futures — the
`@LIN`/`@INV` segment (and any trailing expiry) was left attached, so the suffix match always failed for these
instruments.

Measured impact (real run, CEFI:delta_one, day-window 2026-07-19..2026-07-20, pre-fix):

```
universe_filter [technical_indicators]: retained 0/588; excluded 588 (base_not_in_universe=199, unknown_quote=389)
```

389/588 candidates — every perpetual/future carrying the canonical settlement suffix — were misclassified as
`unknown_quote` and dropped. Since `delta_one`'s filter is shared across feature groups, this zeroed out ALL 18 feature
groups for CEFI on every run (the pre-fix VM run failed all 18 groups: `ALL feature groups failed`).

**Fix**: strip everything from the first `@` onward before the quote-suffix match. Shipped `features-service@02155a55`
with 4 new regression tests (`BASE-QUOTE@LIN`, `@INV`, `@LIN-{expiry}`, venue-prefixed form).

**Proved live** on VM `features-e2e-cefi-20260727-063401-025349` (force-leg, same day-window, fresh code):

```
universe_filter [technical_indicators]: retained 552/588; excluded 36 (base_not_in_universe=33, unknown_quote=3)
```

`unknown_quote` dropped from 389 → 3 (an acceptable residual — likely genuinely unmapped quote assets, not a suffix
bug). This is the fix's live-fire proof.

## Finding 2 — VM code tarball is not rebuilt on push (propagation gap, NOT fixed at the root — worked around this session)

`deployment-service/scripts/vm/launch-features-vm.sh` deploys a pre-built tarball from
`gs://deployment-scripts-{project}/code/features-service-code.tar.gz` (`create-code-tarballs.sh`), not a live git
checkout. There is no CI hook that rebuilds this tarball on every push to `live-defi-rollout` — it is rebuilt on some
other cadence (manually, or a schedule not tied to individual pushes).

**Measured**: the tarball's own manifest (`features-service-code.manifest.json`) showed `commit_sha: 568c56303d...`,
`created_at: 2026-07-27T01:29:26Z` — over 5 hours before the `02155a55` fix landed (~06:18 UTC). A VM launched at
06:17-06:21 UTC to validate the fix ran the STALE pre-fix code and reproduced the exact same `retained 0/588` failure,
which read (at first) as "the fix doesn't work" — it was actually "the VM never ran the fix."

`lc_verify_tarball_freshness()` (`deployment-service/scripts/vm/lib/launcher_common.sh:662`) exists and runs on every
launch, but defaults to `LC_TARBALL_FRESHNESS=warn` — it does not block a launch on a stale tarball, it only logs a
warning (which is easy to miss in a driver's captured stdout).

**Workaround applied this session**: manually ran
`bash scripts/vm/create-code-tarballs.sh --include features-service --force` (from a local clone with the fix already
checked out) to rebuild + upload a fresh tarball (`commit_sha: 36e274ac...`, an ancestor-inclusive descendant of
`02155a55`). Confirmed via the manifest and the second VM run's live `retained 552/588` result.

**Not fixed at the root**: this propagation gap affects EVERY VM-based fix-validation cycle in this workspace, not just
features-service — any code fix shipped to LDR is invisible to a freshly-launched VM until its tarball is separately
rebuilt. `LC_TARBALL_FRESHNESS=enforce` would turn the existing (currently silent) staleness check into a hard abort,
which would at least fail loud instead of silently running stale code — worth considering as the default, or wiring an
automatic tarball rebuild into the quickmerge/promote pipeline for repos with VM-based test harnesses.

**Corroborating finding, 2026-07-27T10:15Z (slot-10, Track F follow-up,
`sports_consolidated_native_ao_extract_2026_07_25.md`)**: a DIFFERENT, more specific bug in the SAME freshness-check
mechanism. `launch-canonical-migration-vm.sh`'s `_fresh_repos` array (line ~1301) is a per-category allowlist of which
repos `lc_verify_tarball_freshness()` even checks — it defaults to
`(market-tick-data-service unified-api-contracts unified-trading-library deployment-service)` with a few
category-specific overrides (`tradfi-catalogue-canon`, `*-candle-census`, etc.), but had **no override for
`sports-features-purge`** — so the check never looked at `features-service` at all for that category, even though the
category's whole job is running a features-service script. Silently launched a VM against a tarball that predated the
just-shipped purge script by minutes → `rc=2 No such file or directory` on first launch (not even a `warn`-level
message, since the repo was never in the checked list to begin with). Fixed by adding a `sports-features-purge` →
`(features-service unified-api-contracts unified-trading-library deployment-service)` override, verified `bash -n`
clean; **fix is currently STASHED, not yet landed** (`git stash` entry
`orchestrator-slot-10-sports-features-purge-tarball-freshness-fix-2026-07-27` in the deployment-service worktree at
`.tabs/10/`) — deployment-service's own QG died twice under a separate, unrelated fleet-wide CPU-contention spike (load
avg hit 39) while trying to land it, so it was parked (not lost) rather than force a QG run that couldn't be trusted.
Unblocked the actual VM relaunch in the meantime via `create-code-tarballs.sh --allow-dirty-tarball` (the documented
emergency-hotfix escape hatch), which worked correctly since the fix only needs to be present in the LOCAL checkout
invoking the launcher, not committed.

**Corroborating finding, 2026-07-27T~13:15Z (interactive session,
`cefi_migration_cutover_and_track8_completion_2026_07_25.md` Script-1 fleet monitoring)**: a THIRD independent hit of
the same root gap, this time on `launch-canonical-migration-vm.sh` itself (the launcher already named in this doc's
`_fresh_repos` finding above). Relaunching an OOM-killed shard (`cs7-4d` → `cs7-4d-r2`) surfaced the warn-only staleness
check flagging all 4 of `market-tick-data-service`/`unified-api-contracts`/`unified-trading-library`/
`deployment-service` as stale — including `market-tick-data-service`, whose tarball predated a same-day fix
(`market-tick-data-service@54817bc1`, the PROGRESS.json-checkpoint fix, landed 10:27 UTC) by hours. Ran
`create-code-tarballs.sh --include <4 repos>` to republish (no `--force`/dirty-checkout needed this time, tree was
clean) — but the relaunch had ALREADY started processing (~12:17:30 UTC) before the republish finished (~12:19:15 UTC),
so this specific VM likely still ran pre-fix code despite the republish "succeeding" moments too late. Three independent
occurrences of this same gap in one day (features-service, sports-features-purge, canonical-migration), across three
different slots/sessions, each discovered only because someone happened to notice the warning — this is a real,
recurring, cross-repo tax, not a one-off. Bumping the "default to enforce" todo below to P1 on that basis; did not
action the enforce-default change itself from this session (mid a live P0 migration campaign — not the right moment to
flip a workspace-wide default that could newly block other in-flight launches without a chance to verify blast radius
first).

## Todos

- [ ] [DATA] P2. Land the stashed `_fresh_repos` fix for the `sports-features-purge` category in
      `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (stash:
      `orchestrator-slot-10-sports-features-purge-tarball-freshness-fix-2026-07-27`, `.tabs/10/` worktree) via a normal
      QG + quickmerge cycle once host load is calm — `git stash pop`, verify `bash -n`, ship. Small, already-verified,
      no design work needed.
- [ ] [DATA] P1 (bumped from P2, 2026-07-27T~13:15Z — 3rd independent occurrence same day, see corroborating finding
      above). Consider defaulting `LC_TARBALL_FRESHNESS=enforce` (or auto-rebuilding the affected repo's tarball) as
      part of the quickmerge/promote pipeline for any repo with a VM-based e2e-check skill, so a fresh push is never
      silently invisible to the next VM launch. Scope: `deployment-service/scripts/vm/lib/launcher_common.sh`,
      `create-code-tarballs.sh`, and whichever CI hook (if any) should trigger the rebuild.
- [ ] [DATA] P1. Investigate the remaining `unknown_quote=3` residual on CEFI (post-fix) — likely a handful of genuinely
      non-standard symbols, not a suffix-parsing bug, but not yet confirmed which 3 instruments or why.
