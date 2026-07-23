---
doc_type: codex-ssot
title: Prospect Questionnaire & Onboarding-Docs Flow
summary: >-
  SSOT for the prospect questionnaire (UAC QuestionnaireResponse — 6 base + 7 Reg-Umbrella axes), its briefings-gate
  access path, the admin playback loop, and the onboarding-docs DocStore (local vs GCS backend) upload/download/delete
  flow.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, sales]
tags: [questionnaire, onboarding, uac, ui, mvp]
related:
  [
    ./signup-signin-workflow.md,
    ./client-onboarding.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
  ]
created: 2026-04-21
authoritative_for:
  [prospect questionnaire schema (13-axis QuestionnaireResponse) + onboarding-docs DocStore upload/delete flow]
referenced_by:
  [
    /codex/02-data/questionnaire-axes.md,
    /codex/08-workflows/client-onboarding.md,
    /codex/08-workflows/platform-walkthrough-and-demo-context.md,
    /codex/08-workflows/signup-signin-workflow.md,
    /codex/09-strategy/architecture-v2/strategy-questionnaire-mapping.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Prospect Questionnaire & Onboarding-Docs Flow

> **Status:** canonical (2026-04-21) **Owner:** UI Architecture **SSOT for:**
> `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py::QuestionnaireResponse`,
> `unified-trading-system-ui/app/(public)/questionnaire/page.tsx`,
> `unified-trading-system-ui/app/(ops)/admin/questionnaires/page.tsx`,
> `unified-trading-system-ui/app/(ops)/admin/organizations/[id]/page.tsx`,
> `unified-trading-system-ui/lib/onboarding/doc-store.ts`,
> `unified-trading-system-ui/app/api/onboarding/{upload,download,docs/list,docs/delete}/route.ts`. **Plan:**
> [`plans/archive/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md`](../../plans/archive/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md)

---

## §1 — The problem

Prospects landing on Odum have three decisions to make: (a) which service family fits (IM / DART / Reg Umbrella /
combo), (b) how to express their existing preferences about venues, instruments, strategy style, and fund structure, and
(c) for Reg-Umbrella specifically, the regulatory posture of their firm (licence region, own-MLRO vs consume Odum's,
entity jurisdiction, operating currencies, 3mo/1yr/2yr business targets). Before 2026-04-21 we only asked the first 6
axes; Reg-Umbrella prospects had to finish the questionnaire and then schedule a call to relay everything else. The call
has now been folded into the form.

> **Naming convention (added 2026-04-26):** the `service_family` enum values (`IM` / `DART` / `RegUmbrella` / `combo`)
> are code-level identifiers and stay unchanged. The marketing display labels surfaced to prospects on public pages and
> questionnaire copy are: `IM` → **Odum-Managed Strategies**, `DART` → **DART Trading Infrastructure**, `RegUmbrella` →
> **Regulated Operating Models**. Public-facing questionnaire copy must use the marketing labels; admin / signup /
> contract surfaces continue to use the legal labels (Investment Management / DART / Regulatory Umbrella). See
> `signup-signin-workflow.md` §2.7.2 for the full mapping.

> **Access context (added 2026-04-26 late):** the questionnaire lives in the **public / gated education** context — the
> first of three contexts in the prospect-to-client journey (public → controlled demo/UAT → production). On submit, the
> form writes its envelope + computes a `catalogue_seed` (Funnel Coherence plan Workstream E5), persists both to
> Firestore and localStorage, and redirects the prospect to `/briefings`. **The questionnaire submit MUST NOT redirect
> public users to `/services/*`** — signed-in / demo-UAT surfaces are reached only after Strategy Review issues a
> demo-session magic link or after signup. See `signup-signin-workflow.md` §1 (three-context access model) and
> `platform-walkthrough-and-demo-context.md` for the demo/UAT entry-point.

Once signed up, every prospect uploads regulatory / legal / compliance documents. Those previously wrote to local disk
in both mock and prod (the handler ignored environment) — clearly wrong for staging + prod, where we need durable cloud
storage + an admin-visible per-org list + a sensible delete path.

---

## §2 — The schema

Single schema, 13 axes, in **one place**: UAC's `QuestionnaireResponse` Pydantic model. 6 base axes are required; 7
Reg-Umbrella axes are optional and only collected when `service_family ∈ {RegUmbrella, combo}`.

| Axis                            | Required | Values                                                                          |
| ------------------------------- | -------- | ------------------------------------------------------------------------------- |
| `categories`                    | ✓        | tuple ∈ {CeFi, DeFi, TradFi, Sports, Prediction}                                |
| `instrument_types`              | ✓        | tuple ∈ {spot, perp, dated_future, option, lending, staking, lp, event_settled} |
| `venue_scope`                   | ✓        | `"all"` sentinel OR tuple of venue ids                                          |
| `strategy_style`                | ✓        | tuple ∈ 8 styles                                                                |
| `service_family`                | ✓        | ∈ {IM, DART, RegUmbrella, combo}                                                |
| `fund_structure`                | ✓        | ∈ {SMA, Pooled, NA}                                                             |
| `licence_region`                | —        | ∈ {EU_only, UK_only, EU_or_UK, EU_and_UK, other} or `None`                      |
| `targets_3mo` / `_1yr` / `_2yr` | —        | free-text or `None`                                                             |
| `own_mlro`                      | —        | `True` (own MLRO) / `False` (consume Odum's) / `None` (unsure)                  |
| `entity_jurisdiction`           | —        | ISO-2 country code or free text or `None`                                       |
| `supported_currencies`          | —        | tuple of ISO-4217 codes (empty tuple allowed)                                   |

**Extension rule:** The 7 optional axes were added 2026-04-21 and must stay backwards-compatible. Responses authored
earlier validate with the new fields defaulting to `None` / `()`. `_apply_questionnaire_override` overlay logic (persona
resolution + tile-lock widening) reads the 6 base axes only; Reg-Umbrella axes surface in admin UI, not persona
resolution.

---

## §3 — Questionnaire IS the access path (post 2026-04-25)

**Inverted relationship:** the questionnaire is no longer wrapped in `<BriefingAccessGate>`. The opposite is now true —
`<BriefingAccessGate>` (which wraps `/briefings/*`, `/docs`, `/our-story`, `/faq`) **embeds** the questionnaire form
inline as its primary access path. The standalone `/questionnaire` page is public and ungated, mounting the same
reusable `<QuestionnaireForm />` component.

Mechanics on submit (both standalone-page and embedded-on-gate paths):

1. Firestore `/questionnaires/{id}` write (or localStorage `questionnaire-response-v1` in dev mock mode).
2. `setBriefingSessionActive()` — writes `localStorage.odum-briefing-session = "1"`. One unlock covers every Deep Dive
   route in the same browser.
3. `POST /api/questionnaire/email` — fire-and-forget. To: prospect, BCC: `info@odum-research.com`. Body carries the
   global access code (for return visits / second device), a numbered "Next steps" block (read briefings → book 30-min
   Calendly call → submit Strategy Evaluation DDQ to unlock Sandbox demo), Deep Dive tour list, and the questionnaire
   echo table.
4. `router.push(returnPath)` after 1.2s. Priority: `returnPath` prop (set by gate) > `?return=` URL param (relative
   only) > `/briefings`.

The form lives at
[components/questionnaire/questionnaire-form.tsx](unified-trading-system-ui/components/questionnaire/questionnaire-form.tsx)
and accepts `returnPath?: string` + `compact?: boolean` props. **Never inline-duplicate this form** — mount the
component in any new host that needs it.

Each submission carries an envelope:

```ts
interface QuestionnaireEnvelope {
  email: string; // work email (free text)
  firm_name: string; // prospect's firm
  access_code_fingerprint: string; // hex SHA-256 of the access code (if any was previously cached)
}
```

The fingerprint is not the code — just a digest, so the admin panel can bucket responses by cohort (e.g. "everyone who
unlocked with the Q2-investor-demo code") without storing plain codes. If SubtleCrypto is unavailable (older runtime)
the fingerprint is the empty string and the envelope still identifies the prospect by email + firm. **Note:**
fingerprint will commonly be empty now since most cold-inbound prospects fill the questionnaire BEFORE having a code.

For the canonical mechanism + the secondary "I already have an access code" disclosure path on the gate, see
[`/codex/14-customer-journeys/authentication/light-auth-briefings.md`](/codex/14-customer-journeys/authentication/light-auth-briefings.md).

---

## §4 — The admin playback loop

```
 ┌─────────────────────────────────────────┐    ┌──────────────────────────┐
 │  Entry channel A — questionnaire on      │    │  Entry channel B —        │
 │  Deep Dive lock screen:                   │    │  standalone page:         │
 │  /briefings/* | /docs | /our-story | /faq │    │  /questionnaire           │
 │  → <BriefingAccessGate> embeds form       │    │  (public, ungated)        │
 └────────────────┬────────────────────────┘    └────────────┬─────────────┘
                  │                                            │
                  └───────────────────┬────────────────────────┘
                                      │ submit (same QuestionnaireForm component)
                                      ▼
            ┌──────────────────────────────────────────────────┐
            │  Side effects (in order):                          │
            │  1. Firestore /questionnaires/{id} write           │
            │     (or localStorage in dev mock mode)             │
            │  2. setBriefingSessionActive() → localStorage flag │
            │  3. POST /api/questionnaire/email (fire-and-forget)│
            │     To: prospect; BCC: info@odum-research.com.     │
            │     Body: code + Next-steps block + tour list      │
            │     + questionnaire echo table.                    │
            │  4. router.push(returnPath) after 1.2s             │
            └─────────────────────────┬─────────────────────────┘
                                      ▼
            ┌──────────────────────────────────────────────────┐
            │  /admin/questionnaires  (list, all rows)          │
            │  — sortable, cross-link "View org" per row        │
            └────────────────┬─────────────────────────────────┘
                             ▼
            ┌──────────────────────────────────────────────────┐
            │  /admin/organizations/[id]                        │
            │    · Prospect questionnaire card                  │
            │      (13 axes when Reg-Umbrella)                  │
            │    · Documents card (list + View / Download       │
            │      / Delete-with-confirm)                       │
            │    · Members · Venue API keys · Reports           │
            └──────────────────────────────────────────────────┘
```

Join rule: `OrgQuestionnaireSection` queries Firestore `/questionnaires` filtered by
`submitted_by.email == org.contact_email` (primary) or `submitted_by.firm_name == org.name` (fallback). Mock mode shows
a friendly "Firebase not configured" message instead of crashing.

### §4a — Email-back funnel framing (post 2026-04-25)

The post-submit email is the **primary funnel nudge**. It carries (in order):

1. **Greeting + access code** — boxed, copy-pasteable. For return visits / second device.
2. **Next steps** — numbered block:
   - Read the Deep Dive (6 briefings + docs + Our Story + FAQ — all unlocked by the same session).
   - Book a 30-minute walk-through call on Calendly (`https://calendly.com/odum-ikenna`).
   - Submit the Strategy Evaluation pack at `/strategy-evaluation` — required (before or after the call) to unlock the
     curated Sandbox demo at Tier 2.
3. **Deep Dive tour list** — describes what's behind each pillar.
4. **Questionnaire echo table** — every answer the prospect provided (so they have a record).
5. **Reply-to** — `info@odum-research.com` for questions.

Subject line: "Your Deep Dive access — {firm} ({service})" when global code is set; falls through to "Your questionnaire
responses — {firm} ({service})" otherwise.

Sender: `hello@mail.odum-research.com` (prod) / `hello@mail.uat.odum-research.com` (uat) / `onboarding@resend.dev` (dev)
— see [app/api/questionnaire/email/route.ts](unified-trading-system-ui/app/api/questionnaire/email/route.ts).

---

## §5 — The onboarding-docs flow

`lib/onboarding/doc-store.ts` exposes a `DocStore` adapter with two backends picked at request-time by
`resolveDocStore()`:

| Backend             | Selected when                                         | Behaviour                                                                                            |
| ------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `localStore`        | `CLOUD_MOCK_MODE=true` OR `ENVIRONMENT ∈ {dev, test}` | Writes / reads `.local-dev-cache/onboarding-docs/`                                                   |
| `cloudStorageStore` | Otherwise (staging / prod)                            | Uses `@google-cloud/storage` against bucket `odum-${env}-onboarding-docs` with ADC credentials (§5a) |

Canonical `gs://odum-${env}-onboarding-docs/{org}/{app}/{doc}.ext` URIs are always emitted on upload regardless of
backend, so downstream readers (admin UI, analytics) see a stable path.

### §5a Cloud backend — operator setup

The cloud backend ships with `@google-cloud/storage` wired. Before a non-mock environment can serve `/api/onboarding/*`
without errors, the operator must provision:

1. **Bucket exists:** `gsutil mb -p ${GCP_PROJECT} -l europe-west2 gs://odum-${env}-onboarding-docs` (one per env —
   `staging`, `production`). Use uniform bucket-level access; object versioning optional but recommended for regulatory
   docs.
2. **IAM:** grant `roles/storage.objectAdmin` on the bucket to the Cloud Run service account running
   `unified-trading-system-ui`. Avoid project-level grants — keep the blast radius scoped to the single bucket.
3. **Credentials:** the SDK uses ADC. On Cloud Run the attached service account works out of the box. For local admin
   runs, `gcloud auth application-default login` is sufficient. Never ship a service-account JSON file into the image.
4. **Smoke test:** from a staging deployment, POST a small PDF to `/api/onboarding/upload` with test org/app/doc_type →
   GET `/api/onboarding/download` → delete via the admin UI's typed-confirm dialog. Watch Cloud Logging for the
   `ADMIN_DOC_DELETED` structured event (see §8).

The `DocStore` adapter interface is stable — swap backends by setting `CLOUD_MOCK_MODE=true` (falls back to local disk)
without touching call sites.

### §5b REST surface

| Method | Path                          | Body / params                                                   | Returns                                          |
| ------ | ----------------------------- | --------------------------------------------------------------- | ------------------------------------------------ |
| `POST` | `/api/onboarding/upload`      | FormData: `file`, `org_id`, `application_id`, `doc_type`        | `{ ok, local_path?, gcs_path, file_name, size }` |
| `GET`  | `/api/onboarding/download`    | `?org_id=...&application_id=...&doc_type=...`                   | Binary blob, `Content-Disposition: attachment`   |
| `GET`  | `/api/onboarding/docs/list`   | `?org_id=...`                                                   | `{ ok, org_id, docs: DocEntry[] }`               |
| `POST` | `/api/onboarding/docs/delete` | JSON: `{ org_id, application_id, doc_type, confirm: "DELETE" }` | `{ ok: true, deleted_path }` or 403 / 404        |

The literal `"DELETE"` confirm token on `/docs/delete` is a second line of defence against accidental `fetch()` calls
from other admin pages. Real admin auth is enforced upstream by the NextAuth / Firebase middleware on `/admin/*` — if
that middleware fails, the token confirm alone is not a security boundary.

---

## §6 — Orphan-audit interaction

The four `/api/onboarding/*` route handlers do not appear on any nav surface (they're fetched programmatically from the
Documents panel). They are in the orphan-audit whitelist under the `API-HANDLER` category per
[`orphan-audit.md` § Whitelist Triage Rule](/codex/04-architecture/orphan-audit.md#whitelist-triage-rule). Both `list`
and `delete` were added 2026-04-21 alongside this plan. `reset` was deleted (replaced by the per-doc `delete` endpoint).

---

## §8 — Admin audit events

`lib/admin/audit.ts` exposes `recordAdminEvent()` which always emits a structured `console.info` JSON line (picked up by
Cloud Logging as a log entry) AND attempts a Firestore `/admin_events` write when Firebase is configured. Firestore
failures are swallowed — a logging failure never fails a business op.

Current event types (extend inline until corpus >10, then promote to a UAC enum):

| Type                | Fires from                    | `target` shape                         | `details` shape                                 |
| ------------------- | ----------------------------- | -------------------------------------- | ----------------------------------------------- |
| `ADMIN_DOC_DELETED` | `/api/onboarding/docs/delete` | `{ org_id, application_id, doc_type }` | `{ deleted_path, backend: "local" \| "cloud" }` |

Events are fire-and-forget (`void recordAdminEvent(...)`) so the response never blocks on logging.

---

## §9 — Follow-ups

- **Admin playback pivot from email → org_id**: when Firestore `/questionnaires` grows large we may want a server-side
  index rather than the current two-query join. Defer until list exceeds ~500 docs.
- **Questionnaire versioning**: if the schema grows past 15 axes, promote to `QuestionnaireResponseV2` with a `version`
  tag and migrate Firestore docs.
- ~~**Port orphan-audit to deployment-ui**: deferred — deployment-ui is Vite/React (not Next.js), so scanner needs a
  framework adapter to discover React Router routes.~~ **Shipped 2026-04-22** in deployment-ui `e5d2355`. React Router
  variant at `deployment-ui/scripts/orphan-audit.ts` discovers `<Route path="...">` JSX; same whitelist / baseline /
  blocking contract as the Next.js variant. Triage surfaced 2 real orphans (`/chaos`, `/client-subscriptions`) — wired
  into `Header.tsx` admin nav. See `/codex/04-architecture/orphan-audit.md §8`.
