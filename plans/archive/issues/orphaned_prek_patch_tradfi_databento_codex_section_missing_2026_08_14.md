---
doc_type: issue
title: Orphaned prek patch — tradfi_satellite_ao_dispatch_batch13 checkbox claims a codex section that isn't in the file
status: resolved
assigned_vm: planning
created: "2026-08-14"
author: ui_developer-slot-7
source: [safe-doc-push.sh orphaned-prek-patch detector, 2026-08-14 run]
summary: >-
  An orphaned prek patch pair, surfaced by safe-doc-push.sh's post-run check, would restore a checkbox flip + a "DONE"
  Progress Log claim on tradfi_satellite_ao_dispatch_batch13_2026_08_13.md's Databento billing-health-doc todo — but the
  codex file it claims to have edited carries none of the described content, so applying it blind would fabricate a
  false completion claim.
nature: process
asset_group: tradfi
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [orphaned-prek-patch, safe-doc-push, tradfi-databento]
related: [/plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md]
parent_epic: tradfi_master
resolved_by:
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

While shipping an unrelated doc edit via `scripts/dev/safe-doc-push.sh`, the run exited 9 with two (identical) orphaned
prek patches:

- `/home/ubuntu/.cache/prek/patches/1786739146281-2091562.patch`
- `/home/ubuntu/.cache/prek/patches/1786739151604-2093993.patch`

Both patches target `plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md` and flip its "Add a codified
requirement to /codex/02-data/tradfi-databento-sourcing-ssot.md that Databento billing-health verification must include
one real scoped data-pull, never list_datasets()/warmup() alone" todo to done, with a Progress Log entry attributed to
"slot 10, backend_engineer" claiming a new section was added to `/codex/02-data/tradfi-databento-sourcing-ssot.md`.

`git apply --check` confirms the patch still applies cleanly (the checkbox is still `- [ ]` in the live file — the
plan-side flip never landed). But a `grep -n "must include one real scoped data-pull\|never .list_datasets\|warmup"`
over `/codex/02-data/tradfi-databento-sourcing-ssot.md` returns ZERO hits — the codex doc does NOT carry the section the
patch's own Progress Log entry describes. So blindly `git apply`-ing this patch would restore a checkbox flip + a "DONE"
Progress Log entry describing work that isn't actually present in the target codex file.

## Why it matters

This is either (a) slot 10's codex-file commit landed under a different mechanism/path and only the plan-side flip was
lost (safe to just re-apply the plan patch), or (b) slot 10's whole change was lost/never actually shipped (the codex
file never got the section — applying the patch would fabricate a false "DONE" claim, violating the CLAUDE.md honesty
rule). Cannot tell which from this vantage point without deeper git-log archaeology on the codex file's history around
2026-08-14.

## Recommended decision

- [x] ✅ [DOC] P2. Investigate whether `/codex/02-data/tradfi-databento-sourcing-ssot.md` ever received the
      "Billing-health verification MUST include one real scoped data-pull" section (check `git log -p` / `git log --all`
      across the codex file's history for a 2026-08-14 slot-10 commit that may have been lost the same way, or
      reverted). If found live elsewhere: apply the orphaned plan-patch as-is (the checkbox flip is then honest) and
      delete both patch files. If genuinely never landed: re-do the codex-doc edit for real, THEN apply the plan-patch's
      checkbox flip, then delete both patch files. Do not apply the patch's checkbox+Progress Log claim without one of
      these two resolutions — it would otherwise fabricate a "DONE" entry for work not present in the cited file. (repo:
      unified-trading-pm + codex is a subtree of unified-trading-pm)

      **RESOLVED 2026-08-14 (slot 30).** `git log --all` found commit `1e1883ee6b` ("docs(codex): codify Databento
          billing-health verification requires a real scoped data-pull") and confirmed it IS an ancestor of
          `origin/live-defi-rollout` (it landed under a different mechanism than the orphaned patch pair, hence the patch's
          original blind-`git apply --check` still reading clean at file-time). `codex/02-data/tradfi-databento-sourcing-ssot.md`
          carries the section live today at line 330. Separately, the plan-side checkbox flip the orphaned patch would have
          restored was ALSO already landed independently, via `37b0627acc` ("docs(plans): flip todo 2") +
          `8d67b7323b` ("docs(plans): fix SHA citation for todo 2") — `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s
          todo already reads `[x]` with a Progress Log entry citing the real SHA `unified-trading-pm@1e1883ee6b` (not the
          patch's `<SHA>` placeholder). `git apply --check` against both orphaned patches now fails
          (`patch does not apply`, context mismatch against the already-flipped file) — confirming they are dead, fully
          superseded duplicates, not a real gap. No re-application needed; both patch files deleted
          (`/home/ubuntu/.cache/prek/patches/1786739146281-2091562.patch`,
          `/home/ubuntu/.cache/prek/patches/1786739151604-2093993.patch`). No referrers cite this issue doc — archiving in
          the same commit.
