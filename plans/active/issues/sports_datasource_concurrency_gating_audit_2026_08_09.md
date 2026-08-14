---
doc_type: issue
title: Sports data-source concurrency gating audit — per-vendor findings + cross-launcher-type gap fix
summary: >-
  Operator asked whether each sports data-vendor has a Tardis-style concurrency constraint and, if so, whether it's
  guarded. Audit of all 7 live sports vendors (api_football, footystats, understat, transfermarkt, soccer_football_info
  (SFI), open_meteo, odds_api) plus 1 not-yet-live vendor (sportradar, BLOCKED-CREDENTIALS, tracked separately).
  Finding: odds_api already has a Tardis-pattern shared guard (`odds-api-concurrency-guard.sh`, credit-budget-capped
  rather than hard-1 since it has no IP-lock); api_football and open_meteo need no guard (single unified launcher / no
  shared-key contention respectively); footystats, understat, transfermarkt, and SFI each DID have a per-vendor
  rate-limit-driven singleton lock already (footystats/understat/transfermarkt per-key; SFI evidenced by a real
  2026-04-19 10-VM 429-thrash incident) but the lock was scoped to ONE launcher-type's own VM-name prefix only — a
  backfill and a forward-poll for the SAME vendor (same shared key) could run concurrently, each blind to the other,
  structurally the same class of gap Tardis's shared cross-launcher guard was built to close. footystats-forward-poll
  had NO lock at all. Fixed in this commit: widened the singleton-lock filter in 6 files to OR-match every sibling
  launcher-type's VM-name prefix for that vendor (mirroring the pattern api_football's own launcher already used
  internally for its backfill+audit sub-types), and added the missing lock to footystats-forward-poll.sh. Live fleet
  checked 2026-08-09: only 1 mtds-backfill-odds-* VM running (smallchunk12) — the earlier-seen smallchunk9+smallchunk12
  co-running state was within odds-api-concurrency-guard.sh's cap (intentional --allow-parallel sharding), not a
  violation.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags:
  [
    sports,
    concurrency,
    vm-launcher,
    rate-limit,
    odds-api,
    footystats,
    understat,
    transfermarkt,
    soccer-football-info,
    tardis-pattern,
  ]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/archive/issues/odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md,
    /plans/active/issues/sportradar_credential_ask_2026_08_09.md,
  ]
created: 2026-08-09
author: agent (sub-agent, tab-2)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    deployment-service/scripts/vm/odds-api-concurrency-guard.sh,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
source:
  [
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/vm/odds-api-concurrency-guard.sh,
    deployment-service/scripts/vm/launch-sfi-forward-poll.sh:36-40 (2026-04-19 incident reference),
    deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh:46-48 ("~1 req/sec pacing" comment),
    "gcloud compute instances list --filter='name~sports OR name~odds' (central-element-323112, asia-northeast1-c), run
    2026-08-09",
  ]
---

# Sports data-source concurrency gating audit

## What I found

**Per-vendor inventory (all launchers live in `deployment-service/scripts/vm/`):**

| Vendor (source key)          | Constraint evidence                                                                                                                    | Guard before this fix                                                                                                                                                                                                                | Gap found                                                                                                                                                                                                                                                                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `odds_api`                   | Real incident 2026-08-02: 5+ uncoordinated VMs burned a 5M-credit/month key to `-772` remaining                                        | `odds-api-concurrency-guard.sh`, sourced by the one launcher that touches it (`launch-mtds-sports-odds-backfill-vm.sh`), Tardis-pattern fail-closed, cap-N (default 1, `--allow-parallel` raises to `ODDS_API_MAX_CONCURRENT_VMS=5`) | **None** — already correctly built, already the Tardis pattern adapted for a credit-budget model instead of Tardis's hard IP-lock-1                                                                                                                                                                                                   |
| `soccer_football_info` (SFI) | Real incident 2026-04-19: 10 concurrent VMs sharing `soccer-football-info-api-key` thrashed on 429 for ~6h, ~4 successful writes total | 3 separate launcher-types (`sfi-backfill-*`, `sfi-fwd-*`, `features-sfi-progressive-*`), each with its OWN singleton check                                                                                                           | `sfi-fwd-*`'s lock only matched its own prefix — a running `sfi-backfill-*` VM went unseen (asymmetric: backfill's broad `^sfi-` filter DID already catch a running fwd VM, but not vice versa). `features-sfi-progressive-*` reads already-captured GCS parquets, not the live API — correctly out of scope, no change needed there. |
| `footystats`                 | Comment-documented: "per-key rate limits" (`FOOTYSTATS_API_KEY` shared)                                                                | `fs-backfill-*` had its own lock; `footystats-fwd-*` (forward-poll) had **NO lock at all**                                                                                                                                           | Forward-poll could run concurrently with itself or with a backfill against the same key, fully unguarded                                                                                                                                                                                                                              |
| `understat`                  | Comment-documented: AJAX scrape, per-IP rate limit                                                                                     | `us-backfill-*` and `us-forward-poll-*`, each with its own, disjoint singleton check                                                                                                                                                 | Backfill + forward-poll could run concurrently, each blind to the other                                                                                                                                                                                                                                                               |
| `transfermarkt`              | Comment-documented: shared API key, ~1 req/sec pacing, "concurrent VMs thrash without useful throughput"                               | `tm-backfill-*` and `tm-forward-poll-*`, each with its own, disjoint singleton check                                                                                                                                                 | Same gap as understat                                                                                                                                                                                                                                                                                                                 |
| `api_football`               | Daily-quota-aware (`REMAINING_DAILY_QUOTA` self-throttle) + per-minute cap                                                             | ONE launcher (`launch-api-football-backfill-vm.sh`) handles both backfill and forward-poll modes, with ONE singleton lock already covering `(af-backfill-* OR af-audit-*)`                                                           | **None** — this launcher already uses exactly the OR-pattern fix applied to the others below; it was the reference design                                                                                                                                                                                                             |
| `open_meteo`                 | No shared key, weather endpoint "tolerates concurrent reads" (explicit code comment)                                                   | Explicitly documented "**No singleton-lock**"                                                                                                                                                                                        | **None** — correct, deliberate no-guard decision, not an oversight                                                                                                                                                                                                                                                                    |
| `sportradar`                 | N/A — not yet live                                                                                                                     | N/A                                                                                                                                                                                                                                  | Out of scope; tracked separately in `/plans/active/issues/sportradar_credential_ask_2026_08_09.md` (`BLOCKED-CREDENTIALS`, no key provisioned, no launcher exists). When it is onboarded, its launcher should follow the same OR-pattern from day one.                                                                                |

**Root-cause framing**: this is structurally the identical problem Tardis's shared `tardis-concurrency-guard.sh` was
built to close (2026-07-16/20) — a name-pattern-scoped, per-launcher-type singleton check cannot see a DIFFERENT
launcher-type consuming the SAME shared credential. Tardis solved it with a shared library function sourced by every
Tardis-consuming launcher; odds_api solved it the same way for its own (single-launcher, so far) vendor. footystats/
understat/transfermarkt/SFI never got the equivalent because each vendor's backfill and forward-poll launchers were
written independently over time, each with its own copy-pasted "check my own VM-name prefix" singleton block.

**Fix applied (proportionate to the actual gap — a filter widen, not a new shared-library build)**: rather than building
4 new per-vendor shared guard scripts (SFI/footystats/understat/transfermarkt don't need Tardis's or odds_api's
`--allow-parallel`/cap-N sharding support — none of them ever deliberately fan out >1 VM), each launcher's existing
`gcloud compute instances list --filter=...` singleton check was widened to OR-match every sibling launcher-type's
VM-name prefix for that vendor, mirroring the pattern `launch-api-football-backfill-vm.sh` already used internally for
its own backfill+audit sub-types. `--force` still bypasses on every launcher, unchanged.

Files changed (`deployment-service/scripts/vm/`):

- `launch-footystats-backfill-vm.sh` — filter widened `^fs-backfill-` → `(^fs-backfill- OR ^footystats-fwd-)`
- `launch-footystats-forward-poll.sh` — **new** singleton lock added (previously had none); `--force` flag added
- `launch-understat-backfill-vm.sh` — filter widened `^us-backfill-` → `(^us-backfill- OR ^us-forward-poll-)`
- `launch-understat-forward-poll.sh` — filter widened `^us-forward-poll-` → `(^us-forward-poll- OR ^us-backfill-)`
- `launch-transfermarkt-backfill-vm.sh` — filter widened `^tm-backfill-` → `(^tm-backfill- OR ^tm-forward-poll-)`
- `launch-transfermarkt-forward-poll.sh` — filter widened `^tm-forward-poll-` → `(^tm-forward-poll- OR ^tm-backfill-)`
- `launch-sfi-forward-poll.sh` — filter widened `^sfi-fwd-` → `^sfi-` (matches `launch-sfi-backfill-vm.sh`'s
  already-broad prefix; `sfi-backfill-vm.sh` itself needed no change)

All 7 files syntax-checked (`bash -n`) clean.

## Live-fleet check (2026-08-09, central-element-323112, asia-northeast1-c)

```
NAME                                              STATUS   CREATED
af-backfill-20260809-020527                       RUNNING  2026-08-08T18:07:23-07:00
expected-universe-v2-sports-20260809-154408       RUNNING  2026-08-09T08:44:15-07:00
mtds-backfill-odds-smallchunk12-20260809          RUNNING  2026-08-09T08:17:26-07:00
mtds-live-sports-odds-api-trades-20260804-131449  RUNNING  2026-08-04T06:15:32-07:00
```

Only **one** `mtds-backfill-odds-*` VM is currently running (`smallchunk12`). The `smallchunk9` VM referenced in the
task brief has already completed/terminated — it is not a live-state finding. Both `smallchunk9` and `smallchunk12`
co-running earlier today would have been **within** `odds-api-concurrency-guard.sh`'s cap (default cap 1 without
`--allow-parallel`, raised to `ODDS_API_MAX_CONCURRENT_VMS=5` when `--allow-parallel` is passed for deliberate
`split1..split5`-style sharding) — this is the guard's own documented, intentional multi-VM sharding path, not a
violation. No evidence of an ungated concurrent-VM breach in the current live fleet for any vendor.

## Follow-up not fixed here (flagged, not actioned — different problem class)

`mtds-live-sports-odds-api-trades-*` is a continuously-running LIVE VM that also draws against the shared odds-api
credit budget, but its VM name does not match `odds-api-concurrency-guard.sh`'s `^mtds-backfill-odds-` pattern, so its
ongoing consumption is not factored into the guard's "how many more backfill VMs fit under budget" arithmetic. This is a
genuinely different problem (continuous live-trading credit draw vs. concurrent-VM race) from the "N VMs racing each
other" concurrency-gating question this audit was scoped to, and is not a `--allow-parallel`-style sharding conflict —
it's a budget-accounting completeness question best addressed alongside the existing credit-budget tracking work from
the 2026-08-02 incident, not by extending this launcher's own name-pattern filter (a live VM is not a candidate to be
blocked/refused the way another backfill VM is — it must keep running).

- [ ] [DOC] P3. Investigate whether `odds-api-concurrency-guard.sh`'s credit-budget cap math should also account for the
      always-on `mtds-live-sports-odds-api-trades-*` VM's ongoing consumption (or a separate, smaller, documented
      key/budget already covers live vs. backfill separately — confirm which before changing anything). Repo:
      deployment-service.

## Progress Log

- 2026-08-09 (sub-agent): Audited all 7 live sports vendors' launchers for a Tardis-style concurrency constraint. Found
  `odds_api` already correctly guarded (`odds-api-concurrency-guard.sh`, built 2026-08-02 in direct response to a real
  credit-exhaustion incident) and `api_football`/`open_meteo` correctly needing no guard. Found a genuine, evidenced
  (SFI: real 2026-04-19 incident; footystats/understat/transfermarkt: explicit shared-key/rate-limit code comments)
  cross-launcher-type gap in SFI/footystats/understat/transfermarkt's per-vendor singleton locks — each launcher-type
  only checked its own VM-name prefix, so a same-vendor backfill+forward-poll pair could run concurrently unseen by
  either lock (footystats-forward-poll had no lock at all). Fixed via a proportionate filter widen (OR-match every
  sibling prefix) across 7 files, mirroring the pattern `api_football`'s own launcher already used internally. Verified
  current live fleet has no active violation. Filed the live-credit-budget-accounting question (live VM vs. backfill
  cap) as a separate P3 follow-up rather than folding it into this fix.
- **na-eligibility-audit 2026-08-10 (sports tranche)**: RECLASSIFY `assigned_vm: NA` → `planning`. The sole open todo
  ("Investigate whether `odds-api-concurrency-guard.sh`'s credit-budget cap math should also account for the always-on
  `mtds-live-sports-odds-api-trades-*` VM's ongoing consumption") is a single-repo (deployment-service), single-script,
  determinable investigation with a stated done-when ("confirm which before changing anything") — meets the
  worker-determinable-outcome bar, not an open-ended design call. Conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) against every active
  `assigned_vm: planning` doc, the 5 draft `sports_satellite_ao_dispatch_batch{5,9,10,11,12}` docs, and
  `sports_consolidated_closeout_2026_07_19.md`: found several docs referencing `odds-api-concurrency-guard.sh`, but all
  are about the VM-COUNT/launch-race guard (cap=1 concurrent VMs) — a different axis from this todo's CREDIT-BUDGET
  cap-math-vs-live-VM-draw question. `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` has an adjacent but
  distinct open P3 ("make the guard memory-aware") — different axis again (memory headroom, not budget accounting vs.
  the live VM). No doc claims this specific question. Clear to dispatch. `assigned_role: data_engineering` already set;
  `execution_scope` corrected `local-only` → `orchestrator-agent`. Single-todo issue doc — finalize-plan-coverage is
  structurally exempt (`check_finalize_plan_coverage.py` only globs `plans/active/*.md`) and archival on this one todo's
  own done-when is trivial, so no companion finalize doc authored.
- **context-scout 2026-08-14**: populated context_scope (3 entries).
