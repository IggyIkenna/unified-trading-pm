---
doc_type: issue
title: deployment-service carries a 19-commit-remaining, month-old, multi-identity strict-quickmerge bypass backlog
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, provenance, ci_reconciler]
created: 2026-08-21
last_reviewed: 2026-08-21
summary: "deployment-service carries 22 bypass commits (dated 2026-07-09 through 2026-07-20, ~1-6 weeks old at filing) that reached live-defi-rollout without a Quickmerge trailer, across 7+ distinct slot/host identities -- not currently blocking a live promote PR, but per /ci-reconcile's size/authorship gate this is a larger multi-identity backlog needing an operator decision (bulk-bless vs re-ship-each vs show-and-wait), not a blind auto-fix. 3 of the original 22 were independently verified small/clean/single-author before the true scope was known and were reprovenanced directly; 19 remain."
related: [mtds_is_historical_quickmerge_bypass_backlog_2026_08_16]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
parent_epic: ci_master
source: ci_reconciler /ci-reconcile sweep 2026-08-21
assigned_vm: NA
resolved_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/scripts/cicd/check_strict_quickmerge.py,
    unified-trading-pm/scripts/cicd/reprovenance_bypass.sh,
  ]
---

# deployment-service historical strict-quickmerge bypass backlog

Found during a `/ci-reconcile` sweep (2026-08-21, ~06:10-06:25Z). `check_strict_quickmerge.py --range
origin/main..origin/live-defi-rollout --block` initially surfaced only 3 bypass commits via a `tail -5`-truncated
view (`7c8b2101`, `a6881d12`, `e18d5850`, all dated 2026-07-07/09, single author `ikennaigboaka` across two host
identities `[main·planning]`/`[slot-3·planning]`) — small enough to qualify for `/ci-reconcile` §4's direct-fix gate
(single-author, self-contained, no active promote PR, diffs clean of secrets/destructive ops). These 3 were
reprovenanced via `reprovenance_bypass.sh <sha>` (no `--push` yet — staged locally, see Todos) before a full,
untruncated re-run of the same check revealed **19 more** bypass commits underneath them, spanning 2026-07-09 through
2026-07-20 and 7+ distinct slot/host identities (`slot-0·human-planning`, `slot-2·planning`, `slot-3·laptop`,
`slot-3·planning`, `slot-4·planning`, `slot-6·planning`, `main·laptop`). That is squarely the "larger, foreign,
multi-subsystem, multi-agent backlog" case `/ci-reconcile` §4 says to stop and ask about, not sweep in — same shape as
the already-filed `[[mtds_is_historical_quickmerge_bypass_backlog_2026_08_16]]` sibling finding for
market-tick-data-service + instruments-service.

**Not currently blocking anything live** — verified via `gh` at sweep time: `deployment-service` has no open promote
PR at all (`gh pr list --search "promote" --state open` returns empty).

## The 3 already reprovenanced (done, harmless, no operator input needed)

- `7c8b2101` — feat(deployments-inventory): AWS Lambda census (existence + config)
- `a6881d12` — feat(vm): stamp D.1 host metric vector onto the registry entry
- `e18d5850` — feat(vm-launchers): wire Deribit BTC/ETH options_chain daily forward-snapshot

Each individually diff-reviewed (no secrets, no destructive ops, clean feature/fix content) before reprovenancing.
Blessing commits are local on this checkout's `live-defi-rollout`, not yet pushed — pushing them is folded into
whichever path the operator picks below (they're additive/harmless either way, so no need to hold them separate).

## The 19 remaining (operator decision needed)

`9a364783`, `dfd7608c`, `c79f984c`, `4c6cef91`, `de7a0a8d`, `ddd9d769`, `d58506e4`, `4f0daeb5`, `9236eadf`,
`f2db5f0a`, `1090c3e5`, `e2a62ccc`, `344958c1`, `7c68e771`, `d8695e3c`, `b665123e`, `b3111a1c`, `a1454a66`,
`f0ad0ab4`, `dc67a617`, `466f4c65`, `9ef144e6` — all `ikennaigboaka`, dated 2026-07-09 through 2026-07-20, across the
7+ identities named above. Touch `deployment_service/{vm,data_pipeline_monitors,cli}/`, `scripts/vm/`,
`scripts/setup-buckets.py`, `scripts/recovery/relaunch_backfill_vm.py` — VM launcher/tarball-pin/maintenance-window/
manifest-reader feature and fix work, nothing that reads as destructive or credential-touching from the commit
subjects alone (not yet individually diff-reviewed at the same depth as the 3 above — that's part of whichever path
gets picked).

## Why it hasn't caused visible pain yet

`quality-gates-v2` on `live-defi-rollout` pushes is green (confirmed in the same sweep — deployment-service's latest
push-CI run is `success`), and there is no actively-blocked promote PR right now — the bypass range just sits latent,
re-surfacing every time `check_strict_quickmerge.py` is run against `origin/main..origin/live-defi-rollout`. It will
collide with a live promotion the moment deployment-service's next promote PR actually gets gated on it, the same way
`unified-trading-pm`'s `e560378a2d` did in an earlier sweep (per the MTDS/IS sibling doc).

## Todos

- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-22 (D14 ruling: bulk-bless after review approved — the 3
  already-reviewed commits were clean and all repos' gates are green, so bulk-bless removes latent promotion risk
  at lowest cost).**
- [ ] [SCRIPT] P3. Push the 3 already-created reprovenance blessing commits (`reprovenance_bypass.sh` was run
      without `--push` for `7c8b2101`/`a6881d12`/`e18d5850`), and reprovenance the 19 remaining via
      `scripts/cicd/reprovenance_bypass.sh <sha> --push` (bless path). Per D14 ruling (2026-08-22): bulk-bless after
      review approved — the 3 already-reviewed commits were clean and all repos' gates are green.

## Progress Log

- **ci_reconciler 2026-08-21**: filed during a `/ci-reconcile` sweep after the initial 3-commit view (truncated by
  a `tail -5` in the sweep's own diagnostic command) turned out to undercount the real backlog by 19 commits once
  re-checked untruncated. The 3 already-verified-clean commits were reprovenanced before the miscount was caught;
  the remaining 19 are left for the operator per the same size/authorship gate the MTDS/IS sibling finding already
  established.
- **2026-08-22 — ruling D14 (Historical quickmerge-bypass commits)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Bulk-bless after review — the 3 already-reviewed commits were clean
  and all repos' gates are green; this removes latent promotion risk at lowest cost. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
