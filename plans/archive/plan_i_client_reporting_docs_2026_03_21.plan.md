---
doc_type: plan
title: plan-i-client-reporting-docs
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, unified-trading-api]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
overview: 'Client-facing business services: document management, invoicing, MiFID compliance reporting, DocuSign integration, and client-reporting-api enhancement — sits outside the core trading system'
type: mixed
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: client-reporting-api, code: C0, deployment: none, business: none}
- {repo: unified-internal-contracts, code: C0, deployment: none, business: none}
- {repo: unified-cloud-interface, code: C0, deployment: none, business: none}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
depends_on: [plan-g-auth-entitlement]
todos:
- {id: i-p0-doc-metadata-schema, content: '- [ ] [AGENT] P0. Add document metadata schema to UIC (DocumentMetadata: id, org_id, category, filename, size, content_type, uploaded_by, uploaded_at, status, docusign_envelope_id)

    ', status: todo}
- {id: i-p0-doc-categories-enum, content: '- [ ] [AGENT] P0. Add document categories enum to UIC (INVOICE, ONBOARDING, REGULATORY, CONTRACT, REPORT, COMPLIANCE)

    ', status: todo}
- {id: i-p0-presigned-url-helpers, content: '- [ ] [AGENT] P0. Add pre-signed URL helpers to UCI (generate_upload_url, generate_download_url — wraps GCS/S3 signed URLs with configurable expiry)

    ', status: todo}
- {id: i-p0-doc-bucket-registry, content: '- [ ] [AGENT] P0. Add documents GCS bucket to UCI bucket registry (org-scoped prefix: documents/{org_id}/{category}/)

    ', status: todo}
- {id: i-p0-doc-metadata-storage, content: '- [ ] [AGENT] P1. Add document metadata storage (BigQuery table or GCS JSON — lightweight CRUD)

    ', status: todo, blocked_by: i-p0-doc-metadata-schema}
- {id: i-p1-audit-existing, content: '- [ ] [AGENT] P0. Audit existing client-reporting-api for current endpoints and mock mode

    ', status: todo, blocked_by: i-p0-doc-metadata-schema}
- {id: i-p1-pnl-reporting, content: '- [ ] [AGENT] P0. Add P&L reporting endpoints (daily/weekly/monthly P&L by account, strategy, instrument)

    ', status: todo, blocked_by: i-p1-audit-existing}
- {id: i-p1-client-returns, content: '- [ ] [AGENT] P0. Add client returns calculation (TWR, MWR, benchmark-relative)

    ', status: todo, blocked_by: i-p1-audit-existing}
- {id: i-p1-settlement-reporting, content: '- [ ] [AGENT] P0. Add settlement reporting (trade confirmations, settlement status)

    ', status: todo, blocked_by: i-p1-audit-existing}
- {id: i-p1-readonly-api-key, content: '- [ ] [AGENT] P0. Add read-only API key auth mode (serve any account with valid API key, not just "our" accounts)

    ', status: todo, blocked_by: i-p1-audit-existing}
- {id: i-p1-historical-performance, content: '- [ ] [AGENT] P1. Add historical performance reporting (drawdown, Sharpe, rolling returns)

    ', status: todo, blocked_by: i-p1-audit-existing}
- {id: i-p2-invoice-generation, content: '- [ ] [AGENT] P0. Add invoice generation endpoint (POST /api/v1/invoices/generate — creates PDF from template)

    ', status: todo, blocked_by: i-p1-pnl-reporting}
- {id: i-p2-invoice-templates, content: '- [ ] [AGENT] P0. Add invoice templates (management fee, performance fee, advisory fee, regulatory fee)

    ', status: todo, blocked_by: i-p2-invoice-generation}
- {id: i-p2-invoice-delivery, content: '- [ ] [AGENT] P0. Add invoice delivery (generates invoice -> stores as document -> notifies client)

    ', status: todo, blocked_by: i-p2-invoice-templates}
- {id: i-p2-invoice-listing, content: '- [ ] [AGENT] P0. Add invoice listing/download (client sees their invoices in portal)

    ', status: todo, blocked_by: i-p2-invoice-generation}
- {id: i-p2-billing-cycle, content: '- [ ] [AGENT] P1. Add billing cycle management (monthly/quarterly, auto-generate on cycle end)

    ', status: todo, blocked_by: i-p2-invoice-delivery}
- {id: i-p2-fee-calculation, content: '- [ ] [AGENT] P1. Add fee calculation engine (management fee %, performance fee % with HWM)

    ', status: todo, blocked_by: i-p2-invoice-generation}
- {id: i-p3-trade-reporting, content: '- [ ] [AGENT] P0. Add trade reporting endpoints (MiFID II transaction reporting fields)

    ', status: todo, blocked_by: i-p1-pnl-reporting}
- {id: i-p3-position-monitoring, content: '- [ ] [AGENT] P0. Add position monitoring (large position reporting thresholds)

    ', status: todo, blocked_by: i-p1-pnl-reporting}
- {id: i-p3-best-execution, content: '- [ ] [AGENT] P0. Add best execution reporting (venue analysis, slippage attribution)

    ', status: todo, blocked_by: i-p1-pnl-reporting}
- {id: i-p3-regulatory-umbrella, content: '- [ ] [AGENT] P0. Add regulatory umbrella monitoring (track what clients are doing, flag violations)

    ', status: todo, blocked_by: i-p1-pnl-reporting}
- {id: i-p3-compliance-dashboard, content: '- [ ] [AGENT] P1. Add compliance dashboard data (alerts, violations, remediation status)

    ', status: todo, blocked_by: i-p3-trade-reporting}
- {id: i-p3-regulatory-filing, content: '- [ ] [AGENT] P1. Add regulatory filing preparation (pre-fill EMIR, MiFIR fields)

    ', status: todo, blocked_by: i-p3-trade-reporting}
- {id: i-p4-docusign-client, content: '- [ ] [AGENT] P1. Add DocuSign API client in client-reporting-api (create envelope, send for signature)

    ', status: todo, blocked_by: i-p0-doc-metadata-schema}
- {id: i-p4-send-for-signature, content: '- [ ] [AGENT] P1. Add POST /api/v1/documents/{id}/send-for-signature endpoint

    ', status: todo, blocked_by: i-p4-docusign-client}
- {id: i-p4-signature-status, content: '- [ ] [AGENT] P1. Add GET /api/v1/documents/{id}/signature-status endpoint

    ', status: todo, blocked_by: i-p4-docusign-client}
- {id: i-p4-docusign-webhook, content: '- [ ] [AGENT] P1. Add DocuSign webhook receiver (completion notifications -> update document status)

    ', status: todo, blocked_by: i-p4-docusign-client}
- {id: i-p4-onboarding-workflow, content: '- [ ] [AGENT] P2. Add onboarding document workflow (KYC/AML docs -> DocuSign -> approved -> access granted)

    ', status: todo, blocked_by: i-p4-docusign-webhook}
- {id: i-p5-upload-url, content: '- [ ] [AGENT] P0. Add POST /api/v1/documents/upload-url (returns pre-signed upload URL + document_id)

    ', status: todo, blocked_by: i-p0-presigned-url-helpers}
- {id: i-p5-download-url, content: '- [ ] [AGENT] P0. Add GET /api/v1/documents/{id}/download-url (entitlement-checked pre-signed download URL)

    ', status: todo, blocked_by: i-p0-presigned-url-helpers}
- {id: i-p5-list-documents, content: '- [ ] [AGENT] P0. Add GET /api/v1/documents (list documents for org, filterable by category)

    ', status: todo, blocked_by: i-p0-doc-metadata-schema}
- {id: i-p5-delete-document, content: '- [ ] [AGENT] P0. Add DELETE /api/v1/documents/{id} (soft delete, admin only)

    ', status: todo, blocked_by: i-p0-doc-metadata-schema}
- {id: i-p5-upload-completion-webhook, content: '- [ ] [AGENT] P1. Add document upload completion webhook (cloud storage notification -> update metadata)

    ', status: todo, blocked_by: i-p5-upload-url}
- {id: i-p6-seed-mock-data, content: '- [ ] [AGENT] P0. Create seed_mock_data.py for client-reporting-api (mock invoices, reports, documents)

    ', status: todo, blocked_by: i-p2-invoice-generation}
- {id: i-p6-mock-doc-uploads, content: '- [ ] [AGENT] P0. Mock document uploads (pre-signed URLs point to local filesystem in mock mode)

    ', status: todo, blocked_by: i-p5-upload-url}
- {id: i-p6-qg, content: '- [ ] [AGENT] P0. Run quality-gates.sh on client-reporting-api

    ', status: todo, blocked_by: i-p6-seed-mock-data}
- {id: i-p6-sit-tests, content: '- [ ] [AGENT] P1. Add SIT tests for document upload/download flow

    ', status: todo, blocked_by: i-p6-qg}
isProject: false
---

# Notes & Context

## Pre-Signed URL Pattern

```
UPLOAD FLOW:
                                                          +------------------+
  Client ──POST /documents/upload-url──> API ──generate──>| GCS/S3 Signed URL|
  Client <──{upload_url, document_id}──  API              +------------------+
  Client ──PUT {file bytes}──────────────────────────────>| GCS/S3 Bucket    |
                                                          +------------------+
  GCS/S3 ──object.finalize notification──> API ──update──> DocumentMetadata.status = UPLOADED

DOWNLOAD FLOW:
  Client ──GET /documents/{id}/download-url──> API ──entitlement check──> generate signed URL
  Client <──{download_url, expires_in}──────── API
  Client ──GET {signed URL}──────────────────────────────> GCS/S3 Bucket ──> file bytes
```

Pre-signed URLs have configurable expiry (default: 15 minutes for upload, 1 hour for download). The API never handles
file bytes directly — all file transfer is client-to-cloud-storage.

## Document Categories

| Category   | Use Case                                             | Typical Formats |
| ---------- | ---------------------------------------------------- | --------------- |
| INVOICE    | Management/performance/advisory fee invoices         | PDF             |
| ONBOARDING | KYC/AML docs, account opening, IMA agreements        | PDF, DOCX       |
| REGULATORY | MiFID II reports, EMIR filings, best execution       | PDF, XML        |
| CONTRACT   | IMAs, side letters, amendments                       | PDF, DOCX       |
| REPORT     | P&L reports, performance reports, settlement reports | PDF, CSV, XLSX  |
| COMPLIANCE | Compliance certifications, audit trails, policy docs | PDF             |

## Why Client-Reporting Is Separate From Trading API

client-reporting-api serves a fundamentally different business function:

1. **Different audience**: External clients (fund investors, counterparties) vs internal traders/quants
2. **Different auth model**: Read-only API key access to ANY account (not just "our" accounts) — a client can query
   their own P&L, invoices, and documents without access to the trading system
3. **Different compliance surface**: MiFID II transaction reporting, best execution analysis, regulatory filings — these
   are legal obligations, not trading features
4. **Different lifecycle**: Invoicing runs on billing cycles (monthly/quarterly), not trade cycles
5. **Proxied through unified-trading-api** (Plan H): The UI still calls one API origin; the documents domain in
   unified-trading-api proxies to client-reporting-api

## DocuSign Integration Flow

```
1. Admin uploads document (contract, onboarding form) via /documents/upload-url
2. Admin calls POST /documents/{id}/send-for-signature
   -> API creates DocuSign envelope with document + signer list
   -> DocuSign sends email to signers
3. Signer opens DocuSign link, signs document
4. DocuSign calls webhook -> API updates DocumentMetadata:
   - docusign_envelope_id set
   - status = SIGNED
5. Onboarding workflow: all KYC/AML docs signed -> client access granted
```

DocuSign credentials stored in Secret Manager (`docusign-integration-key`, `docusign-api-account-id`). Mock mode:
DocuSign client returns synthetic envelope IDs, webhook simulated by seed data.

## Invoicing Fee Calculation Model

```
Management Fee:
  fee = AUM * annual_rate / periods_per_year
  Example: $10M AUM * 2% / 12 = $16,667/month

Performance Fee (with High Water Mark):
  if current_nav > high_water_mark:
    fee = (current_nav - high_water_mark) * performance_rate
    high_water_mark = current_nav
  else:
    fee = 0
  Example: NAV $11M, HWM $10M, rate 20% -> fee = $200K

Advisory Fee:
  fee = flat_amount_per_period (no AUM dependency)

Regulatory Fee:
  fee = pass-through of exchange/regulatory costs (itemized)
```

Fee schedules stored per-org in config. Billing cycles: monthly or quarterly, configurable per client. Auto-generation:
cron job at cycle end creates draft invoices for human review before delivery.

## Execution DAG

```
Phase 0: Document Infrastructure (PARALLEL)
  i-p0-doc-metadata-schema ──────┐
  i-p0-doc-categories-enum ──────┤
  i-p0-presigned-url-helpers ────┤
  i-p0-doc-bucket-registry ──────┘
  i-p0-doc-metadata-storage (after schema)
       |
       v (QG gate: UIC + UCI pass quality-gates.sh)
Phase 1: Reporting Enhancement (PARALLEL)    Phase 4: DocuSign (SEQUENTIAL)    Phase 5: Document Routes (PARALLEL)
  i-p1-audit-existing                          i-p4-docusign-client              i-p5-upload-url
  i-p1-pnl-reporting                           i-p4-send-for-signature           i-p5-download-url
  i-p1-client-returns                          i-p4-signature-status             i-p5-list-documents
  i-p1-settlement-reporting                    i-p4-docusign-webhook             i-p5-delete-document
  i-p1-readonly-api-key                        i-p4-onboarding-workflow          i-p5-upload-completion-webhook
  i-p1-historical-performance
       |
       v (QG gate: client-reporting-api Phase 1 endpoints pass)
Phase 2: Invoicing (SEQUENTIAL)              Phase 3: MiFID Compliance (PARALLEL)
  i-p2-invoice-generation                      i-p3-trade-reporting
  i-p2-invoice-templates                       i-p3-position-monitoring
  i-p2-invoice-delivery                        i-p3-best-execution
  i-p2-invoice-listing                         i-p3-regulatory-umbrella
  i-p2-billing-cycle                           i-p3-compliance-dashboard
  i-p2-fee-calculation                         i-p3-regulatory-filing
       |                                             |
       └─────────────────────┬───────────────────────┘
                             v (QG gate: all Phase 2-5 items pass)
Phase 6: Mock Data + QG (SEQUENTIAL)
  i-p6-seed-mock-data
  i-p6-mock-doc-uploads
  i-p6-qg
  i-p6-sit-tests
```

## Parallelization Strategy

- **Phase 0** is maximally parallel: 4 infrastructure items in UIC/UCI are independent
- **Phases 1, 4, 5** run in parallel after Phase 0 (reporting, DocuSign, document routes are independent)
- **Phases 2, 3** run in parallel after Phase 1 (invoicing and compliance are independent)
- **Phase 6** is sequential after all other phases

## Success Criteria

| Phase | Gate | Criteria                                                                                      |
| ----- | ---- | --------------------------------------------------------------------------------------------- |
| 0     | C4   | DocumentMetadata + DocumentCategory in UIC, pre-signed URL helpers in UCI, QG pass            |
| 1     | C4   | P&L, returns, settlement endpoints working in mock mode, read-only API key auth functional    |
| 2     | C4   | Invoice generation creates PDF, delivery stores document + notifies, listing returns invoices |
| 3     | C4   | MiFID II fields populated, best execution report generates, compliance dashboard data ready   |
| 4     | C4   | DocuSign envelope creation works (mock), webhook updates document status                      |
| 5     | C4   | Upload/download pre-signed URLs generated, document CRUD functional, entitlement-scoped       |
| 6     | C5   | quality-gates.sh passes, SIT tests for upload/download flow pass                              |

## Plan File References

| Plan | File                                         | Slug                           |
| ---- | -------------------------------------------- | ------------------------------ |
| I    | `plan_i_client_reporting_docs_2026_03_21.md` | `plan-i-client-reporting-docs` |
