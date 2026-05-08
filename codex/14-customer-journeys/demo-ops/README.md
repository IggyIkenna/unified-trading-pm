---
scope: [sales, engineer, admin]
---

# `demo-ops/` — Demo configuration + sales ops

How demo restriction profiles are built, how demo modes layer on top, and how sales context flows into provisioning and
post-demo follow-up. Combines what an earlier v1 outline called `demo-controls/` and `sales-ops/` into one directory per
Stage 2 decisions.

## Contents

| File                                                                                 | Cluster       | Purpose                                           |
| ------------------------------------------------------------------------------------ | ------------- | ------------------------------------------------- |
| [demo-restriction-profiles.md](demo-restriction-profiles.md)                         | Demo config   | Per-path profiles; Stage 3B registry link         |
| [dart-demo-modes.md](dart-demo-modes.md)                                             | Demo config   | Broader-platform / turbo / deep-dive              |
| [upsell-overlays.md](upsell-overlays.md)                                             | Demo config   | Base-package vs next-tier toggle                  |
| [pre-demo-curation-rules.md](pre-demo-curation-rules.md)                             | Demo config   | What to show / skip / skim per prospect profile   |
| [account-intelligence-record.md](account-intelligence-record.md)                     | Sales ops     | CRM structure per prospect                        |
| [pre-demo-discovery-framework.md](pre-demo-discovery-framework.md)                   | Sales ops     | What sales infers + records without interrogating |
| [demo-decision-matrix.md](demo-decision-matrix.md)                                   | Sales ops     | Prospect profile → recommended demo path          |
| [meeting-history-and-interest-tracking.md](meeting-history-and-interest-tracking.md) | Sales ops     | Session logs back into the account record         |
| [post-demo-followup-orchestration.md](post-demo-followup-orchestration.md)           | Orchestration | 7-day stall trigger + what goes out               |

## Relationship to other dirs

- **[`../experience/`](../experience/)** — experience playbooks reference demo-ops for restriction profiles (§7
  what-not-to-show), account-intelligence record updates (§9 internal handoff), and follow-up orchestration.
- **[`../commercial-model/`](../commercial-model/)** — restriction profiles reference block identifiers from rule 05 and
  commercial paths from rule 04.
- **[`../shared-core/`](../shared-core/)** — restriction profiles use venue / chain / instrument-type scope.
- **[`../infra-spec/`](../infra-spec/)** — Stage 3B's UAC combo rules are the runtime enforcement of the restriction
  profiles defined here.

## Stage 3 relationship

Stage 3B's registry reads restriction-profile identifiers defined here; Stage 3C's derivation engine resolves
`access_control(user, route, item, phase)` using the profile + commercial-path resolution.

## Cross-references

- [`../_ssot-rules/`](../_ssot-rules/) — rules 02, 04, 05, 06, 07, 08, 09, 10
- [`../experience/`](../experience/)
- [`../infra-spec/stage-3b-uac-combo-rules.md`](../infra-spec/stage-3b-uac-combo-rules.md)
- [`../infra-spec/stage-3c-derivation-engine.md`](../infra-spec/stage-3c-derivation-engine.md)
- [`../../00-SSOT-INDEX.md`](../../00-SSOT-INDEX.md)
