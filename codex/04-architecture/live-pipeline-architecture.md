---
title: Live Pipeline Architecture
type: architecture
status: stub
created: 2026-05-21
---

# Live Pipeline Architecture

> **STUB** — Reference: `plans/epics/defi_master.md`.

The live pipeline is the same code path as batch, operating in live mode:
`instruments-service → MTDS → features → strategy → execution`. Identical schemas and data_types; only difference is
execution fills replace simulated fills.

See CLAUDE.md "Live = batch" and `codex/02-data/availability-manifest-and-data-status.md`.
