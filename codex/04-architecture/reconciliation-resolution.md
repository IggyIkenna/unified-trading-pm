---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Reconciliation Resolution Architecture

## Overview

The reconciliation resolution workflow allows operators to accept, reject, or investigate batch-live reconciliation
breaks from the UI, and book correcting trades when needed.

## Resolution Schema

`ReconciliationAction` enum and `ReconciliationResolution` model in UIC `reconciliation.py`:

| Action      | Value         | Description                                                    |
| ----------- | ------------- | -------------------------------------------------------------- |
| ACCEPT      | `accept`      | Expected divergence (timing, rounding) -- no correction needed |
| REJECT      | `reject`      | Error requiring correction -- triggers book-correction flow    |
| INVESTIGATE | `investigate` | Needs further analysis before resolution                       |

`ReconciliationResolution` fields:

- `break_id`: str -- ID of the break being resolved
- `action`: ReconciliationAction
- `note`: str (min 10 chars) -- FCA audit trail
- `resolved_by`: str -- Operator identity (OAuth sub)
- `correcting_instruction_id`: str | None -- Links to manual booking when action=REJECT

## Resolution API

Served by `batch-live-reconciliation-service/api/resolution_api.py`:

| Method | Path                            | Description                                                 |
| ------ | ------------------------------- | ----------------------------------------------------------- |
| GET    | /reconciliation/breaks          | List breaks with filters (venue, type, status)              |
| POST   | /reconciliation/resolve         | Accept/reject/investigate a break                           |
| POST   | /reconciliation/book-correction | Generate pre-filled ManualInstructionRequest for correction |

## UI Workflow

### Accept/Reject/Investigate

On the reconciliation page (`/services/reports/reconciliation`):

1. Non-resolved rows show 3 action buttons: Accept (green), Reject (red), Investigate (blue)
2. Clicking opens a dialog with note textarea (min 10 chars for FCA)
3. On confirm: calls `useResolveBreak()` mutation -> POST /reconciliation/resolve
4. Break status updates in the table

### Book Correcting Trade

When a break is rejected:

1. "Book Correction" button appears (PenLine icon)
2. Click calls `useBookCorrection()` -> POST /reconciliation/book-correction
3. Response contains pre-filled params (venue, instrument, delta quantity, execution_mode=record_only)
4. Navigates to `/services/trading/book?prefill={encoded_params}`
5. Back-office page reads prefill and populates the form

### View Market

Every reconciliation row has a "View Market" link -> navigates to
`/services/trading/markets?instrument={id}&venue={venue}`. The markets page has ManualTradingPanel as a slide-out for
that instrument.

## SSOT

- Resolution schemas: `unified-api-contracts/unified_api_contracts/internal/reconciliation.py`
- Resolution API: `batch-live-reconciliation-service/batch_live_reconciliation_service/api/resolution_api.py`
- UI hooks: `unified-trading-system-ui/hooks/api/use-reports.ts` (useResolveBreak, useReconciliationBreaks,
  useBookCorrection)
- Reconciliation page: `unified-trading-system-ui/app/(platform)/services/reports/reconciliation/page.tsx`
