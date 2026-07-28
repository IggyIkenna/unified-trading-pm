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
  the AO-dispatchable corpus. Todo 2 is downgraded `[CODE]→[OPERATOR]` per
  `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s own classifier finding: it touches fleet-wide
  concurrency-critical code and needs explicit operator sign-off before an AO worker attempts it.
status: open
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
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# ManifestWriter per-VM-shard follow-ups (split from the resolved OOM incident)

The incident itself is resolved and archived — full root-cause history, both fix attempts, and live verification:
`plans/archive/issues/per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md`. These 2 items are the "genuinely
open" follow-ups carried forward so they don't go dark in the archive.

## Open work

- [ ] [DATA] P2. **Audit other launchers for the same latent risk — INCLUDING already-chunked ones.** The original
      framing (single-shot dispatch only) was incomplete: the real fix's own Attempt 1 proved a launcher that's ALREADY
      routed through a chunked `setup-data-pipeline-vm.sh` branch (e.g. `cefi-hl-aster-backfill`, or any other `elif`
      branch reusing one `VM_NAME` across many chunk-loop iterations over a long enough total range) carries the SAME
      latent risk unless it also scopes `VM_NAME` per chunk. Audit every chunked branch in `setup-data-pipeline-vm.sh`
      (not just single-shot `--operation ...` dispatches) for reused-VM_NAME-across-chunks exposure, cross-referenced
      against whether that launcher is ever invoked with a range wide enough to grow the shard past the ~155-165K-row
      OOM threshold in practice. **Done when**: every such launcher is either confirmed low-risk (bounded cumulative-
      shard growth for its realistic invocation range) or given the same per-chunk `VM_NAME` suffix.
- [ ] [OPERATOR] P3. **Library-level fix for the `ManifestWriter` per-VM-shard flush cost — NO LONGER BLOCKING, still
      worth doing eventually.** Caching the merged DataFrame + GCS-generation-check (the originally proposed fix) would
      reduce REDUNDANT download+parse work across flushes, but would NOT reduce PEAK memory at the moment of
      `merged.to_parquet()` — that allocation is proportional to the CURRENT shard size regardless of whether
      `existing_df` came from a fresh download or a cache, so it would not actually have fixed the original incident.
      The per-chunk `VM_NAME` suffix (the incident's real fix) addresses the acute case (any launcher that chunks into
      fresh processes) by capping shard size directly. This item remains open only for the residual case of a genuinely
      long-running SINGLE process with a constant `VM_NAME` that never restarts (e.g. a live/forward VM) — lower
      urgency, no longer incident-driving. **Retagged `[CODE]→[OPERATOR]`**: this touches fleet-wide
      concurrency-critical code (`ManifestWriter`'s `_per_vm_shard_lock` correctness guarantee,
      `test_concurrent_writers_same_shard_lose_no_entries`) — needs explicit operator sign-off on the caching approach
      before an AO worker attempts it, not a judgment call for a worker to make alone. If picked up: cache the merged
      per-VM shard DataFrame + its GCS generation in the `ManifestWriter` instance across flushes, generation-checked
      before trusting the cache (falls back to a full read on any mismatch — must preserve the existing
      concurrent-writer correctness guarantee exactly). **Done when**: (a) both existing suites stay green
      (`test_manifest_writer_per_vm.py`, `test_manifest_writer_per_vm_debounce.py`), AND (b) a NEW adversarial test
      proves the generation-check detects a concurrent mutation and falls back to a full read-merge (not just that the
      happy-path cache hit works). `quality-gates.sh` green on `unified-trading-library`.
