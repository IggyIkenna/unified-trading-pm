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
`/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` Script-1 fleet monitoring)**: a
THIRD independent hit of the same root gap, this time on `launch-canonical-migration-vm.sh` itself (the launcher already
named in this doc's `_fresh_repos` finding above). Relaunching an OOM-killed shard (`cs7-4d` → `cs7-4d-r2`) surfaced the
warn-only staleness check flagging all 4 of
`market-tick-data-service`/`unified-api-contracts`/`unified-trading-library`/ `deployment-service` as stale — including
`market-tick-data-service`, whose tarball predated a same-day fix (`market-tick-data-service@54817bc1`, the
PROGRESS.json-checkpoint fix, landed 10:27 UTC) by hours. Ran `create-code-tarballs.sh --include <4 repos>` to republish
(no `--force`/dirty-checkout needed this time, tree was clean) — but the relaunch had ALREADY started processing
(~12:17:30 UTC) before the republish finished (~12:19:15 UTC), so this specific VM likely still ran pre-fix code despite
the republish "succeeding" moments too late. Three independent occurrences of this same gap in one day
(features-service, sports-features-purge, canonical-migration), across three different slots/sessions, each discovered
only because someone happened to notice the warning — this is a real, recurring, cross-repo tax, not a one-off. Bumping
the "default to enforce" todo below to P1 on that basis; did not action the enforce-default change itself from this
session (mid a live P0 migration campaign — not the right moment to flip a workspace-wide default that could newly block
other in-flight launches without a chance to verify blast radius first).

**Corroborating finding, 2026-07-28 (slot-4, `defi_satellite_ao_dispatch_batch1_2026_07_25.md` HYPERLIQUID trades
re-run)**: a FOURTH independent hit, this time on `launch-mtds-backfill-vm.sh` (not previously named in this doc) —
launching `mtds-backfill-cefi-hyperliquid-trades-1` warned `market-tick-data-service` and `deployment-service` stale
(manifest sha predated repo HEAD, which included the `@c48096e7` parser fix this task exists to re-run with). Unlike the
3rd finding above, this one was caught and republished
(`create-code-tarballs.sh --include market-tick-data-service deployment-service`) BEFORE the real launch — the dry-run +
real-launch sequence gave a natural checkpoint to read the warning and stop, rather than the warning surfacing
mid-relaunch. Deleted the first (stale-tarball) VM instance before it did any real work and relaunched clean
(`lc_verify_tarball_freshness: all 4 tarball(s) current`). Fourth launcher now confirmed to hit this same silent-`warn`
gap; no new action taken on the default itself (existing P2 todos below already own that).

## Todos

- [ ] [DATA] P2. Land the stashed `_fresh_repos` fix for the `sports-features-purge` category in
      `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (stash:
      `orchestrator-slot-10-sports-features-purge-tarball-freshness-fix-2026-07-27`, `.tabs/10/` worktree) via a normal
      QG + quickmerge cycle once host load is calm — `git stash pop`, verify `bash -n`, ship. Small, already-verified,
      no design work needed.
- [x] ✅ [DATA] P1 (bumped from P2, 2026-07-27T~13:15Z — 3rd independent occurrence same day, see corroborating finding
      above). Consider defaulting `LC_TARBALL_FRESHNESS=enforce` (or auto-rebuilding the affected repo's tarball) as
      part of the quickmerge/promote pipeline for any repo with a VM-based e2e-check skill, so a fresh push is never
      silently invisible to the next VM launch. Scope: `deployment-service/scripts/vm/lib/launcher_common.sh`,
      `create-code-tarballs.sh`, and whichever CI hook (if any) should trigger the rebuild.

      **Resolution (2026-07-27, slot-8): investigated, decided AGAINST a blanket default flip — evidence below,
                                                                                                                                                                                                                                                                                                                                                      follow-up todos filed instead of shipping an unvetted change.** `lc_verify_tarball_freshness()` already has an
                                                                                                                                                                                                                                                                                                                                                      `auto` mode (republish-then-continue, added in the original 2026-07-12 guard) that in principle closes exactly
                                                                                                                                                                                                                                                                                                                                                      this gap without `enforce`'s launch-blocking downside. Tried flipping the shared function's default
                                                                                                                                                                                                                                                                                                                                                      `LC_TARBALL_FRESHNESS:-warn` → `:-auto` in `deployment-service/scripts/vm/lib/launcher_common.sh` and ran the
                                                                                                                                                                                                                                                                                                                                                      full `quality-gates.sh` to measure blast radius before shipping (per the "not the right moment... without a
                                                                                                                                                                                                                                                                                                                                                      chance to verify blast radius first" caution already on this doc). Result: **24 existing unit tests broke**,
                                                                                                                                                                                                                                                                                                                                                      spanning THREE unrelated launcher categories — `TestCanonicalMigrationVmRelaunch` (8),
                                                                                                                                                                                                                                                                                                                                                      `TestCanonicalMigrationStallDetection` (4) and `TestCandleApplyCategory` (4) (all
                                                                                                                                                                                                                                                                                                                                                      `launch-canonical-migration-vm.sh`), plus `TestDefiLaunchersSpotPreemptionContract` (7, the two DeFi backfill
                                                                                                                                                                                                                                                                                                                                                      launchers — confirming the breakage is NOT confined to the two launchers this doc's corroborating findings
                                                                                                                                                                                                                                                                                                                                                      actually implicate). Root cause of the breakage: most of these tests mock `gcloud` for the `compute instances
                                                                                                                                                                                                                                                                                                                                                      create` call but do NOT mock a manifest `commit_sha` matching the real local repo HEAD, so under the OLD
                                                                                                                                                                                                                                                                                                                                                      default (`warn`) the mismatch was silently non-blocking; under `auto` the guard now attempts a REAL
                                                                                                                                                                                                                                                                                                                                                      `create-code-tarballs.sh --include <repo>` subprocess, which has no valid target to tar/upload inside the test
                                                                                                                                                                                                                                                                                                                                                      sandbox and fails, and `auto` mode (correctly) aborts the launch on a failed republish — turning 24 previously-
                                                                                                                                                                                                                                                                                                                                                      green tests into hard failures. **This is real, measured evidence the blast-radius concern was correct**, not
                                                                                                                                                                                                                                                                                                                                                      just caution: even scoping the flip to ONLY the two launchers this doc names (`launch-features-vm.sh`,
                                                                                                                                                                                                                                                                                                                                                      `launch-canonical-migration-vm.sh`) would still break the 16 canonical-migration-vm.sh tests above — closing
                                                                                                                                                                                                                                                                                                                                                      that gap safely needs a companion pass hardening every affected test's `gcloud` mock (return a manifest
                                                                                                                                                                                                                                                                                                                                                      `commit_sha` equal to the real HEAD, or explicitly pin `LC_TARBALL_FRESHNESS=warn`/`off` where the test is
                                                                                                                                                                                                                                                                                                                                                      deliberately exercising unrelated behavior) BEFORE any default changes, which is materially larger than this
                                                                                                                                                                                                                                                                                                                                                      todo's `est_hours: 1.0` scope and touches test suites for launchers this doc doesn't otherwise own. Reverted
                                                                                                                                                                                                                                                                                                                                                      the trial change cleanly (`git checkout --` on both files; tree confirmed clean). Filed two properly-scoped
                                                                                                                                                                                                                                                                                                                                                      follow-ups below instead of leaving this as unactioned prose.

- [x] ✅ [DATA] P1 — features-service@a9429cba. Investigate the remaining `unknown_quote=3` residual on CEFI (post-fix)
      — likely a handful of genuinely non-standard symbols, not a suffix-parsing bug, but not yet confirmed which 3
      instruments or why.

      **Resolution (2026-07-27, slot-14): NOT unmapped/non-standard symbols — a real, fixed bug.** Root cause:
                                                                                                                                                                                                                                                                                                                                      `mvp_universe_filter.py::_extract_base_asset()` matched against the bare fleet-default
                                                                                                                                                                                                                                                                                                                                      `CEFI_ACCEPTED_QUOTE_ASSETS` (USDT/USDC/USD) instead of UAC's venue-aware `accepted_quotes_for_venue()`. UAC
                                                                                                                                                                                                                                                                                                                                      already declares a per-venue quote extension (`_CEFI_VENUE_QUOTE_EXTENSIONS`, `cefi_instrument_universe.py`):
                                                                                                                                                                                                                                                                                                                                      `BITFINEX-FUTURES` → BTC, for Bitfinex's genuine BTC-margined inverse perps. MTDS capture already honours this
                                                                                                                                                                                                                                                                                                                                      extension (`_passes_asset_filter`), but the features-service universe filter did not — so an instrument MTDS
                                                                                                                                                                                                                                                                                                                                      correctly captured was then dropped downstream as `unknown_quote`. The exact 3: `BITFINEX-FUTURES:PERPETUAL:
                                                                                                                                                                                                                                                                                                                                      ETH-BTC@LIN`, `LTC-BTC@LIN`, `XRP-BTC@LIN` (bases ETH/LTC/XRP are all in `CEFI_BASE_ASSET_UNIVERSE`). A 4th
                                                                                                                                                                                                                                                                                                                                      BTC-margined leg in the same Bitfinex family, `XAUTF0:BTCF0` (base XAUT), is NOT part of this residual — XAUT is
                                                                                                                                                                                                                                                                                                                                      not in `CEFI_BASE_ASSET_UNIVERSE`, so MTDS never captures it and it never reaches this filter as a candidate;
                                                                                                                                                                                                                                                                                                                                      confirmed via direct repro that it now correctly excludes via `base_not_in_universe` (not `unknown_quote`) once
                                                                                                                                                                                                                                                                                                                                      the quote gate recognises BTC. Fix: threaded `venue` through `_extract_base_asset` (cached per-venue sorted-quote
                                                                                                                                                                                                                                                                                                                                      lookup via `functools.cache` on `accepted_quotes_for_venue`) at all 4 call sites in `mvp_universe_filter.py`
                                                                                                                                                                                                                                                                                                                                      (base-asset gate, options gate, both `_collapse_to_perp_representative` passes). Verified the `BITFINEX-FUTURES`
                                                                                                                                                                                                                                                                                                                                      extension does NOT leak to `BITFINEX-SPOT` (a genuine ETH/BTC spot cross-pair still correctly excluded). 5 new
                                                                                                                                                                                                                                                                                                                                      regression tests added to `tests/delta_one/unit/test_mvp_universe_filter.py` (venue-aware extraction + leak-check
                                                                                                                                                                                                                                                                                                                                      + the 3-instrument keep + the XAUT non-leak); full suite (51→56 tests) green; `quality-gates.sh` clean on the
                                                                                                                                                                                                                                                                                                                                      shipped commit.

- [ ] [DATA] P2. Harden the `lc_verify_tarball_freshness`-adjacent unit tests in
      `deployment-service/tests/unit/test_vm_launcher_scripts.py` so a future `LC_TARBALL_FRESHNESS` default change is
      actually safe to ship: for every test that invokes a launcher without `--dry-run` and without setting
      `LC_TARBALL_FRESHNESS` explicitly (at minimum `TestCanonicalMigrationVmRelaunch`,
      `TestCanonicalMigrationStallDetection`, `TestCandleApplyCategory`, `TestDefiLaunchersSpotPreemptionContract` — the
      24 identified in the P1 resolution above), either mock a manifest `commit_sha` equal to the real local repo HEAD
      (so the guard reads fresh) or explicitly set `LC_TARBALL_FRESHNESS=off`/`warn` in the test's env (so the test's
      intent doesn't silently depend on today's default). This is a prerequisite for the next todo, not optional
      cleanup.
- [ ] [SCRIPT] P2. **RULED 2026-07-28** (operator general theme applied — no item-specific answer was given, so the
      standing theme governs: "things should recover FULLY if they die or restart... prefer building the full automatic
      recovery, not just a manual runbook note"). **Ruling: (a) — flip `LC_TARBALL_FRESHNESS` default `warn` → `auto` in
      `deployment-service/scripts/vm/lib/launcher_common.sh`, once (and only once) the prior test-hardening todo above
      is FULLY complete** (every affected test in `test_vm_launcher_scripts.py` hardened — not just the 24 named, any
      other test that invokes a launcher without `--dry-run`/an explicit `LC_TARBALL_FRESHNESS` pin — no partial
      hardening pass). Reasoning: `auto` mode is not merely a stricter warning — it actually REPUBLISHES the stale
      tarball and continues the launch, i.e. it is a genuine full self-healing auto-recovery (closing the gap at launch
      time with zero staleness reaching the workload), which is a strictly better fit for the theme's stated preference
      than `enforce` (which only blocks) or option (b) alone (which only prevents the _common_ case — a merge — but
      doesn't help a tarball that goes stale for any other reason, e.g. an infra rebuild lag). **Full-completion scope,
      not MVP**: also close the `_fresh_repos` allowlist gaps this same doc's corroborating findings exposed (the
      `sports-features-purge` category omission — already tracked as its own P2 todo above, land that in the same pass)
      so `auto` mode actually covers every launcher/category combination that can go stale, not just the two this doc
      directly analyzed. **Option (b) (a proactive rebuild-on-merge pipeline hook) is not additionally required** —
      `auto` mode already achieves full staleness self-healing without a second, overlapping piece of infrastructure; if
      `auto` mode's per-launch republish cost ever proves too slow in practice, revisit (b) then as a follow-up, not
      now. **Done when**: the default flip ships with `quality-gates.sh` green (no new regressions beyond the
      already-hardened 24 tests), and a real VM launch against an intentionally-stale tarball is observed
      auto-republishing before the workload starts.

      **Checked 2026-07-31 (slot 12): still genuinely blocked — confirmed against live code, not just this doc's
                  checkbox.** `deployment-service/scripts/vm/lib/launcher_common.sh:672` still defaults
                  `LC_TARBALL_FRESHNESS:-warn` (unflipped). Grepped `tests/unit/test_vm_launcher_scripts.py`'s 4 named classes
                  (`TestCanonicalMigrationVmRelaunch`, `TestCanonicalMigrationStallDetection`,
                  `TestDefiLaunchersSpotPreemptionContract`, `TestCandleApplyCategory`) for `LC_TARBALL_FRESHNESS`/`commit_sha` —
                  zero hits across all 24 tests, confirming the hardening todo above
                  (`features_universe_filter_settlement_suffix_and_vm_tarball_staleness-005`, backlog status `queued`,
                  `dispatched_to: null` as of this check) has NOT landed yet. Flipping the default now would reproduce the exact
                  24-test breakage the P1 resolution above already measured. **Dispatch note**: this doc has no
                  `depends_on`/`sequential` wiring between the two todos (correctly, per CLAUDE.md — the rest of this doc's
                  todos are independent and a whole-doc `sequential: true` would wrongly serialise them too), so the intra-doc
                  "once the prior todo is FULLY complete" gate is prose-only, not structural — the dispatcher offered this
                  SCRIPT todo (`-013`) to slot 12 despite `-005` still sitting unclaimed in queue. Not a backend defect worth its
                  own issue doc (self-contained, low-blast-radius authoring pattern — the answer is "read this note before
                  touching this todo," not a code fix); skipping this dispatch (`reason_code=BLOCKED`) rather than flip the
                  default. Whoever picks up `-005` next should land that first; this todo becomes genuinely actionable
                  immediately after.

              **Re-checked 2026-08-02 (slot-13, review craft): still genuinely blocked, unchanged from slot-12's finding.**
                  `launcher_common.sh:787` still defaults `LC_TARBALL_FRESHNESS:-warn`. Grepped the 4 named test classes
                  (`TestCanonicalMigrationVmRelaunch`, `TestCanonicalMigrationStallDetection`, `TestCandleApplyCategory`,
                  `TestDefiLaunchersSpotPreemptionContract`) for `LC_TARBALL_FRESHNESS`/`commit_sha` individually — zero hits
                  in all 4 (the 8 corpus-wide hits that now exist are pre-existing, scoped to the dedicated
                  `lc_verify_tarball_freshness` unit-test class itself, not the 4 launcher-invoking classes this todo's gate
                  names). `-005` (the hardening todo) confirmed still `status: queued`, `dispatched_to: None` in the live
                  backlog — untouched since slot-12's check. Declining via `/skip-current-task` with `reason_code: "GATED"`
                  (slot-12 used `BLOCKED`; either engages the fleet cooldown/auto-park escalation per
                  `dispatch_cooldown_auto_park_skip_threshold`, `GATED` is the closer semantic match for "waiting on a sibling
                  todo") rather than a plain decline, so a repeat re-dispatch before `-005` lands cools down / eventually
                  auto-parks instead of bouncing to a fresh slot every time.

              **Re-checked 2026-08-02 (slot 15, cicd-role worker): still genuinely blocked, byte-identical to slot-13's
                  finding above.** `launcher_common.sh:787` still defaults `LC_TARBALL_FRESHNESS:-warn`; all 4 named test
                  classes still show 0 hits for `LC_TARBALL_FRESHNESS`/`commit_sha`; live `/api/backlog` confirms `-005` is
                  still `status: queued`, unclaimed. Nothing to add beyond re-confirming no drift. Skipping via
                  `reason_code: "GATED"`, same as the prior check.
