---
title:
  staging→main promote PRs recur as pyproject `version =` conflicts — the version line has TWO writer lineages on
  main (gated semver bump vs LDR→main drain); the --rebase promote conflicts whenever the drain lineage wrote last,
  and the reactive drain that fixes it re-seeds the next conflict (treadmill). Structural cure = collapse to one
  writer lineage.
created: 2026-06-22
source:
  - 2026-06-22 first-hand verification (this doc's Appendix A — reproducible git/gh commands + outputs)
  - instruments-service `git log -p pyproject.toml origin/main` (two interleaved version-line authors)
  - agent-orchestrator `git log -p pyproject.toml` main+staging (14 bumps / 20 h; my sync + bumps both wrote the line)
  - fleet version-triple scan main/staging/LDR (23/25 aligned → mechanism is transient, not steady-state)
  - .github/workflows/staging-to-main.yml (promotes via `gh pr merge --rebase`; conflict→conflict-resolution-agent)
  - .github/workflows/staging-conflict-ldr-main-fallback.yml (Class-D LDR→main reactive drain, hourly)
  - .github/workflows/conflict-resolution-agent.yml (dup-`env:` silent outage; fixed PR #490)
  - scripts/workflow-templates/semver-agent.yml.tmpl (bump fires on push:[staging], one commit per bump)
locked_by: live-defi-rollout
parent_epic: infrastructure_master
estimate_class: design
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.5
priority: P1
status: active
supersedes: plans/active/issues/staging_main_version_line_divergence_2026_06_22.md (re-archive on approval — see § Consolidation)
---

## TL;DR

The recurring `staging→main` "version-line conflict" is **real and now verified first-hand** (not relayed). It has
**two distinct problems** that the operator experienced as one "it keeps jamming for days":

1. **The multi-day JAM is already RESOLVED.** It was a compound failure (trigger death + Mode-A/B version-recording
   loss + a **silent outage of the reactive-drain worker**). Every layer is fixed; the fleet is healthy now (23/25
   repos version-aligned across all three branches, all drain workflows green).
2. **The transient FLICKER will keep recurring until a structural cure.** The `version =` line on `main` is written by
   **two commit lineages**; `--rebase` promotion conflicts whenever the non-bump lineage wrote last; the reactive drain
   that fixes it re-writes the line and **seeds the next conflict**. This self-heals (drains are green) but flickers on
   the dashboard. To make conflicts NEVER form, collapse the version line to a single writer lineage — **DECIDED
   2026-06-22: cure B (version-line auto-resolve in the promoter); A ruled out (pyproject `version` must stay real for
   internal-dep resolution).**

This doc is the diagnosis + cure record (doc → plan → code). **Cure B is implemented + shipping** — the merge driver
(`scripts/cicd/semver_max_merge_driver.py`), the promoter-side wrapper (`scripts/cicd/auto_resolve_version_promote.sh`),
and the `staging-to-main.yml` injection — see § "(B) … DECIDED" + § Implementation.

## What I found (verified first-hand)

### The mechanism — dual-lineage writes to a single hot line, replayed by `--rebase`

- semver-agent bumps the version **once per commit** as its own `chore(release): bump version to X` commit, on
  `staging` (it fires on `push:[staging]`). Each bump touches exactly one line: `pyproject.toml` `version =`.
- That line reaches `main` via **two independent lineages**:
  1. **Gated promote** — `staging-to-main.yml` runs `gh pr merge --rebase`, which **replays staging's individual bump
     commits** onto `main` in sequence.
  2. **LDR→main drain** — the Class-D `staging-conflict-ldr-main-fallback.yml` (and Tier-C `LDR → staging` drain
     commits that ride LDR→main) bring LDR's content, **including the version line**, as a merge — i.e. a write to the
     line that is NOT part of the sequential bump chain.
- **The conflict:** a `--rebase` of staging's bump commits applies cleanly only if `main`'s version line is the
  expected base of the oldest pending bump. When the **drain lineage** wrote `main`'s version line last (a value that
  is not that base), the rebase of the bump sequence **conflicts on that one line**.
- **Why it's a treadmill, not a one-off:** the conflict is drained by the Class-D `LDR→main` fallback, which writes the
  version line via the drain lineage **again** → the next gated promote rebases the next bump onto a drain-written line
  → conflicts again. **The cure re-seeds the cause.**

### Evidence (first-hand — full commands in Appendix A)

- **instruments-service `main` pyproject history** shows the two lineages **interleaved** on the version line:
  `semver-agent[bot] chore(release): bump to 0.27.0` immediately followed by
  `uts-ci-poller[bot] feat: LDR → staging (Tier C auto-drain)` **holding the line at 0.27.0**, then
  `semver-agent[bot] bump to 0.28.0`. Two authors, one line. ✅ dual-lineage confirmed.
- **agent-orchestrator** bumped **14× in ~20 h** (0.14.0 → 0.28.0), one commit per bump → the line churns fast, and my
  morning sync commit (`30f0f21`) is itself a third, non-bump writer of the same line. ✅ frequency + multi-writer
  confirmed.
- **Fleet version-triple scan:** 23/25 repos have `version` IDENTICAL across main/staging/LDR right now; only
  agent-orchestrator shows a benign 1-bump lag (main 0.27.0 vs staging/LDR 0.28.0); PM is N/A (Option-B, no staging).
  ✅ the conflict is **transient per-repo** (the bump→align window), not a steady state.

### Jam vs flicker — two different things, do not conflate

- **JAM** = the version-line flickers piled up fleet-wide for *days* because the drain net was broken (below). RESOLVED.
- **FLICKER** = even with a healthy drain net, each new bump-vs-drain window briefly conflicts before draining (up to
  ~90 min on the hourly Class-D). Cosmetic but visible on the Repos CI dashboard; this is what the cure eliminates.

### The compound JAM cause — every layer now fixed

| Layer | What broke | Status |
| ----- | ---------- | ------ |
| Trigger death (2026-06-10) | LDR-trunk decoupling moved v2 off the staging *branch* → semver-agent's `workflow_run` trigger died → promotion machinery went dead fleet-wide | FIXED (`push:[staging]` trigger added) |
| Mode B | Tier-C squash fallback collapsed `feat/fix` into one `chore` commit → no semver bump → version-driven promoter blind | FIXED (`_squash_subject` preserves type, weekend) |
| Mode A | repo→manifest `version-bump` dispatch dropped bumps → promoter blind | FIXED (reconcile-staging-versions cron + backfill) |
| **Drain-net silent outage (the amplifier)** | `conflict-resolution-agent` had a **duplicate `env:` block** (Max-plan-worker cutover regression) → invalid YAML → every dispatch failed with **no failure alert** → transient version-line conflicts never drained → piled up for days | FIXED (PR #490) |

### Current health (verified 2026-06-22)

- 23/25 repos: `version` identical across main/staging/LDR.
- `staging-to-main.yml`, `staging-conflict-ldr-main-fallback.yml`, `conflict-resolution-agent.yml`: **all running
  green** (the agent's `env:` blocks are now one-per-step; recent dispatches succeed).
- Only agent-orchestrator (hyperactive) shows a benign 1-bump lag. **The pipeline self-heals again.**

## Why it matters

- `main` is the **release branch + the Docker image source**. While the version line flickers (and the drain dwells up
  to ~90 min), the dashboard shows "Stuck — triage queue", and a *genuine* (non-version) conflict is harder to spot in
  the noise.
- It is **silent** when healthy (each workflow reports green: "no bump", "squashed", "drained"), so the only signal is
  the lag dashboard — a lagging indicator. The drain-net outage proved a silent break can become a multi-day jam.
- It is **self-reinforcing**: more `main-backmerge` merge commits on LDR → more squash fallbacks (Mode B) and more
  drain-lineage writes (this doc) → the longer it is left, the worse it gets.

## Why the prior analyses were incomplete (reconciliation)

- `staging_to_main_promotion_starvation_2026_06_19.md` correctly found Mode A/B (the promoter was *blind* — "no PR").
  It did **not** cover the conflict mode (PR *exists* but conflicts) that bites once bumps flow again.
- `staging_main_version_line_divergence_2026_06_22.md` (the doc this supersedes) correctly traced the dual-lineage
  version-line conflict, then **closed it as a by-design false-positive ("no action")**. That conclusion is now
  **overridden by the operator** ("fix it properly"), and it **under-weighted the silent-outage amplifier** as the
  reason it was a multi-day jam rather than a managed flicker.
- The weekend agent work (Mode A/B fixes, semver climbing-aware breaker, conflict-resolution-agent PR #490) fixed the
  **JAM**. None of it removes the **dual-lineage** that causes the flicker — that is this doc's open item.

## Recommended decision — the cure (collapse to one writer lineage)

The conflict needs **two** writers of `version =` on `main`. Remove one and it cannot form. Operator picks the approach
(this is a fleet-wide release-flow change → blast radius; a prior audit reached a different conclusion + velocity
matters):

### (B) Version-line auto-resolve in the promoter — **DECIDED 2026-06-22** ("go with B")

The `staging→main` `--rebase` conflict on `version =` is always the same trivial shape (two semvers). **Resolve it
deterministically (higher semver wins)** inside the promoter instead of escalating to the reactive drain.

- *Why auto-resolve, not the "keep-ours / version-neutral drains" variant first floated:* keep-ours would leave `main`
  with the newer **content** but an older `version =` (a lie about what is there — bad for the internal-dep resolution
  we rely on, which is why A is also out). **Auto-resolve keeps the version correct** (always the highest, matching the
  newest content) AND removes the conflict AND retires the second lineage by removing the drain's reason to fire.
- **Removes the conflict at source** → `staging→main` PRs stop recurring as `dirty`; the Class-D drain becomes a rare
  backstop (kept, not deleted).
- Does **not** touch `--rebase` (no BEHIND re-jam regression), no routine force-sync, no `strict`-flag change. **Avoids
  every pitfall the prior audit flagged.**

### (A) Dynamic / tag-based version

Stop committing the bump into `pyproject.toml`; mark `version` `dynamic` and derive it from a git tag; semver-agent
**tags** instead of commit-bumping. **Zero version-bump commits → zero conflict surface** (the cleanest long-term).
Highest blast radius: every repo's build backend + semver-agent + the manifest `versions`/`staging_versions` readers
must move from "read pyproject line" to "read tag".

### (C) Accept the now-healthy reactive equilibrium

The prior stance. Drains self-heal the flicker; treat it as cosmetic. **Now overridden by the operator**, recorded for
completeness.

## Implementation (cure B — DECIDED, operator: "do it end-to-end")

**Verified pre-conditions (first-hand):** semver bumps touch **only** `pyproject.toml`'s `version =` line — never
`uv.lock` (root pkg is editable; confirmed across 5+ recent agent-orchestrator bumps). Resolver scope = one line, one
file.

**Where:** the central `staging-to-main.yml` promoter, at the `mergeable_state == "dirty"` branch (~line 723, the spot
that today dispatches `conflict-resolution-agent`). Inject the auto-resolve **before** the escalation.

**How (deterministic, runner-local, no force-push):**

1. `scripts/cicd/semver_max_merge_driver.py` — a git merge driver (`%O %A %B`): 3-way-merges `pyproject.toml`; for the
   `version =` line takes the **higher semver**; leaves any **other** conflicting hunk as markers + exits non-zero.
2. `scripts/cicd/auto_resolve_version_promote.sh OWNER REPO PR` — clones the repo, wires the driver via
   `.git/info/attributes` (`pyproject.toml merge=semvermax`, runner-local, not committed), then
   `git checkout -B _ar origin/staging && git rebase origin/main`. If the rebase **completes** (only version-line hunks,
   auto-resolved) → push the resolved branch, open a **clean v2-gated PR** to main, arm `--auto --rebase`, close the
   dammed `staging→main` PR as superseded → emit `AUTO_RESOLVED <pr>`. If the rebase hits a **non-version** conflict →
   `git rebase --abort` → emit `GENUINE_CONFLICT files=…`.
3. The promoter: `AUTO_RESOLVED` → count PROMOTED; `GENUINE_CONFLICT` → dispatch `conflict-resolution-agent` exactly as
   today (escalation path unchanged).

**Safety:**

- Kill-switch env `CURE_B_VERSION_AUTORESOLVE` (default `true`) disables the behaviour instantly without a revert.
- **No force-push, no protection bypass** — resolved content lands via a normal v2-gated PR, so `main`'s required check
  still runs; a bad resolve is caught by `quality-gates-v2`.
- **Bounded downside** — only the conflict path changes; genuine conflicts still escalate to `conflict-resolution-agent`.

**Rollout / verify:**

- **Local PoC** proves the driver + rebase + resolve (a synthetic version-only conflict resolves to the higher semver;
  a synthetic non-version conflict still surfaces) before any push.
- Ship to the **central** promoter (one file → fleet-wide; this is NOT a 24-repo template rollout). The escalation
  fallback + kill-switch + v2 gate bound the risk → no per-repo staging; the first live version-line conflict is the
  monitored smoke.
- Verify: a promote cycle with the version line resolving — zero `conflict-resolution-agent` dispatches for
  version-only conflicts; `staging→main` PRs stop recurring `dirty`. Update `codex/08-workflows/ci-cd-flow.md` to record
  the single-writer / version-line-auto-resolve invariant.

## Durability hardening (2026-06-22 #2 — "fix it properly, don't drain the repos every time")

The initial cure-B injection (above) landed at **one** spot — the `mergeable_state == "dirty"` branch of the promoter,
which is reached **only when `gh pr create` no-ops because a staging→main PR already exists**. First-hand re-audit
(2026-06-22, fleet 22/25 behind, T0 `unified-trading-library` head-of-line-blocked) showed the promoter had **two
divergent merge paths and cure B was in only one of them**:

- **New-PR path** (`gh pr create` succeeds → `PR_URL` set): blind-armed `gh pr merge --auto --rebase` and counted the
  repo **PROMOTED without ever reading `mergeable_state`**. So a version-line conflict on a **freshly-created** PR was
  (a) **never auto-resolved on the run it was born** — it had to survive to a *later* run (hours; GitHub throttles the
  `*/15` schedule to ~2 h under load) before the existing-PR branch (and thus cure B) ever saw it; and (b) **falsely
  recorded as promoted** → manifest-vs-reality skew + the per-repo `main…staging` compare re-attempting forever.
- **Existing-PR path**: the only branch that polled `mergeable_state` and ran cure B.

This is *why the drain kept needing a manual kick* even with cure B "shipped": the version conflict was real and the
resolver worked (proven: utl base `0.29.0` / main `0.31.0` / staging `0.35.0` → driver resolves `0.35.0`, exit 0, zero
markers), but the conflict simply **wasn't routed to cure B on the run it appeared**.

**The durable fix (PM@`staging-to-main.yml`):** collapse the two paths into **one unified merge path** —
`gh pr create` (idempotent no-op if open) → resolve the open PR number (new **or** pre-existing) → **poll
`mergeable_state` for both** → `dirty` ⇒ cure B (same-run); anything else ⇒ arm `--auto --rebase`. Net effects:

1. Cure B fires **proactively, same-run**, for **every** conflicting promote — the multi-run / multi-hour latency is
   gone.
2. No more false-positive PROMOTED on a born-dirty PR.
3. A reliable same-run staging→main means the **Class-D `staging-conflict-ldr-main-fallback` (LDR→main) rarely fires**
   → the *other* writer lineage stops re-seeding the conflict (the treadmill's second half shrinks).

Genuine (non-version) conflicts + any resolver error **still escalate** to `conflict-resolution-agent` exactly as before
(AO escalators own those — explicit operator scope 2026-06-22). Kill-switch `CURE_B_VERSION_AUTORESOLVE=false`
unchanged. Validated: `bash -n` clean on all 5 promote run-blocks; YAML parses.

**Remaining lever (documented, not yet shipped — cadence, not correctness):** the `*/15` schedule is GitHub-throttled to
~2 h, so a conflict that forms just after a run is *visible as "behind"* until the next run even though it will
auto-resolve. Tightening this needs an **event-driven trigger** (e.g. `ldr-to-staging-promote` / `semver-agent`
dispatching the promote when it lands content on staging), which the workflow's existing readiness/SIT gates make safe.
Tracked as a follow-up todo; the correctness fix above is independent of it.

## Defense-in-depth (independent of the cure — low-risk, ship-able now)

Neither `conflict-resolution-agent` nor the Class-D fallback alerts on **its own** failure; `promotion-lag-monitor`
only catches the lagging *symptom* (days late). Add a **drain-net workflow-health alert**: page (Slack #ci-failures) if
any of {`staging-to-main`, `staging-conflict-ldr-main-fallback`, `conflict-resolution-agent`, `semver-agent`} is
invalid or its last run concluded `failure`/`action_required`. This makes the silent-outage class (the JAM amplifier)
impossible to miss again. Implementable without the structural cure; recommend shipping regardless of B/A/C.

## Consolidation (housekeeping)

`staging_main_version_line_divergence_2026_06_22.md` was reopened earlier today (PM@300a3073b) with a verified banner.
On approval of this doc, re-archive that one with a `SUPERSEDED → staging_main_version_line_dual_lineage_2026_06_22.md`
banner so there is a **single** record (no dual-tracking, per issue-doc-lifecycle). The earlier reopen-push can be
reverted if the operator prefers it stay archived.

## Related

- `plans/active/issues/staging_to_main_promotion_starvation_2026_06_19.md` (Mode A/B — promoter-blind starvation)
- `plans/active/issues/staging_main_version_line_divergence_2026_06_22.md` (prior false-positive; superseded by this)
- `codex/08-workflows/ci-cd-flow.md` (§ "LDR is the SSOT", § promotion / `--rebase`)
- CLAUDE.md § "LDR is the SSOT", § "v2-never-reported deadlock", § semver-agent dispatch SPOF

## Appendix A — Verification evidence (reproducible)

```bash
# 1. Dual-lineage on the version line (two authors, interleaved) — instruments-service main
git -C <repo> log -16 --format='%h|%an|%s' origin/main -- pyproject.toml
#   semver-agent[bot]  chore(release): bump version to 0.28.0   (v=0.28.0)
#   uts-ci-poller[bot] feat: LDR → staging (Tier C auto-drain)  (v=0.27.0)  <-- drain lineage writes the line
#   semver-agent[bot]  chore(release): bump version to 0.27.0   (v=0.27.0)

# 2. Bump frequency / multi-writer — agent-orchestrator: 14 bumps in ~20 h; my sync commit 30f0f21 also wrote the line
git -C <repo> log -12 --format='%h|%ci|%an|%s' origin/main -- pyproject.toml

# 3. Fleet version-triple — 23/25 aligned (transient, not steady-state)
for b in main staging live-defi-rollout; do gh api .../contents/pyproject.toml?ref=$b ... | grep '^version'; done

# 4. Drain-net health (all green now; conflict-resolution-agent env: one-per-step)
gh run list --workflow staging-to-main.yml ...                 # green
gh run list --workflow staging-conflict-ldr-main-fallback.yml  # green
gh run list --workflow conflict-resolution-agent.yml           # workflow_dispatch success after PR #490
```
