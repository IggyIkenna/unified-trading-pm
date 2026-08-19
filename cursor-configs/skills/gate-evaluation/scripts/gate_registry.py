#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Gate registry -- the 53 BATCH/PAPER/LIVE data-pipeline readiness gates,
transcribed verbatim (id, name, bar, owning_doc) from
/plans/active/data_pipeline_completion_2026_08_21.md's own gate tables, as
cross-linked by the 2026-08-18 infra pass (batch15 item 7). This module owns
DATA only -- no evaluation logic lives here (see evaluate_gates.py / checks.py
for that), mirroring the readiness-state-dump / honest-coverage-dump split
between a registry module and its evaluator.

`owning_doc=None` means the register plan's own cross-link pass found no
dedicated owning plan/issue doc for that gate (29 of 53, confirmed by the
`NO_OWNING_DOC_COUNT` assertion at the bottom of this file) -- most of these
are corpus-wide policies documented in a codex SSOT rather than a tracked
work item, or genuinely un-tracked concerns. `None` here is not a defect in
this registry; it is the finding the source doc itself already recorded.

Re-sync this registry by hand whenever data_pipeline_completion_2026_08_21.md's
own gate tables change (a new gate added, an owning_doc filled in, a bar
re-worded) -- there is no automated doc-to-registry sync; treat drift between
this file and the source doc's tables as a doc-hygiene finding, same as any
other "doc that misled you" case.
"""

from __future__ import annotations

from dataclasses import dataclass

_REGISTER_DOC = "/plans/active/data_pipeline_completion_2026_08_21.md"


@dataclass(frozen=True)
class Gate:
    gate_id: str
    category: str  # BATCH | PAPER | LIVE
    name: str
    bar: str  # concise paraphrase -- the register doc is the SSOT for the full prose
    owning_doc: str | None  # None == confirmed "no owning doc" per the 2026-08-18 cross-link pass


GATES: tuple[Gate, ...] = (
    # --- BATCH (B1-B26) ---
    Gate(
        "B1",
        "BATCH",
        "Availability",
        ">0 honest coverage per shard dimension, excluding empty_confirmed",
        None,
    ),
    Gate(
        "B2",
        "BATCH",
        "Smoke test",
        "Data is downloadable; minimum 1h machine runtime",
        "/plans/active/venue_smoke_test_bar_2026_08_16.md",
    ),
    Gate(
        "B3",
        "BATCH",
        "Observability and recovery",
        "Alerting + auto-recovery + no zombie/duplicate VMs",
        None,
    ),
    Gate(
        "B4",
        "BATCH",
        "Resource",
        "Recorded resources actually used to reach current state, per shard",
        None,
    ),
    Gate(
        "B5",
        "BATCH",
        "Performance",
        "Concrete throughput figure + ETA to completion, per shard",
        "/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md",
    ),
    Gate(
        "B6",
        "BATCH",
        "Vertical scaling",
        "Bundled multi-shard resource requirements auto-aggregated, no waste",
        None,
    ),
    Gate(
        "B7",
        "BATCH",
        "Daily T+1 backfill",
        "Scheduled backfill keeps honest coverage at 100%, no decay",
        None,
    ),
    Gate(
        "B8",
        "BATCH",
        "Honest coverage 100%",
        "Full coverage over the declared expected set",
        None,
    ),
    Gate(
        "B9",
        "BATCH",
        "No silent zero-row success",
        "Progress = count of TARGET artefacts, never activity",
        None,
    ),
    Gate(
        "B10",
        "BATCH",
        "Non-retriable classification",
        "Every attempted_failed shard verdicted retriable vs structurally non-retriable",
        "/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md",
    ),
    Gate(
        "B11",
        "BATCH",
        "Rightsizing verdict",
        "Any shard deployment running >30min carries a CPU/memory rightsizing verdict",
        "/codex/05-infrastructure/vm-launcher-runbook.md",
    ),
    Gate(
        "B12",
        "BATCH",
        "Per-source concurrency cap declared",
        "Each source declares max concurrent workers from its real rate limits",
        "/codex/05-infrastructure/vm-launcher-runbook.md",
    ),
    Gate(
        "B13",
        "BATCH",
        "Single-walk discipline",
        "Coverage answerable from the manifest, no new whole-corpus GCS walk",
        None,
    ),
    Gate(
        "B14",
        "BATCH",
        "Shard-atom identity across surfaces",
        "Identical atom string across writer/manifest/status/gate/UI",
        None,
    ),
    Gate(
        "B15",
        "BATCH",
        "Idempotent re-run/skip semantics",
        "A re-run without --force skips genuinely-captured, not absent",
        None,
    ),
    Gate(
        "B16",
        "BATCH",
        "Denominator declared",
        "Every coverage % states its denominator; 4 capture states reported separately",
        "/codex/02-data/honest-coverage-model.md",
    ),
    Gate(
        "B17",
        "BATCH",
        "Cost recorded",
        "Actual spend to reach current state, per shard",
        None,
    ),
    Gate(
        "B18",
        "BATCH",
        "Canonical value-check, not just path shape",
        "UAC oracle PLUS a separate check on filename instrument_id + axis VALUES",
        "/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md",
    ),
    Gate(
        "B19",
        "BATCH",
        "Consolidator freshness gating",
        "A launcher with a stale manifest index exits rather than proceeding",
        "/codex/05-infrastructure/manifest-consolidator-ssot.md",
    ),
    Gate(
        "B20",
        "BATCH",
        "Orthogonal shard vocabulary",
        "[OPERATOR] sign-off: no two shard names describe the same thing",
        "/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md",
    ),
    Gate(
        "B21",
        "BATCH",
        "Manifest canonical on the named surface",
        "Zero non-canonical entries in deployment-UI Distinct Values, per AG",
        "/plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md",
    ),
    Gate(
        "B22",
        "BATCH",
        "Path <-> manifest reconciled BOTH ways",
        "manifest->path and path->manifest, manifest-driven, no new whole-corpus walk",
        "/codex/02-data/orphan-object-detection.md",
    ),
    Gate(
        "B23",
        "BATCH",
        "Schemas conformant, locked, versioned",
        "Every GCS object conforms to a declared, locked, versioned schema",
        "/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md",
    ),
    Gate(
        "B24",
        "BATCH",
        "Minimum history declared per shard, transitive",
        "Transitive closure through the tick->candle->feature->archetype chain",
        _REGISTER_DOC,
    ),
    Gate(
        "B25",
        "BATCH",
        "Registration fails when declared config exceeds history",
        "A config asking more lookback than measured coverage is rejected at registration",
        _REGISTER_DOC,
    ),
    Gate(
        "B26",
        "BATCH",
        "Three-stage benchmark per shard",
        "fetch throughput / process latency / write throughput, per shard, per mode",
        "/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md",
    ),
    # --- PAPER (P1-P13) ---
    Gate(
        "P1",
        "PAPER",
        "Live adapter parity",
        "A live adapter exists for every batch adapter, never the reverse",
        "/plans/active/venue_e2e_wiring_2026_08_16.md",
    ),
    Gate(
        "P2",
        "PAPER",
        "Live capture running, with a freshness SLA",
        "Running + a declared staleness bound",
        None,
    ),
    Gate(
        "P3",
        "PAPER",
        "Schema parity, batch <-> live",
        "Identical schemas; live is the same code path as batch",
        "/codex/02-data/live-data-persistence-and-event-log.md",
    ),
    Gate(
        "P4",
        "PAPER",
        "Determinism proof (epsilon=0)",
        "paper(W) == batch-rerun(W) trade-for-trade, proven with a negative control",
        "/codex/09-strategy/operational/paper-batch-live-reconciliation.md",
    ),
    Gate(
        "P5",
        "PAPER",
        "Gap backfill closes the loop",
        "T+1 batch pass fills a live drop; honest coverage returns to 100%",
        None,
    ),
    Gate(
        "P6",
        "PAPER",
        "Stream continuity detection",
        "Sequence/ordering continuity checked; dupes/gaps detected",
        None,
    ),
    Gate(
        "P7",
        "PAPER",
        "Transport is the event-log spine",
        "Published via the UTL EventTransport facade, never a bespoke transport",
        "/codex/02-data/live-data-persistence-and-event-log.md",
    ),
    Gate(
        "P8",
        "PAPER",
        "Latency instrumentation",
        "time-data-received and time-data-sent recorded on every artefact",
        None,
    ),
    Gate(
        "P9",
        "PAPER",
        "Staleness SLA per input",
        "Each input declares a reasonable wait before it is stale",
        None,
    ),
    Gate(
        "P10",
        "PAPER",
        "Testnet position recorded per venue",
        "Testnet existence/behaviour, or a simulated-matching-engine fallback, recorded per venue",
        "/plans/active/venue_smoke_test_bar_2026_08_16.md",
    ),
    Gate(
        "P11",
        "PAPER",
        "Read credentials present",
        "Live market-data READ credentials exist (not execution accounts)",
        None,
    ),
    Gate(
        "P12",
        "PAPER",
        "Preflight input registration",
        "A missing required input fails at registration, not mid-run",
        None,
    ),
    Gate(
        "P13",
        "PAPER",
        "Gap-recovery policy declared per (SOURCE x STRATEGY)",
        "Cross product of source-replayability and strategy gap-tolerance, per pair",
        None,
    ),
    # --- LIVE (L1-L14) ---
    Gate(
        "L1",
        "LIVE",
        "All PAPER gates hold",
        "Non-negotiable precondition on the PAPER table above",
        None,
    ),
    Gate(
        "L2",
        "LIVE",
        "SLOs declared and measured",
        "Freshness/completeness/latency SLOs per shard, actual attainment measured",
        None,
    ),
    Gate(
        "L3",
        "LIVE",
        "Alerting pages a human, with a defined ladder",
        "retry -> restart -> drain -> hold-dependants -> halt; lifecycle events never page",
        "/codex/05-infrastructure/data-pipeline-alerts.md",
    ),
    Gate(
        "L4",
        "LIVE",
        "Auto-recovery matrix respected",
        "Protective arming autonomous; resume autonomous only within the matrix",
        "/codex/04-architecture/autonomous-recovery-matrix.md",
    ),
    Gate(
        "L5",
        "LIVE",
        "In-line data-quality rejection",
        "Bad rows rejected/quarantined at write time, never silent placeholders",
        None,
    ),
    Gate(
        "L6",
        "LIVE",
        "Backpressure handled",
        "Defined shed/buffer/halt behaviour when consumers fall behind",
        None,
    ),
    Gate(
        "L7",
        "LIVE",
        "Consolidator availability",
        "The manifest consolidator is not a single point of failure for the live path",
        "/codex/05-infrastructure/manifest-consolidator-ssot.md",
    ),
    Gate(
        "L8",
        "LIVE",
        "Runbook with owner, cadence, verifier",
        "Declared and current; a verifier + last-executed date required",
        None,
    ),
    Gate(
        "L9",
        "LIVE",
        "DR and failover exercised",
        "Region/cloud failover for the capture path, TESTED not merely designed",
        None,
    ),
    Gate(
        "L10",
        "LIVE",
        "Retention and lifecycle policy",
        "Declared per data type and actually enforced; live volume cost bounded",
        "/codex/05-infrastructure/gcs-lifecycle-policies.md",
    ),
    Gate(
        "L11",
        "LIVE",
        "Production-scale cost model",
        "Cost at live volume, with headroom stated",
        None,
    ),
    Gate(
        "L12",
        "LIVE",
        "Access control and audit",
        "Who can read each shard, recorded + enforced; immutable audited status",
        None,
    ),
    Gate(
        "L13",
        "LIVE",
        "Reconciliation against venue-reported totals",
        "Captured totals reconcile to venue-published totals within a declared tolerance",
        None,
    ),
    Gate(
        "L14",
        "LIVE",
        "Intraday recovery EXERCISED, not designed",
        "Every P13 recovery-claiming pair has actually run its recovery; halt-only pairs exercised too",
        None,
    ),
)

CATEGORIES: tuple[str, ...] = ("BATCH", "PAPER", "LIVE")

#: Gates this skill wires a REAL machine check for (see evaluate_gates.py's
#: CHECKERS map) -- kept here too so a caller can answer "is this gate
#: automated?" without importing the evaluator.
AUTOMATED_GATE_IDS: frozenset[str] = frozenset({"B1", "B8", "B16"})

# Self-check: the register doc's own 2026-08-18 cross-link pass counted 29 of
# 53 gates with no owning doc (11 BATCH + 8 PAPER + 10 LIVE). If this
# transcription ever drifts from that count, it is a sign this file fell out
# of sync with the source doc -- fail loudly at import time rather than
# silently reporting a wrong owning-doc picture.
_NO_OWNING_DOC_COUNT = sum(1 for g in GATES if g.owning_doc is None)
if _NO_OWNING_DOC_COUNT != 29:
    raise AssertionError(
        f"gate_registry.py drifted from {_REGISTER_DOC}'s own cross-link count: "
        f"expected 29 gates with no owning_doc, found {_NO_OWNING_DOC_COUNT}. "
        "Re-sync this registry against the source doc's gate tables before trusting a run."
    )
if len(GATES) != 53:
    raise AssertionError(f"gate_registry.py has {len(GATES)} gates, expected 53 (26 BATCH + 13 PAPER + 14 LIVE).")
