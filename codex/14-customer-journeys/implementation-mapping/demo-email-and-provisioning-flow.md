---
doc_type: codex-ssot
title: Demo Email and Provisioning Flow
summary:
  Semi-automated sales demo-to-provisioning flow — booking confirmation, persona selection via the decision matrix,
  user-management-ui demo-user creation, welcome email, and pre-session verify; enumerates the manual steps Stage 3E
  automates.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [demo, provisioning, sales, persona, onboarding, staging, automation]
related:
  [
    ../demo-ops/account-intelligence-record.md,
    ../demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    ../demo-ops/demo-restriction-profiles.md,
  ]
created: 2026-04-20
authoritative_for: [demo booking-to-provisioning flow (sales -> demo user -> welcome email)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/implementation-mapping/README.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/shared-core/org-fund-client-entity-model.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Demo Email and Provisioning Flow

> How a sales "book demo" click flows to user-management-ui provisioning + welcome email. Current state described; Stage
> 3E specifies what to build for end-to-end automation.

## Current state

Semi-automated. A sales person books a demo for a prospect; provisioning runs with manual steps between the calendar
booking and the demo user sign-in.

### Step 1 — Demo booking confirmed

Sales person confirms the demo date with the prospect. The confirmation:

- Creates / updates the account-intelligence record (see
  [`../demo-ops/account-intelligence-record.md`](../demo-ops/account-intelligence-record.md)).
- Sets `next_commitment_named` with the session date.
- Triggers the provisioning workflow.

### Step 2 — Persona selection

Sales person consults the demo decision matrix (see
[`../demo-ops/demo-decision-matrix.md`](../demo-ops/demo-decision-matrix.md)) to identify the persona fixture that
matches the resolved commercial path.

### Step 3 — User-management-ui provisioning

Sales person uses user-management-ui to create a demo user:

- Firm name: prospect's organisation.
- Primary contact: prospect's contact.
- Persona fixture: from step 2.
- Entitlement profile: matching the persona's restriction profile.
- Scope (venues / chains / instrument-types): from the account-intelligence record.
- Demo mode: from the decision matrix.
- Staging environment: `odum-research.co.uk` Firebase project.

The user-management-ui writes to the staging entitlement registry and provisions Firebase staging credentials.

Reference:
[`../../../plans/ai/user_management_merge_2026_03_23.plan.md`](../../../plans/ai/user_management_merge_2026_03_23.plan.md)
tracks the user-management-ui build.

### Step 4 — Welcome email

The provisioning triggers a welcome email to the prospect's primary contact with:

- The staging URL (`odum-research.co.uk`).
- The sign-in credentials (Firebase staging — typically magic-link).
- The demo session date + time + sales-person contact.
- A short note framing the session ("We'll meet in the demo environment for 45 minutes on [date]").

Email template is curated per path (IM / Reg Umbrella / DART) with the rule-02 calm tone. Template library lives in
Odum's sales tooling.

### Step 5 — Pre-session verify

Sales person signs into staging as the demo user 15–30 minutes before the session to:

- Verify restriction profile rendering matches expectations.
- Verify demo data renders sensibly for the scope.
- Verify LOCKED-VISIBLE surfaces show the correct upgrade-path message.
- Walk one end-to-end path to catch any routing issues.

### Step 6 — Session

Prospect signs in; demo runs. Session outcome captured per
[`../demo-ops/meeting-history-and-interest-tracking.md`](../demo-ops/meeting-history-and-interest-tracking.md).

### Step 7 — Post-session

If the prospect advances to commercial close, the demo user is retained for potential diligence-depth sessions. If the
prospect stalls, the post-demo follow-up orchestration triggers (see
[`../demo-ops/post-demo-followup-orchestration.md`](../demo-ops/post-demo-followup-orchestration.md)).

## Manual steps in the current flow

Steps that require human intervention:

- **Persona selection** — sales person reads the decision matrix.
- **Entitlement profile attach** — sales person picks from the profile library.
- **Scope entry** — sales person transcribes from the account-intelligence record.
- **Email tone** — sales person reviews the template before send.
- **Pre-session verify** — manual walk-through.

## What Stage 3E should automate

Named items in the Stage 3E refactor plan:

- **One-click provisioning from calendar booking.** Calendar → account-intelligence-record → persona auto-selection (via
  decision matrix) → user-management-ui invocation → welcome email. Entirely automated for the standard cases; sales
  person reviews before send.
- **Profile library UI.** The profile library is browsable and attachable at provisioning time; currently it's a
  developer-managed dataset.
- **Scope inference from the record.** The account-intelligence record already has `market_scope`; automation reads it
  directly rather than requiring sales-person transcription.
- **Pre-session verify automation.** A pre-session Playwright smoke test runs against the provisioned demo user and
  reports any rendering / routing issues before the session.
- **Email template orchestration.** Templates are selected per persona + path; tone is validated against rule-02
  guardrails before send.

Until Stage 3E lands, the flow is semi-automated as described.

## Error modes

- **Profile not rendering correctly.** Pre-session verify catches this. If missed, sales person aborts the demo at
  session start and reschedules.
- **Welcome email bounces.** Sales follow-up with manual credential hand-off.
- **Demo data stale.** The staging environment's demo seed should be refreshed per the
  [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md) expectations; stale data is
  escalated to the demo-ops team for re-seed.
- **Persona entitlement leak.** If the prospect can see a surface they shouldn't, this is a rule-06 violation logged to
  the account-intelligence record's `deviations_logged` and to the compliance audit trail.

## Cross-references

- [`../demo-ops/account-intelligence-record.md`](../demo-ops/account-intelligence-record.md) — record lifecycle
- [`../demo-ops/demo-decision-matrix.md`](../demo-ops/demo-decision-matrix.md) — persona selection
- [`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md) — profile library
- [`../demo-ops/post-demo-followup-orchestration.md`](../demo-ops/post-demo-followup-orchestration.md)
- [persona-and-user-prototype-mapping.md](persona-and-user-prototype-mapping.md) — persona fixtures
- [route-mapping.md](route-mapping.md) — routes to verify pre-session
- [`../authentication/firebase-staging.md`](../authentication/firebase-staging.md) — Firebase staging auth
- [`../../../plans/ai/user_management_merge_2026_03_23.plan.md`](../../../plans/ai/user_management_merge_2026_03_23.plan.md)
  — user-management-ui build
