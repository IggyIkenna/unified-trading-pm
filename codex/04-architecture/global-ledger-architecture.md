---
title: Global Ledger Architecture
type: architecture
status: stub
created: 2026-05-21
---

# Global Ledger Architecture

> **STUB** — Reference: `plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md`.

The global ledger aggregates per-client, per-archetype P&L across DeFi + CeFi legs. Consumes fill events + funding +
borrow costs → emits attribution parquets per `(client_id, archetype, date)`. Full architecture pending; discovery phase
captured in referenced plan.
