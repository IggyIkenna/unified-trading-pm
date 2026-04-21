---
scope: [engineer, sales]
---

# Prospect Questionnaire & Onboarding-Docs Flow

> **Status:** canonical (2026-04-21) **Owner:** UI Architecture **SSOT for:**
> `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py::QuestionnaireResponse`,
> `unified-trading-system-ui/app/(public)/questionnaire/page.tsx`,
> `unified-trading-system-ui/app/(ops)/admin/questionnaires/page.tsx`,
> `unified-trading-system-ui/app/(ops)/admin/organizations/[id]/page.tsx`,
> `unified-trading-system-ui/lib/onboarding/doc-store.ts`,
> `unified-trading-system-ui/app/api/onboarding/{upload,download,docs/list,docs/delete}/route.ts`. **Plan:**
> [`plans/active/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md`](../../plans/active/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.plan.md)

---

## §1 — The problem

Prospects landing on Odum have three decisions to make: (a) which service family fits (IM / DART / Reg Umbrella /
combo), (b) how to express their existing preferences about venues, instruments, strategy style, and fund structure, and
(c) for Reg-Umbrella specifically, the regulatory posture of their firm (licence region, own-MLRO vs consume Odum's,
entity jurisdiction, operating currencies, 3mo/1yr/2yr business targets). Before 2026-04-21 we only asked the first 6
axes; Reg-Umbrella prospects had to finish the questionnaire and then schedule a call to relay everything else. The call
has now been folded into the form.

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

## §3 — The access-code gate

The questionnaire page at `/questionnaire` is wrapped in the existing `<BriefingAccessGate>` (same access-code session
as `/briefings/*` and `/docs`). Session keyed by `odum-briefing-session` in localStorage; a prospect who unlocked
briefings is not re-prompted. Access codes live in `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` (global) or per-path overrides
declared in `lib/briefings/access-code.ts`.

Each submission carries an envelope:

```ts
interface QuestionnaireEnvelope {
  email: string; // work email (free text)
  firm_name: string; // prospect's firm
  access_code_fingerprint: string; // hex SHA-256 of the access code
}
```

The fingerprint is not the code — just a digest, so the admin panel can bucket responses by cohort (e.g. "everyone who
unlocked with the Q2-investor-demo code") without storing plain codes. If SubtleCrypto is unavailable (older runtime)
the fingerprint is the empty string and the envelope still identifies the prospect by email + firm.

---

## §4 — The admin playback loop

```
 ┌──────────────────────────────┐
 │  /questionnaire  (invite-     │
 │  gated public page; optional  │
 │  Reg-Umbrella branch)         │
 └──────────────┬────────────────┘
                │ submit
                ▼
 ┌──────────────────────────────┐     ┌──────────────────────────────┐
 │  localStorage (mock/dev):     │     │  Firestore /questionnaires    │
 │  questionnaire-response-v1    │     │  (staging/prod) — response    │
 │  questionnaire-envelope-v1    │     │  doc with submitted_by field  │
 └──────────────┬────────────────┘     └────────────┬─────────────────┘
                │                                    │
                └─────────────┬──────────────────────┘
                              ▼
         ┌──────────────────────────────────────────────┐
         │  /admin/questionnaires  (list, all rows)     │
         │  — sortable, cross-link "View org" per row   │
         └────────────────┬─────────────────────────────┘
                          ▼
         ┌──────────────────────────────────────────────┐
         │  /admin/organizations/[id]                   │
         │    · Prospect questionnaire card             │
         │      (13 axes when Reg-Umbrella)             │
         │    · Documents card (list + View / Download  │
         │      / Delete-with-confirm)                  │
         │    · Members · Venue API keys · Reports      │
         └──────────────────────────────────────────────┘
```

Join rule: `OrgQuestionnaireSection` queries Firestore `/questionnaires` filtered by
`submitted_by.email == org.contact_email` (primary) or `submitted_by.firm_name == org.name` (fallback). Mock mode shows
a friendly "Firebase not configured" message instead of crashing.

---

## §5 — The onboarding-docs flow

`lib/onboarding/doc-store.ts` exposes a `DocStore` adapter with two backends picked at request-time by
`resolveDocStore()`:

| Backend          | Selected when                                         | Behaviour                                          |
| ---------------- | ----------------------------------------------------- | -------------------------------------------------- |
| `localStore`     | `CLOUD_MOCK_MODE=true` OR `ENVIRONMENT ∈ {dev, test}` | Writes / reads `.local-dev-cache/onboarding-docs/` |
| `cloudStubStore` | Otherwise (staging / prod)                            | Throws a fail-loud error pointing at this doc      |

Canonical `gs://odum-${env}-onboarding-docs/{org}/{app}/{doc}.ext` URIs are always emitted on upload regardless of
backend, so downstream readers (admin UI, analytics) see a stable path.

### §5a Enabling the cloud path

1. Install the Google Cloud Storage client: `pnpm add @google-cloud/storage` (or `firebase-admin` if we want to reuse
   Firebase Auth for server-side admin gates).
2. Mint the bucket in the target GCP project: `odum-staging-onboarding-docs`, `odum-prod-onboarding-docs`. Rotate keys
   quarterly; grant `roles/storage.objectAdmin` to the Cloud Run service account running the UI.
3. Replace the body of `cloudStubStore` in `lib/onboarding/doc-store.ts` with GCS-backed `upload` / `download` / `list`
   / `delete`. The adapter interface (`DocStore`) is stable — only the stub body changes.
4. Verify the cloud path with an integration test that uses `CLOUD_MOCK_MODE=false` + ADC credentials.
5. Delete the `NOT_IMPLEMENTED` constant + stub. The `resolveDocStore()` dispatcher picks automatically.

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
[`orphan-audit.md` § Whitelist Triage Rule](orphan-audit.md#whitelist-triage-rule). Both `list` and `delete` were added
2026-04-21 alongside this plan. `reset` was deleted (replaced by the per-doc `delete` endpoint).

---

## §7 — Follow-ups

- **Cloud storage live**: install `@google-cloud/storage` and replace `cloudStubStore` (see §5a).
- **Admin playback pivot from email → org_id**: when Firestore `/questionnaires` grows large we may want a server-side
  index rather than the current two-query join. Defer until list exceeds ~500 docs.
- **Delete audit log**: currently `/docs/delete` returns `{ ok, deleted_path }` but does not write an audit event. Hook
  `log_event("ADMIN_DOC_DELETED", {...})` once the UTL client-side bridge lands.
- **Questionnaire versioning**: if the schema grows past 15 axes, promote to `QuestionnaireResponseV2` with a `version`
  tag and migrate Firestore docs.
