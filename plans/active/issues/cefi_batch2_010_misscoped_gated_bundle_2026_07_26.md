---
doc_type: issue
title: cefi_satellite_ao_dispatch_batch2-010 is a mis-scoped, multi-gated bundle — cannot close in one backend slot
summary: >-
  The AO task `cefi_satellite_ao_dispatch_batch2-010` ([BACKEND] P0, plan
  `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` line 228) bundles four residuals from the `assigned_vm: NA`
  (local-only) source doc `cefi_residual_followups_after_honest_done_2026_07_17.md` into ONE "bounded, decision-free"
  backend checkbox. In reality the four span four crafts and three gate-classes: a 4-service CLOUD DEPLOY (infra +
  cloudbuild-evidence), a features IMAGE BUILD fix (infra + cloudbuild-evidence), a ~116,742-row MANIFEST `--apply`
  (data + VM heavy-I/O + operator/delete-safety gate; no script exists yet), and 4 CODEX SSOT edits (docs-reconciliation
  channel + operator-ruling; the plan's own doc paths are wrong). NONE can be closed by an in-slot backend worker with
  the runtime-verification evidence the workspace HARD RULES require. Filed by slot-10 on dispatch of batch2-010; the P0
  checkbox was NOT flipped.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    execution-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags:
  [cefi, ao-dispatch, mis-scoped, gated, findings, reader-bridge, canonical-filename, manifest, codex-reconciliation]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: cefi_satellite_ao_dispatch_batch2-010 dispatch to slot-10 (2026-07-26) — findings-closure escalation
resolved_by:
---

# cefi_satellite_ao_dispatch_batch2-010 — mis-scoped, multi-gated bundle

## What I found

`cefi_satellite_ao_dispatch_batch2-010` was dispatched to slot-10 as `[BACKEND] P0` (plan
`/plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md` line 228). Its own text calls the four sub-items
"bounded, decision-free residuals … safe as one worker's sequential pass." On investigation that framing does not hold —
the four are RE-DISPATCHES of four already-tracked todos in the source doc
`/plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md`, which is deliberately
`assigned_vm: NA` + `execution_scope: local-only` because the deploy/cutover/manifest work is drain- and operator-gated.
They span four crafts and three gate-classes, and **none is closeable by an in-slot backend worker with the evidence the
workspace runtime-verification HARD RULE (`plans/PLAN_FORMAT.md` §8b) demands**:

| #   | Sub-item                                                                                             | Source-doc todo                    | Real craft / gate                     | Why not in-slot-closeable                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --- | ---------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Deploy the D3 reader-bridge build to MTDS / MDPS / features / execution                              | Phase 0b `[BACKEND] P0` (line 398) | infra + cloud                         | Code already shipped (`market-tick-data-service@0388e1a9`, `market-data-processing-service@0035f79`, `features-service@efd3e038`). "Deploy" = 4 Cloud Run/job redeploys; done-when = "all 4 confirmed running the build (redeploy logs/version check)" — cloud verification, not a code change. No in-slot deploy path; needs `Evidence: cloudbuild=<id>`.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2   | Fix the features-service image build (`cefi_wire_bridge.py` ImportError)                             | Phase 0b `[INFRA] P1` (line 402)   | infra + cloud-build                   | Confirmed: `Dockerfile:23` pins `BASE_IMAGE_DIGEST=sha256:3bd6d0b7…` and installs UAC via `uv pip install --no-sources` (line 64), so a new UAC symbol (`CeFiWireCanonicalMap`) is absent if the base image predates it. Fix (digest bump OR COPY-fresh-UAC-source, a cloudbuild.yaml/Dockerfile change) is verifiable ONLY by an actual image build → `Evidence: cloudbuild=<id>` SUCCESS. Local `quality-gates.sh` is already green here (editable UAC in `.venv`), so it does NOT prove the image builds — the done-when's local-QG alternative is a red herring for this specific defect.                                                                                                                                                                                            |
| 3   | OKX-FUTURES manifest `instrument_type` mislabel (~116,742 rows PERPETUAL→FUTURE, dated-futures only) | Phase 1 `[SCRIPT] P2` (line 441)   | data + VM + operator                  | **No script exists** — none of the instruments-service `canonicalize_*` scripts covers this itype relabel. Requires WRITING a new migration + dry-run + snapshot-first + `--apply` on a VM (heavy-I/O manifest-index rewrite = HARD RULE "never from local machine"), gated `[OPERATOR]` per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. Current live presence of the mislabel was NOT re-verified in-session (a live `_index` read is itself best done on the VM that would run the fix).                                                                                                                                                                                                                                                                              |
| 4   | Resolve 4 codex↔plan SSOT contradictions                                                             | Phase 2 `[DOCS] P1` (line 469)     | docs-reconciliation + operator-ruling | Doc 1 (`/codex/02-data/chart-candle-delivery-flow.md:287`) is CONFIRMED still stale ("Filename is the bare symbol…"). But the plan's other references are imprecise: doc 4 is at `/codex/02-data/per-asset-group-bucket-layouts.md`, NOT `codex/05-infrastructure/…:135`; and `/codex/06-coding-standards/read-time-filter-pushdown.md` (144 lines) has no "substring-match filename assumption" matching the ask. Codex reconciliation is a live DEDICATED workstream (recent `docs(codex): apply …-reconciliation findings` commits) — ad-hoc SSOT edits from a `drift_direction: advance-code` backend task bypass it, and both the backend_engineer craft ("edit codex only if drift is correct-codex") and the plan_reconciler discipline ("codex edits NEVER autonomous") gate it. |

## Why it matters

Flipping this P0 in-slot would require fabricating unverifiable "done" claims for a cloud deploy, a cloud image build,
and a 116,742-row manifest `--apply` — exactly the false-progress the runtime-verification HARD RULE and
`check_evidence_backed_completion.py` exist to stop. Re-dispatching the same checkbox to another backend slot repeats
the wall (each backend worker hits the same gates). The four residuals are already correctly tracked and phase-gated in
the source doc; the defect is the AO re-derivation of them into a single "decision-free backend" checkbox.

## Recommended decision

**Un-dispatch batch2-010 — do not re-route it to another backend slot.** The four residuals stay tracked in the source
doc under their proper gates; sequence them through the right channels:

- Sub-items 1 + 2 → an `[INFRA]` + `[OPERATOR]` deploy/build unit with `Evidence: cloudbuild=<id>` (the reader-bridge
  deploy is a prerequisite that can land ahead of the drain; the features image-build fix is non-cutover-blocking).
- Sub-item 3 → a `[SCRIPT]` + `[OPERATOR]` data unit: write the itype-relabel migration, dry-run, snapshot-first,
  `--apply` on a VM coordinated with the Phase-1 cefi drain.
- Sub-item 4 → the docs-reconciliation channel (per-doc verification first — the plan's paths are wrong), operator-ruled
  per the codex-edit discipline.

Operator: confirm the routing (or re-author batch2-010 into four correctly-tagged/gated todos). The todos below are
`[OPERATOR]`-gated so they do NOT auto-dispatch back to a worker slot before that routing decision.

## Todos

- [ ] [OPERATOR] P1. Rule on routing batch2-010: either un-dispatch it (the four residuals remain tracked in
      `cefi_residual_followups_after_honest_done_2026_07_17.md` under their Phase-0b/1/2 gates) OR re-author it into
      four correctly-tagged/gated todos ([INFRA]+[OPERATOR] deploy/build, [SCRIPT]+[OPERATOR] manifest `--apply`, [DOCS]
      codex-reconciliation). Until ruled, the batch2-010 checkbox stays `- [ ]` (not fake-closed). (repo:
      unified-trading-pm)
- [ ] [OPERATOR] P1. Sequence the reader-bridge deploy + features image-build fix as an [INFRA] unit with cloudbuild
      evidence (repos: market-tick-data-service, market-data-processing-service, features-service, execution-service).
- [ ] [OPERATOR] P2. Sequence the OKX-FUTURES itype-relabel (~116,742 rows) as a VM-run, snapshot-first,
      drain-coordinated data `--apply` — a migration script still needs to be written (repo: instruments-service).
- [ ] [DOCS] P1. Route the 4 codex↔plan SSOT reconciliations through the docs-reconciliation channel after fixing the
      plan's stale doc paths (doc 4 → `/codex/02-data/per-asset-group-bucket-layouts.md`; re-locate doc 2's actual
      claim) (repo: unified-trading-pm).
