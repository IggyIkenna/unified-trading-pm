---
doc_type: issue
title: >-
  Shared-host `gcloud config set account` clobbers the active identity across ALL concurrent slots — confirmed live
  twice in one session, aborted a real production VM-launch backfill both times
summary: >-
  While running the real production sports historical `expected_unattempted` backfill (7 sequential VM-launching chunks
  over ~an hour+), `gcloud compute instances create` failed twice with `PERMISSION_DENIED` on `compute.instances.create`
  mid-run, even though the launcher script itself never changes the active gcloud account. Root cause:
  `~/.config/gcloud/` is DELIBERATELY shared per-host (not per-slot — explicitly excluded from the per-slot
  on-demand-artifact purge in `/codex/05-infrastructure/per-tab-worktrees.md` § "On-demand artifact pattern", to avoid
  duplicating credentials across slots), so `core/account` is a SINGLE GLOBAL value. Any slot running `gcloud config set
  account <x>` (or a similar tool that mutates the active config) changes it for EVERY slot concurrently using bare
  `gcloud` on the same host — with no locking, no per-invocation account pinning, and no warning. Observed live
  2026-08-04: this session's active account silently flipped between `github-actions-deploy@...`, `github-deploy@...`,
  and `unified-trading-sa@...` at least 4 times across ~2 hours with no action from this session, and twice the
  clobbered identity lacked `compute.instances.create`, aborting an in-progress production backfill (caught cleanly both
  times only because of a same-session fix — see Related — that makes a failed child-launcher call surface its error and
  hard-abort instead of dying silently).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [shared-host, gcloud, identity, multi-agent-safety, vm-launcher, per-tab-worktrees]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-04
author: unknown
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
locked_by:
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh,
  ]
resolved_by:
source: >-
  Discovered as a side-finding while executing
  sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md's job (2) launch-and-verify todo (a
  data_engineering worker, slot 14, 2026-08-04) — the recurring `PERMISSION_DENIED` mid-backfill led to diagnosing the
  shared `~/.config/gcloud` active-account state as the root cause, not a genuine IAM gap.
depends_on: []
---

# Shared-host `gcloud config set account` clobbers the active identity across ALL concurrent slots

## What I found

Mid-run of a real production VM-launching backfill (sequential `gcloud compute instances create` calls spanning well
over an hour), the child launcher failed twice with:

```
ERROR: (gcloud.compute.instances.create) Could not fetch resource:
 - Required 'compute.instances.create' permission for 'projects/.../instances/expected-universe-v2-sports-...'
```

Both times, `gcloud config list` immediately after showed the active `core/account` was NOT the identity this session
had been using moments earlier — it had silently changed to a DIFFERENT service account
(`github-actions-deploy@central-element-323112.iam.gserviceaccount.com` /
`github-deploy@central-element-323112.iam.gserviceaccount.com` observed) that lacks `compute.instances.create`. This
session never ran `gcloud config set account` itself between launches (the child launcher script doesn't touch account
config at all) — the only explanation is a DIFFERENT process on the same shared host (almost certainly a sibling slot
doing its own gcloud work) ran `gcloud config set account ...`, which mutates `~/.config/gcloud/active_config` / the
named config's `core/account` property GLOBALLY, not per-invoking-process.

This matches the documented design in `/codex/05-infrastructure/per-tab-worktrees.md` § "On-demand artifact pattern":
`~/.config/gcloud/` is explicitly listed as one of the paths EXCLUDED from the per-slot on-demand-artifact purge — i.e.
it is deliberately a single shared, per-host location, not duplicated per slot (presumably to avoid re-running
credential setup per slot). That design choice is reasonable for the credential FILES themselves, but `gcloud`'s
`config set` also stores a mutable ACTIVE-SELECTION property in that same shared location, and nothing in the
worktree/multi-agent-safety docs (`per-tab-worktrees.md`'s "Multi-agent safety" sections, `RULES.md`) calls out that
switching the active account is a HOST-WIDE side effect, not a per-session one.

## Why it matters

Any slot that runs `gcloud config set account <x>` for its own legitimate reason (e.g. this session did exactly that,
switching to `unified-trading-sa` after an earlier PERMISSION_DENIED) immediately changes which identity EVERY OTHER
concurrent `gcloud` invocation on the host uses — including invocations already mid-flight in another slot's
backgrounded VM-launcher loop. This is silent (no lock contention error, no warning) and can turn a working long-running
operation into a `PERMISSION_DENIED` failure with zero warning, exactly as observed twice here. It also means the
reverse is true: a fix applied in one session (e.g. correctly diagnosing and switching to the ambient
`unified-trading-sa` identity per RULES.md § 5) does not STAY fixed — any other slot's next `gcloud config set account`
silently undoes it. Left alone, this will keep intermittently breaking any multi-step / long-running `gcloud`-CLI-based
workflow (VM launches, storage operations, IAM lookups) on this shared host whenever two or more slots are doing GCP
work concurrently — which, per the workspace's own concurrency model (multiple slots always running), is the NORMAL
case, not an edge case.

This is NOT a genuine IAM permission gap (RULES.md § 5's "grant the missing role yourself" guidance does not apply —
`unified-trading-sa` already has the needed role; the problem is that a DIFFERENT, less-privileged identity got switched
in from under this session). The mitigation used in-session (re-running
`gcloud config set account unified-trading-sa@...` before each retry) is a workaround, not a fix — it does not prevent
recurrence and is itself exactly the kind of cross-slot-clobbering action that causes the problem for OTHER slots.

## Recommended decision

**round5-cross-cutting-audit 2026-08-08**: no operator decision needed — this workspace has direct precedent for
per-slot isolated config (git-identity pattern, per-tab-worktrees.md); resolution is to implement BOTH options below.

Two independent fix directions, either or both:

- [ ] [INFRA] P2. Stop launcher scripts (and any script invoking `gcloud`) from depending on the ambient/global active
      account at all — pin the identity PER-INVOCATION instead, e.g.
      `gcloud --account=unified-trading-sa@... compute instances create ...` (gcloud supports a per-command
      `--account` flag that overrides the active config without mutating shared state) or
      `CLOUDSDK_CORE_ACCOUNT=unified-trading-sa@...` exported only within the launcher's own subshell. Audit
      `deployment-service/scripts/vm/lib/launcher_common.sh` and the `launch-*.sh` family for any bare `gcloud`
      invocation that relies on ambient `core/account` and pin it explicitly. This removes the dependency on shared
      mutable state entirely rather than just avoiding collisions. (repo: deployment-service)
- [ ] [INFRA] P3. Alternative/complementary: give each slot its own NAMED gcloud configuration
      (`gcloud config configurations create slot-<N>` + `CLOUDSDK_ACTIVE_CONFIG_NAME=slot-<N>` exported in each slot's
      shell profile / boot env) so `gcloud config set account` inside one slot only ever mutates that slot's own named
      configuration, never the shared default. Needs a one-time per-slot bootstrap step (likely `setup-tab-worktrees.sh`
      or the per-slot `.claude/settings.json` env block) and verification that credential FILES (not just the
      active-account pointer) are still shared/reused rather than re-authenticated per slot — the goal is isolating the
      MUTABLE selection, not duplicating the credentials themselves. (repo: unified-trading-pm, touches per-slot
      bootstrap tooling)
- **[DOC] P3. EXTRACTED 2026-08-09 -> `cross_cutting_satellite_ao_dispatch_batch4_2026_08_09.md`.** Document the
  `gcloud config set account` host-wide-mutation hazard in `/codex/05-infrastructure/per-tab-worktrees.md` §
  "Multi-agent safety". See the batch doc for the full scoped todo; do not duplicate-dispatch from here. (repo:
  unified-trading-pm)

## Progress Log

- **data_engineering worker (slot 14) 2026-08-04**: filed while executing
  `sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md` job (2)'s launch-and-verify todo. Worked
  around live by re-running
  `gcloud config set account unified-trading-sa@central-element-323112.iam.gserviceaccount.com` each time the clobber
  was detected (via the launcher's own error-surfacing fix, deployment-service@b64e4a7) and relaunching the (idempotent,
  safe-to-resume) backfill script. Did not implement either fix above — out of this todo's scope, filed here per the
  findings-closure HARD RULE instead of silently working around it forever.
- **data_engineering worker (slot 6) 2026-08-04 — independent second confirmation, different task.** Hit the identical
  failure shape while running `/data-pipeline-check-is --asset-group prediction --day 2026-08-02` (pre-Phase-B baseline,
  `prediction_consolidated_native_ao_extract_2026_07_25.md` todo 2): the POLYMARKET force-leg VM launched fine at
  05:35:56 UTC under `unified-trading-sa`, but the skip-leg launch 26 min later (06:01:24 UTC) failed
  `compute.instances.create PERMISSION_DENIED` — `gcloud config configurations list` at that moment showed the shared
  active config (`slot9-monitor`) pointed at `github-deploy@...`, a different identity than what launched the force-leg
  moments before, with no action taken by this session. Confirms the report is host-wide, not sports-specific or a
  one-off. **Applied fix-direction 2 ad hoc for this session**: created a slot-scoped named config
  (`gcloud config configurations create slot6-work --no-activate` +
  `gcloud config set account unified-trading-sa@... --configuration=slot6-work`) and invoked all subsequent
  `gcloud`/pipeline-check subprocess calls with `CLOUDSDK_ACTIVE_CONFIG_NAME=slot6-work` prefixed per-command —
  confirmed this does NOT touch the shared active config (`gcloud config configurations list` showed `slot9-monitor`
  still `IS_ACTIVE=True` afterward) while correctly scoping my own subprocess to `unified-trading-sa`. This validates
  fix-direction 2 works as designed; it is still a per-session workaround (the named config isn't wired into
  `setup-tab-worktrees.sh`/boot bootstrap), so the P3 todo above stays open. Also verified fix-direction 1's premise
  directly: `unified-trading-sa` genuinely holds `roles/compute.admin` + `roles/compute.instanceAdmin.v1` at the project
  level (confirmed via `gcloud projects get-iam-policy`) — this is conclusively an identity-selection race, never an IAM
  gap, in both independent occurrences now on record.
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — brand-new doc (created 2026-08-04), 3 open `[INFRA]` todos under
  an explicit "Recommended decision" header framing two independent fix directions as an open choice; todo 2 modifies
  per-slot bootstrap tooling inherited by every slot at clone time, todo 1 modifies production VM-launcher scripts —
  both are shared-blast-radius infra changes needing a direction decision first, not worker-determinable alone.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged): todos 1-2 modify
  multi-agent-safety-critical shared bootstrap infra with an undecided architecture choice; todo 3 (document) alone
  doesn't clear the whole-doc bar.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: considered for RECLASSIFY -- today's
  round5-cross-cutting-audit entry on this doc's own "Recommended decision" resolved the prior blocker ("no operator
  decision needed... resolution is to implement BOTH options"), which on its face clears the 2026-08-04/08-06 KEEP-NA
  rationale ("needing a direction decision first"). **Held, not flipped**: this doc's own subject (a shared-host
  `gcloud` active-account race across ALL concurrent AO slots) closely overlaps
  `plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` (already cites this doc in its
  own `context_scope`) -- a related but distinct root cause (GH Actions WIF job auth vs multi-slot
  `gcloud config set account` races) proposing the same class of fix (per-invocation identity pinning / named configs)
  against the SAME shared `~/.config/gcloud` mutable state. Per the conflict-check protocol's caution on
  closely-adjacent claims, staying `assigned_vm: NA` and flagging the overlap rather than guessing which doc should own
  the shared-gcloud-identity fix space.

- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
