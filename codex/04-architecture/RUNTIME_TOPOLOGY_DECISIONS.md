---
doc_type: codex-ssot
title: Runtime Topology — Decisions Log
summary:
  "Durable decision record for unified-trading-pm/configs/runtime-topology.yaml — the SSOT itself declares this doc as
  its decisions_doc (ssot.decisions_doc field) but it was never created; this file closes that gap. Records WHY a
  topology change was made (deployment_profile assignment, isolation_policy choice, sla_tier calibration), not just WHAT
  changed — the yaml diff already shows the what."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, strategy-service, deployment-service]
scope: [engineer, admin]
tags: [runtime-topology, deployment-profile, decisions-log, sla-tiers, archetype]
related:
  [
    unified-trading-pm/configs/runtime-topology.yaml,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
    /plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md,
  ]
created: 2026-08-10
authoritative_for: [runtime-topology.yaml change rationale, deployment_profile decision history]
referenced_by: []
owner:
last_reviewed: 2026-08-10
code_refs: [unified-trading-pm/configs/runtime-topology.yaml]
---

# Runtime Topology — Decisions Log

**Purpose**: `runtime-topology.yaml`'s own `ssot.decisions_doc` field has pointed here since v7 (2026-07-19), but the
file was never created — this closes that gap. Append a dated entry per topology decision below; do not duplicate the
yaml's own content here, only the reasoning that isn't obvious from the diff.

## 2026-08-10 — archetype-family deployment_profile derivation (pending)

`isolation_policies.strategy-service` in `runtime-topology.yaml` has pointed to
`codex/09-strategy/architecture-v2/families/*.md` for per-archetype latency requirements since v7, but those family docs
had no latency content for `carry-and-yield` (basis), `ml-directional`, `rules-directional`, and only an incidental
mention for `arbitrage-structural` — confirmed via a 2026-08-10 investigation. Operator ruling the same day: these
families require `Low`-category (ms-realm) latency, specifically on INTER-LEG execution timing for multi-leg archetypes
(basis spot/hedge legs, cross-venue arb legs) rather than tick-to-signal decision speed — correcting the archived pre-v2
`latency-profiles.md`'s Medium/High categorization of basis.

Tracked in `/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md` (audit — populates the
family docs + derives each archetype's required `deployment_profile`) and its paired execution plan
`/plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md` (wires the decision into
`runtime-topology.yaml` + strategy-service's archetype registry). This entry will be updated with the actual
per-archetype table once the audit plan's todos complete — until then this is a placeholder recording WHY the work was
started, not a finished decision record.
