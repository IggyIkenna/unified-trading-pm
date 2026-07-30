---
doc_type: issue
title:
  ManifestWriter per-VM-shard follow-ups — VM-launcher audit + library-level fix, split out at archive time from the
  resolved OOM incident
summary: >-
  `per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md` (the sports FIXTURES backfill OOM incident) is resolved
  and verified live 2026-07-28 (`deployment-service@20ce4c9`, per-chunk `VM_NAME` suffix), so it is archiving per the
  terminal-status-archived rule. Two follow-ups from its own "What's NOT fixed" section were still genuinely open and
  would otherwise go dark once the parent moves to plans/archive/issues/ — this doc carries them forward so they stay in
  the AO-dispatchable corpus. Todo 2 was downgraded `[CODE]→[OPERATOR]` per
  `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s own classifier finding (it touches fleet-wide
  concurrency-critical code); **RULED 2026-07-28 (operator general theme applied): leave parked, not pursued** — see
  todo 2's own resolution text for the full reasoning. Retagged `[OPERATOR]→[REVIEW]` since this is now a closed
  decision, not an open ask.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, unified-trading-library, instruments-service]
scope: [engineer, admin]
tags: [oom, memory-leak, manifest-writer, per-vm-shard, backfill, vm-launcher, follow-up]
related:
  [
    /plans/archive/issues/per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: "2026-07-28"
parent_epic: infrastructure_master
priority: P2
source:
  [
    "split from per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md at archive time (plan_health gate
    remediation, 2026-07-28)",
    "na_docs_validity_and_ao_eligibility_audit_2026_07_26.md classifier finding re: todo 2's operator-gate",
  ]
assigned_vm: planning
resolved_by: deployment-service@d49767d
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
---

> **🗄️ ARCHIVED 2026-07-30** — `status: resolved`, `resolved_by: deployment-service@d49767d`. Audited all 3
> `CHUNK_SCRIPT=` chunked branches in `setup-data-pipeline-vm.sh` (the complete set); found `mtds_chunk_loop.sh` and
> `cefi_hl_aster_loop.sh` (the doc's own named example) both reused `VM_NAME` unmodified across chunks, fixed both with
> the same `VM_NAME="${VM_NAME}-c${CHUNK_NUM}"` scoping `instruments_chunk_loop.sh` already had; 3 new regression tests
> extracting the real generated script text (never a hand-copied excerpt). Todo 2 (the concurrency-risk item) was
> already independently ruled PARKED 2026-07-28 (see its own resolution text below) — not reopened here.

# ManifestWriter per-VM-shard follow-ups (split from the resolved OOM incident)

The incident itself is resolved and archived — full root-cause history, both fix attempts, and live verification:
`plans/archive/issues/per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md`. These 2 items are the "genuinely
open" follow-ups carried forward so they don't go dark in the archive.

## Open work

- [x] ✅ [DATA] P2. **Audit other launchers for the same latent risk — INCLUDING already-chunked ones.** The original
      framing (single-shot dispatch only) was incomplete: the real fix's own Attempt 1 proved a launcher that's ALREADY
      routed through a chunked `setup-data-pipeline-vm.sh` branch (e.g. `cefi-hl-aster-backfill`, or any other `elif`
      branch reusing one `VM_NAME` across many chunk-loop iterations over a long enough total range) carries the SAME
      latent risk unless it also scopes `VM_NAME` per chunk. Audit every chunked branch in `setup-data-pipeline-vm.sh`
      (not just single-shot `--operation ...` dispatches) for reused-VM_NAME-across-chunks exposure, cross-referenced
      against whether that launcher is ever invoked with a range wide enough to grow the shard past the ~155-165K-row
      OOM threshold in practice. **Done when**: every such launcher is either confirmed low-risk (bounded cumulative-
      shard growth for its realistic invocation range) or given the same per-chunk `VM_NAME` suffix.

      **DONE 2026-07-30 — deployment-service@d49767d.** Audited all 3 `CHUNK_SCRIPT=` chunked branches in
                                                                  `setup-data-pipeline-vm.sh` (the complete set — `grep -n 'CHUNK_SCRIPT="'` finds exactly 3, no others exist):
                                                                  `mtds_chunk_loop.sh` (mtds-backfill), `cefi_hl_aster_loop.sh` (cefi-hl-aster-backfill, day-by-day chunking,
                                                                  `VM_CHUNK_DAYS` default 1 — the doc's own named example), `instruments_chunk_loop.sh` (instruments-backfill,
                                                                  ALREADY fixed pre-existing). Found `mtds_chunk_loop.sh` and `cefi_hl_aster_loop.sh` both reused the boot-time
                                                                  `VM_NAME` unmodified across every chunk (confirmed: `export VM_NAME="$VM_NAME_SELF"` fires once at VM boot,
                                                                  `MANIFEST_PER_VM_SHARDS=true` keys the per-VM shard filename off it) — the SAME latent OOM exposure. Fixed both by
                                                                  adding the identical `VM_NAME="\${VM_NAME}-c\${CHUNK_NUM}"` per-chunk scoping `instruments_chunk_loop.sh` already
                                                                  used. Added `TestChunkedBranchesScopeVmNamePerChunk` (3 tests) to `tests/unit/test_vm_launcher_scripts.py` —
                                                                  extracts the REAL generated heredoc bodies from the source file (never a hand-copied excerpt, so it can't drift)
                                                                  and asserts the `VM_NAME` scoping literal precedes each chunk's `python -m {service}` invocation, including a
                                                                  regression test confirming `instruments_chunk_loop.sh`'s pre-existing fix is still present. Full
                                                                  `quality-gates.sh` green (2967 passed).

- [x] ✅ [REVIEW] P3. **RULED 2026-07-28 — leave PARKED, do not pursue now.** Applying the operator's general theme to
      this item: the theme's affirmative "do it fully" pushes (full backfills/migrations, adaptor completion,
      cost-not-a-concern, auto-recovery-over-manual, relaxed live-probing) are all about completing DEFINITE,
      already-committed-to work or closing real gaps — none of them affirmatively call for taking on NEW risk to a
      fleet-wide concurrency-correctness guarantee (`ManifestWriter`'s `_per_vm_shard_lock` invariant,
      `test_concurrent_writers_same_shard_lose_no_entries`) for a performance optimization that, by this doc's own
      analysis, is "no longer fixing anything broken" — the incident's real fix (per-chunk `VM_NAME` suffix) already
      addresses the acute case. This is a pure risk-tolerance judgment on correctness-critical shared code with zero
      current operational pain driving it, which is categorically different from every theme bullet (none of which is
      "take on optional correctness risk with no live justification") — so the theme does not flip this to "do it now,"
      and the doc's own recommendation (leave parked) stands. **Decision, not silence**: this is now a closed "not
      pursuing at this time" call, not an open operator-gated question — revisit ONLY if the residual case (a genuinely
      long-running single process with a constant `VM_NAME` that never restarts, e.g. a live/forward VM) starts causing
      measured, real operational pain (e.g. observed flush-cost degradation on an actual live VM), at which point
      re-open with that concrete evidence rather than resurrecting this as a standing backlog item.
