---
title: "CI-status side store — move ci_status from the git manifest to Firestore (doc-per-repo + CAS-on-rank)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
created: 2026-06-10
source:
  - operator design direction 2026-06-10 ("ci_status commit noise — what's a side store + how are races handled")
  - inspection 2026-06-10: ~57% of an 80-commit PM-LDR window was bot/CI churn; `ci: update ci_status …[skip ci]`
    was the single biggest class (21/80), each a commit per repo per CI-status transition.
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# CI-status side store — Firestore doc-per-repo, CAS-on-rank

## Problem

`ci_status` currently lives **inside `workspace-manifest.json`, committed to PM git**. Each repo's every CI lifecycle
transition (`FEATURE_GREEN → STAGING_GREEN → SIT_VALIDATED → MAIN_GREEN`, or `FAILING`) fires a `repository_dispatch`
`ci-status-update` → `.github/workflows/ci-status-update.yml` → a `ci: update ci_status for <repo> (<status>) [skip ci]`
commit to PM `live-defi-rollout`. Two costs:

1. **Commit noise** — one commit per transition per repo across 25 repos; during an active drain (e.g. 13 repos →
   `MAIN_GREEN`) this is a burst that floods every `git pull` and the PM log.
2. **A write-contention race by construction** — all 25 repos write the SAME file in the SAME repo, so concurrent
   updates contend on one git ref → push races → `[skip ci]` retry churn in the bot, and occasional lost/over-written
   updates (the reconciler `ci-status-reconciler.yml` exists to paper over this).

The lifecycle ranking + no-downgrade guard already exist (`ci-status-update.yml:94`: `MAIN_GREEN`=4 can't be knocked to
`STAGING_GREEN`=2 by a later green-staging; `FAILING` is never suppressed). We keep that semantics — only the STORAGE

- CONCURRENCY model changes.

## Approved design (operator 2026-06-10)

**Store: Firestore, one document per repo** — collection `ci_status`, document id `{repo}`:

```
ci_status/{repo} = {
  status:     "MAIN_GREEN" | "SIT_VALIDATED" | "STAGING_GREEN" | "FEATURE_GREEN" | "FAILING",
  rank:       4 | 3 | 2 | 1 | 0,        # the existing lifecycle rank (FAILING ranks specially — see CAS)
  branch:     "main" | "staging" | "live-defi-rollout",
  sha:        "<head sha>",
  updated_at: <server timestamp>,
}
```

Already proven in this stack — the promote path uses Firestore (`MinimalCandidateManifest`), `get_*_client` cloud
facades exist, and a collection query is a single read for the whole-fleet aggregate.

### Race handling — two layers (approved)

**Layer 1 — cross-repo races eliminated by PARTITIONING, not locking.** The entire problem is 25 writers sharing one
record. Per-repo document id ⇒ two repos updating concurrently touch DISJOINT docs ⇒ **zero contention, by design** (no
retries, no push wars). Same principle as the per-VM manifest shards (`MANIFEST_PER_VM_SHARDS`) — partition the write
surface, consolidate on read.

**Layer 2 — same-repo ordering** (one repo firing `STAGING_GREEN` then `MAIN_GREEN` ms apart, possibly out of order) via
a **Firestore transaction (compare-and-set)**:

- write iff `new_rank > stored_rank`, OR (`new.branch == stored.branch` AND `new.updated_at > stored.updated_at`);
- **`FAILING` is written UNCONDITIONALLY** (a genuine failure must never be suppressed by the no-downgrade rule — same
  carve-out as today);
- result: "**highest-rank / newest wins**" — a delayed `STAGING_GREEN` can't clobber a real `MAIN_GREEN`, and a real
  failure always lands. (GCS equivalent if we ever swap stores: `ifGenerationMatch` precondition; Firestore txn is
  cleaner.)

### Reads

Consumers query the `ci_status` collection (one read → aggregate) instead of `git pull` + parse manifest. They see
current truth instantly, with no contention and no waiting for a manifest commit to reach `origin/main`.

### Git keeps an OPTIONAL low-frequency snapshot

A consolidator writes the aggregate back into `workspace-manifest.json.ci_status` on a cadence (e.g. every 15 min or
on-demand) for human-readability + offline fallback — **one commit per interval, not per transition**. This is the
manifest-consolidator pattern (Cloud Run Job + Scheduler) applied to ci_status. The LIVE source of truth is Firestore;
the git copy is a cache.

## Phased execution (safe migration of a LIVE system — dual-write first, never a flag-day)

### Phase 1 — Firestore writer + the CAS (P2)

- [x] ✅ [CODE] P2. DONE 2026-06-10 — `scripts/cicd/ci_status_store.py` (`resolve_status` pure CAS decision +
      `set_status` Firestore txn + `get_all`); 10 unit tests green
      (rank/no-downgrade/FAILING-unconditional/main-authoritative), ruff + basedpyright clean. Was:
      `set_status(repo, status, branch, sha)` doing the Layer-2 CAS in a Firestore transaction (rank map + the
      `FAILING`-unconditional carve-out), and `get_all() -> dict[repo,...]` for readers. Cloud-agnostic via
      `get_firestore_client()`; unit-tested (mock Firestore) incl. the out-of-order + `FAILING` cases.
- [x] ✅ [CI] P2. DONE 2026-06-10 — `ci-status-update.yml` dual-write wired (gated behind
      `vars.CI_STATUS_FIRESTORE_DUALWRITE`, `continue-on-error` so it can never redden the run / block the git commit;
      mirrors the persist-cicd-event GCP-auth pattern). Was: `ci-status-update.yml` (+ the `Recording ci_status` step
      the reusable `python-quality-gates-v2.yml` dispatches) **DUAL-WRITE**: keep the existing git commit AND call
      `ci_status_store.set_status(...)`. No reader change yet — pure additive, lets us validate Firestore mirrors git
      before cutover.
- [ ] [VERIFY] P2. Run a drain / a few transitions; assert the Firestore docs match the manifest `ci_status` (rank +
      no-downgrade behaviour identical). Confirm concurrent multi-repo transitions produce NO contention (vs the git
      push-retries today).

### Phase 2 — migrate readers to Firestore (P2) — the inventory (verified 2026-06-10)

> **[CONFLICT-GUARD 2026-06-10 — operator-ratified, SAFETY-CRITICAL SEQUENCING]**: the manifest dual-write must OUTLIVE
> the LAST manifest reader. Known manifest ci_status readers that must each cut over to Firestore (or be verified
> non-blocking) BEFORE the manifest write stops: (1) quickmerge STAGE 1.7 dep-tier gate (reads repositories{}.ci_status
> from PM origin/main — gated EVERY fleet promotion on it today); (2) ldr-to-staging-promote.yml +
> ldr-to-main-promote.yml; (3) cascade-qg-ordering.yml's per-level ci_status poll; (4) sit-debounce-trigger.yml.
> Premature write-cutover makes the dep-order gate read stale/absent → blocks all ships or waves them through ungated.
> NOTE this side-store is also the structural fix for the manifest-update concurrency-group contention that the DEFECT-2
> resolve-gate's ≤5-min group hold worsens (dependency_promotion plan, item 9 tension) — sequencing matters doubly.

Cut each reader from "parse `workspace-manifest.json.ci_status`" to `ci_status_store.get_all()`:

- [ ] [CI] P2. `.github/workflows/sit-gate.yml` (the `rank >= STAGING_GREEN` gate — the cascade-convergence reader).
- [ ] [CI] P2. `.github/workflows/staging-to-main.yml` + `ldr-to-staging-promote.yml` (promotion gates).
- [ ] [CI] P2. `.github/workflows/cascade-qg-ordering.yml` + `update-repo-version.yml` + `auto-merge-minor-fixes.yml`.
- [ ] [CI] P2. `.github/workflows/staging-backmerge-to-ldr.yml` + `main-backmerge-to-ldr.yml` + `ldr-ci-monitor.yml`.
- [ ] [SCRIPT] P2. `scripts/quickmerge.sh` (STAGE lock/status read) + `scripts/tier-gate-check.sh` +
      `scripts/cicd/check_ci_status_bot_only.py` + `scripts/cascade/invalidate-ci-status.py`.
- [ ] [CODE] P2. The orchestrator dashboard / `server/` read path (the authoritative work-split surface) → collection
      query.
- [ ] [SCRIPT] P3. `scripts/manifest/_align_workspace_manifest.py` + `generate_workspace_dag.py` → read the snapshot
      (Phase 3) or the store; these are tooling, lower urgency.

### Phase 3 — snapshot consolidator + retire the per-transition commit (P2)

- [ ] [CODE] P2. A consolidator (Cloud Run Job + Scheduler, reuse the manifest-consolidator infra) writes the Firestore
      aggregate → `workspace-manifest.json.ci_status` on a cadence / on-demand — ONE commit per interval.
- [ ] [CI] P2. Drop the git-commit half of the `ci-status-update.yml` dual-write (Firestore-only writes). The
      `ci: update ci_status …[skip ci]` per-transition commit class is GONE; `ci-status-reconciler.yml` (the
      race-papering reconciler) is retired — the CAS makes it unnecessary.

### Phase 4 — verify + clean up (P2)

- [ ] [VERIFY] P2. A full drain produces ZERO `ci: update ci_status` commits; the cascade/promotion gates behave
      identically (read from Firestore); the dashboard is live. Confirm the PM-LDR commit volume drops by the measured
      ci_status share.
- [ ] [DOCS] P2. Codex SSOT updates (below) + CLAUDE.md one-liner (ci_status is Firestore-backed; manifest copy is a
      snapshot cache, not the source of truth).

## Success criteria

- No per-transition `ci_status` commit to git (only the optional periodic snapshot).
- Concurrent multi-repo transitions: zero write contention (per-repo docs), no reconciler needed.
- Same-repo ordering correct under the CAS (no-downgrade preserved; `FAILING` never suppressed) — proven by unit tests +
  a live drain.
- Every reader (the ~15 above) reads Firestore (or the snapshot) and the cascade/promotion logic is unchanged in
  behaviour.

## Codex SSOT updates

`codex/08-workflows/ci-cd-flow.md` (ci_status is a Firestore side store, doc-per-repo + CAS-on-rank; manifest copy is a
snapshot), `codex/04-architecture/agent-orchestrator-overview.md` (dashboard reads the store),
`codex/05-infrastructure/manifest-consolidator-ssot.md` (the snapshot consolidator reuses this infra). CLAUDE.md § "CI
Verification" / "ci_status" pointer.

## Out of scope (named successors)

- Deriving ci_status purely on-read from GitHub's checks API (no store at all) — rejected for now (rate limits + the
  custom lifecycle ranking); revisit only if Firestore cost/latency ever becomes an issue.
