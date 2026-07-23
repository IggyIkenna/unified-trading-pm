---
doc_type: plan
title: ────────────────────────────────────────────────────────────────────────────
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
---

---

name: reg-umbrella-questionnaire-and-onboarding-docs-2026-04-21 overview: Extend the existing `/questionnaire` with a
Reg-Umbrella branch (7 new axes — licence region, 3mo/1yr/2yr targets, own-MLRO, entity geography, supported
currencies); gate the whole page behind the briefings access-code; wire submissions to the admin org detail view so
per-org answers are visible alongside their docs. Swap the local-disk onboarding doc handlers for GCS writes in non-demo
/ non-dev environments, rename `/reset` to a per-doc delete with confirmation, and add a Documents section to
`/admin/organizations/[id]` with View / Download / Delete-with-confirm. Operator directive 2026-04-21 — "one schema, one
questionnaire". Feeds directly into the admin panel so we can review the organisation's answers + uploaded
KYC/AML/licence docs in one surface.

type: mixed epic: epic-code-completion status: active locked_by: live-defi-rollout locked_since: 2026-04-21

completion_gates: code: C5 deployment: D0 business: none

repo_gates:

- repo: unified-api-contracts code: C0 deployment: none business: none
- repo: unified-trading-system-ui code: C0 deployment: D0 business: none
- repo: unified-trading-pm code: C0 deployment: none business: none

depends_on: []

# ────────────────────────────────────────────────────────────────────────────

# CONTEXT + PRE-AUDIT

# ────────────────────────────────────────────────────────────────────────────

#

# User directive 2026-04-21: "one schema, like one questionnaire, makes complete

# sense to me. And obviously, when someone fills out the questionnaire, that

# should feed back to the admin thing so that we can see, for that organisation

# that signed up, what their answers are. We have a record."

#

# Current state (pre-audit):

#

# UAC — unified-api-contracts

# - `internal/architecture_v2/restriction_profiles.py` defines:

# \* QuestionnaireCategory (CeFi/DeFi/TradFi/Sports/Prediction)

# \* QuestionnaireInstrumentType (spot/perp/dated_future/option/lending/staking/lp/event_settled)

# \* QuestionnaireStrategyStyle (8 styles)

# \* QuestionnaireServiceFamily (IM/DART/RegUmbrella/combo)

# \* QuestionnaireFundStructure (SMA/Pooled/NA)

# \* QuestionnaireResponse (BaseModel, frozen=True, extra="forbid", 6 required axes)

# \* \_apply_questionnaire_override + resolve_restriction_profile (overlay logic)

# - `internal/architecture_v2/__init__.py` re-exports all of the above.

# - `internal/architecture_v2/tempt_logic.py` imports QuestionnaireResponse +

# QuestionnaireCategory for upsell-gating logic.

#

# UI — unified-trading-system-ui

# - `app/(public)/questionnaire/page.tsx` — 6-axis form, localStorage (dev) / Firestore `/questionnaires` (prod).

# - `app/(ops)/admin/questionnaires/page.tsx` — admin playback; lists docs from Firestore.

# - `app/(ops)/admin/organizations/[id]/page.tsx` — org detail; has `status === "onboarding"` branch but NO

# questionnaire-response section, NO documents section today.

# - `app/api/onboarding/{upload,download,reset}/route.ts` — local-disk mock handlers writing to

# `.local-dev-cache/onboarding-docs/{org_id}/{app_id}/{doc_type}.ext`. Upload returns a fake

# `gs://onboarding-docs/...` path showing the intent was always GCS.

# - `components/briefings/briefing-access-gate.tsx` — reusable access-code gate (env-var:

# NEXT_PUBLIC_BRIEFING_ACCESS_CODE). Session stored via isBriefingSessionActive().

# - `lib/questionnaire/types.ts` — manual TS mirror of UAC schema (drift-risk note at top).

# - `lib/questionnaire/submit.ts` — submitQuestionnaire() sink (localStorage vs Firestore).

# - `lib/questionnaire/resolve-persona.ts` — 6-axis → persona mapper.

# - `lib/api/mock-handler.ts` — short-circuits `/api/onboarding/*` to let route handlers serve.

# - `lib/visibility/use-tile-lock-state.ts` — G1.10 tile-widening consumer (reads localStorage key).

#

# Tests

# - `tests/e2e/playbooks/refactor/refactor-g1-10-questionnaire.spec.ts` — e2e that reads localStorage key.

# - `tests/e2e/playbooks/refactor/refactor-g1-13-upsell-tempt-logic.spec.ts` — e2e consumer.

# - `__tests__/scripts/orphan-audit.test.ts` — unrelated (scanner tests).

#

# Pre-audit manifest (consumers that must still build after extension):

# - UAC `tempt_logic.py` — imports QuestionnaireResponse + QuestionnaireCategory (no new axes → no break).

# - UAC `restriction_profiles.py::_apply_questionnaire_override` — overlay logic reads 3 axes today; new axes are

# optional with safe defaults → no behaviour change.

# - UI `resolve-persona.ts` — reads 4 axes (service_family, fund_structure, categories, instrument_types) → new axes

# optional → no break.

# - UI `use-tile-lock-state.ts` — reads via persisted payload; new axes optional → no break.

# - UI e2e specs — assert on localStorage KEY + known shape; safe if new fields are additive + optional.

# - Admin `/admin/questionnaires` — Firestore reader; if payload gets new fields, admin UI can ignore or display them

# progressively.

#

# Risk calls:

# - **Extension must be additive + optional (Pydantic `Field(default=...)`)** — tempt_logic and other downstream

# readers must not break on responses authored before this plan.

# - **Reg-Umbrella branch is conditionally rendered** (service_family ∈ {RegUmbrella, combo}) — unconditional widening

# would force every prospect through 7 extra questions, breaking the "only ask what's needed" UX.

# - **Access-code gate**: move questionnaire from fully public to access-code gated. This changes the orphan-audit

# landscape — the page is still reachable (from contact-flow / regulatory CTA), just not anonymously.

# Update /admin/questionnaires playback to show access-code session metadata (if captured).

# - **Storage swap (Phase 4)** is orthogonal to Phases 1-3; can be shipped independently if phases 1-3 converge first.

# - **UAC version bump**: adding optional fields to a frozen BaseModel is a MINOR bump pre-1.0.0 (semver-agent

# handles); no human approval needed. Commit prefix: `feat:`.

#

# Dependency graph (phases):

#

# Phase 1 (UAC + TS types, SEQUENTIAL, P0)

# │

# ├──► Phase 2 (UI questionnaire branch + access-gate, P0)

# │ │

# │ └──► Phase 3 (admin org questionnaire section, P0)

# │

# └──► Phase 4 (onboarding docs GCS + admin doc panel, PARALLEL with Phase 2-3, P1)

#

# Phase 5 (codex + QG + closeout, SEQUENTIAL after all others)

#

# ────────────────────────────────────────────────────────────────────────────

todos:

# ──────────────────────────────────────────────────────────────────────

# PHASE 1 — UAC schema extension + TS mirror (SEQUENTIAL, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p1-uac-reg-umbrella-fields content: |
  - [x] [AGENT] P0. Extend
        `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py` with 7 new
        optional Reg-Umbrella fields on `QuestionnaireResponse`: _ `licence_region: LicenceRegion | None = None` —
        Literal["EU_only", "UK_only", "EU_or_UK", "EU_and_UK", "other"] _ `targets_3mo: str | None = None` — free-text
        AUM/revenue/headcount target for first 3 months _ `targets_1yr: str | None = None` — same, for end-of-year-1 _
        `targets_2yr: str | None = None` — same, for end-of-year-2 _ `own_mlro: bool | None = None` — will the firm
        supply its own MLRO (True) vs consume Odum's (False/None) _ `entity_jurisdiction: str | None = None` — ISO
        country code or free-text for the operating entity \* `supported_currencies: tuple[str, ...] = ()` — ISO 4217
        codes (USD, EUR, GBP, …) Add `LicenceRegion = Literal[...]` alongside the existing literal types. Ensure
        `ConfigDict(extra="forbid")` still holds (the new fields are whitelisted). Re-export from
        `internal/architecture_v2/__init__.py`. Keep `frozen=True`. status: pending

- id: p1-uac-tests content: |
  - [x] [AGENT] P0. Add unit tests under `unified-api-contracts/tests/internal/architecture_v2/` covering: _
        QuestionnaireResponse accepts the new fields with explicit values. _ QuestionnaireResponse accepts a payload
        OMITTING the new fields (default/None/empty tuple). \* `_apply_questionnaire_override` behaviour is unchanged
        when the new fields are present (regression guard). status: pending

- id: p1-uac-qg content: |
  - [x] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh` — full green (pytest + basedpyright +
        ruff). Then
        `bash scripts/quickmerge.sh "feat: add reg-umbrella axes to QuestionnaireResponse" --agent --files     "unified_api_contracts/internal/architecture_v2/restriction_profiles.py unified_api_contracts/internal/architecture_v2/__init__.py tests/internal/architecture_v2/test_restriction_profiles.py"`.
        status: done

- id: p1-ts-mirror content: |
  - [x] [AGENT] P0. Mirror the 7 new fields in `unified-trading-system-ui/lib/questionnaire/types.ts`: _ Add
        `QuestionnaireLicenceRegion` type alias + const array. _ Extend `QuestionnaireResponse` with all 7 new fields
        matching the UAC optional shape (string | null / boolean | null / readonly string[]). \* Update the top-of-file
        SSOT comment listing (QuestionnaireLicenceRegion + the 7 field names). status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 2 — /questionnaire UI: Reg-Umbrella branch + access-gate (P0)

# Blocked by: p1-ts-mirror

# ──────────────────────────────────────────────────────────────────────

- id: p2-conditional-reg-umbrella-branch content: |
  - [x] [AGENT] P0. Extend `app/(public)/questionnaire/page.tsx` form state with the 7 new Reg-Umbrella fields. Render a
        conditional "Regulatory Umbrella details" section ONLY when `service_family ∈ {RegUmbrella, combo}`. Sections
        (each a clearly labelled group in the existing form style): 1. Fund structure preference (already exists —
        reuse). 2. Instrument types + categories (already exist — reuse). 3. NEW: Licence region preference
        (LicenceRegion radio group). 4. NEW: Entity jurisdiction (text input with ISO-2 hint + placeholder). 5. NEW:
        Supported currencies (multi-select from common 4217 list: USD, EUR, GBP, CHF, AUD, CAD, SGD, JPY, HKD, AED +
        "Other / add"). 6. NEW: Own-MLRO Y/N (boolean radio; default None with tooltip — "Leave blank if Odum's MLRO
        covers you"). 7. NEW: Business targets (three free-text textareas for 3mo / 1yr / 2yr). Persist-to-submit flow
        unchanged (same buildResponse → submitQuestionnaire pipeline). status: pending

- id: p2-access-gate content: |
  - [x] [AGENT] P0. Wrap `/questionnaire` in the existing `<BriefingAccessGate>` from
        `components/briefings/briefing-access-gate.tsx` so the page is no longer anonymously-accessible. Share the
        briefing-session key (already set via `setBriefingSessionActive`) so a prospect who unlocked `/briefings/*` does
        not get re-prompted. Update the page header copy to mention "Invite-only questionnaire". status: pending

- id: p2-org-association content: |
  - [x] [AGENT] P0. Capture `org_id` (or the email/firm name if anonymous) with each submission. (a) Extend
        `QuestionnaireResponse` submission payload at write-time (not schema) with
        `submitted_by: { email, firm_name, access_code_fingerprint }` — write via `submitQuestionnaire` helper. (b) When
        submitting to Firestore (`/questionnaires` collection), include this envelope so admin can later pivot from
        org-email → questionnaire doc. Do NOT store PII beyond email + firm name + access-code hash. (c) Fallback for
        dev/localStorage path: write to `questionnaire-response-v1` as today PLUS `questionnaire-envelope-v1` (new key)
        with the submitted_by envelope. status: pending

- id: p2-ui-tests content: |
  - [x] [AGENT] P0. Unit tests (vitest) for: _ Conditional branch renders only when service_family ∈ {RegUmbrella,
        combo}. _ Access-gate passes through when session is already active. \* Envelope payload includes submitted_by
        email/firm_name. Place tests in `__tests__/app/questionnaire/` matching existing test layout. status: pending

- id: p2-qg content: |
  - [x] [SCRIPT] P0. `cd unified-trading-system-ui && npx tsc --noEmit` + `CI=true npm test -- --run` +
        `npm run     orphan-audit` → all green + 0 new orphans. Then quickmerge with explicit `--files` naming only the
        edited files. status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 3 — Admin org integration (P0, blocked by Phase 2)

# ──────────────────────────────────────────────────────────────────────

- id: p3-admin-org-questionnaire-section content: |
  - [x] [AGENT] P0. Extend `app/(ops)/admin/organizations/[id]/page.tsx` with a new "Questionnaire" Card underneath the
        existing org summary. Fetch the questionnaire response for this org from Firestore `/questionnaires` collection
        filtered by `submitted_by.email` or `submitted_by.firm_name` (match to the org's `contact_email` / `name`).
        Render the six original axes + the seven new Reg-Umbrella axes as a clean definition-list. Show "No
        questionnaire on file" when empty (don't 404). status: pending

- id: p3-admin-cross-link content: |
  - [x] [AGENT] P0. Add a cross-link from `app/(ops)/admin/questionnaires/page.tsx` row actions: each row gets a "View
        org" button linking to `/admin/organizations/{org_id}` when the envelope's email matches an organisation. No
        change to the questionnaires list itself — this is a pure navigation affordance. status: pending

- id: p3-admin-tests content: |
  - [x] [AGENT] P0. Vitest cases covering the new section: renders the full axis table, handles missing-response state,
        handles missing firestore client gracefully (mock mode). status: pending

- id: p3-qg content: |
  - [x] [SCRIPT] P0. Repo QG green (tsc + vitest + orphan-audit). Quickmerge. status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 4 — Onboarding docs cloud storage + admin doc panel (P1, PARALLEL with Phase 2-3)

# ──────────────────────────────────────────────────────────────────────

- id: p4-upload-gcs-adapter content: |
  - [x] [AGENT] P1. Refactor `app/api/onboarding/upload/route.ts` to use a `resolveDocStore()` dispatcher: _
        `CLOUD_MOCK_MODE=true` OR `NODE_ENV=development` → local-disk path (current behaviour, but under
        `.local-dev-cache/onboarding-docs/{org_id}/{app_id}/{doc_type}.ext`). _ Otherwise → write to GCS bucket
        `odum-${ENVIRONMENT}-onboarding-docs` (ENVIRONMENT ∈ {staging, prod}). Use `@google-cloud/storage`; ADC
        credentials (no hardcoded keys). Response shape unchanged: `{ ok, local_path?, gcs_path, file_name, size }`.
        Local mock still reports the canonical
        `gs://odum-${ENVIRONMENT}-onboarding-docs/{org_id}/{app_id}/{doc_type}.ext` path in the response so downstream
        callers get consistent URIs. status: pending

- id: p4-download-gcs-adapter content: |
  - [x] [AGENT] P1. Refactor `app/api/onboarding/download/route.ts` with the same `resolveDocStore()` split. Cloud path
        streams from GCS; local path behaves as today. Keep Content-Type inference + Content-Disposition headers; stream
        bytes rather than buffering whole files on GCS path (use a Readable-from-GCS pattern). status: pending

- id: p4-rename-reset-to-delete content: |
  - [x] [AGENT] P1. Delete the current `/api/onboarding/reset/route.ts` nuke-all handler. Create a new
        `/api/onboarding/docs/delete/route.ts` (POST) accepting `{ org_id, application_id, doc_type, confirm_token }` —
        confirm_token must match a short-lived server-generated token echoed by the admin UI (or at minimum, validate
        that the caller has admin entitlement via the existing auth middleware). Delete that one object from local disk
        or GCS as appropriate. Return `{ ok: true, deleted_path }`. status: pending

- id: p4-admin-documents-section content: |
  - [x] [AGENT] P1. Extend `app/(ops)/admin/organizations/[id]/page.tsx` with a "Documents" Card listing every
        onboarding doc on file for this org. Each row: doc_type + filename + uploaded-at + View (opens /api/onboarding/
        download with the correct query params) + Download (same endpoint, `?download=1`) + Delete (opens a confirmation
        dialog that requires typing the org's name or "DELETE" literal before firing the new delete endpoint). Use
        existing Card/Table/Button/AlertDialog primitives from components/ui/. status: pending

- id: p4-admin-documents-list-endpoint content: |
  - [x] [AGENT] P1. Add `/api/onboarding/docs/list/route.ts` (GET, `?org_id=...`) that returns the list of docs on file
        for that org (filename, doc_type, size, uploaded_at). Implementation mirrors the upload/download split
        (local-disk readdir vs GCS list). This powers the admin Documents section. status: pending

- id: p4-onboarding-tests content: |
  - [x] [AGENT] P1. Vitest cases covering the mock-mode vs cloud-mode dispatch (mock Web3? no, mock
        `@google-cloud/     storage` via vitest.mock). Also cover the delete-flow: missing confirm_token → 403;
        mismatched token → 400; happy path → 200 + file gone. status: pending

- id: p4-qg content: |
  - [x] [SCRIPT] P1. Repo QG green (tsc + vitest + orphan-audit — note: the 3 /api/onboarding whitelist entries get
        updated paths or removed if the new routes are genuinely called from the admin UI). Quickmerge. status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 5 — Codex + closeout (P1, SEQUENTIAL after Phases 1-4)

# ──────────────────────────────────────────────────────────────────────

- id: p5-codex-questionnaire-flow content: |
  - [x] [AGENT] P1. Create `/codex/08-workflows/prospect-questionnaire-flow.md` documenting: _ The 13-axis questionnaire
        (6 base + 7 reg-umbrella conditional) and its SSOT position in UAC. _ The access-code gate + session-sharing
        with /briefings. _ The admin playback loop: prospect submits → Firestore writes → /admin/organizations/{id} +
        /admin/ questionnaires surfaces show the response. _ The Phase 4 onboarding-doc flow: upload to GCS (prod) /
        local-disk (mock) → admin sees per-org list + can View/Download/Delete-with-confirm. status: pending

- id: p5-workspace-qg-sweep content: |
  - [x] [SCRIPT] P1. Workspace QG across all 3 touched repos (unified-api-contracts + unified-trading-system-ui +
        unified-trading-pm) in that dependency order. All green before declaring this plan complete. status: pending

- id: p5-plan-closeout content: |
  - [x] [AGENT] P1. Flip every todo in this plan to `status: done`. Leave `locked_by: live-defi-rollout` in place; ask
        the human to run `[unlock-plan]` when ready to archive. status: pending

# ────────────────────────────────────────────────────────────────────────────

# SUCCESS CRITERIA

# ────────────────────────────────────────────────────────────────────────────

# - `QuestionnaireResponse` in UAC carries all 7 new Reg-Umbrella axes + stays backwards-compatible with payloads

# authored before this plan.

# - `/questionnaire` renders the Reg-Umbrella branch only when service_family ∈ {RegUmbrella, combo}; gate required.

# - `/admin/organizations/{id}` shows the full 13-axis response + per-org document list + per-doc Delete-with-confirm.

# - Onboarding doc uploads land in `gs://odum-${env}-onboarding-docs/...` in staging/prod; local disk only in mock/dev.

# - `/api/onboarding/reset` deleted; `/api/onboarding/docs/delete` + `/api/onboarding/docs/list` exist and are wired

# into the admin UI. Orphan-audit stays clean.

# - All three affected repos pass QG end-to-end; workspace QG sweep green on the final closeout pass.

# ────────────────────────────────────────────────────────────────────────────
