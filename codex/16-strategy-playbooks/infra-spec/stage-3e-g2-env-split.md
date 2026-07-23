---
doc_type: codex-ssot
title: Stage 3E G2 — Env-split design (dev / staging / prod) for pricing, contracts, metering, claims, compliance
summary:
  mock/staging/prod sink placement for the 5 G2.x state items — pricing numbers (codex markdown, no split), client
  contracts (Firestore per project), usage metering (GCS parquet + BigQuery), capability claims (Firebase custom
  claims), compliance events (UTL → Pub/Sub) — with Firestore rules, the odum-staging setup walkthrough, and the
  staging→prod promotion diff.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    execution-service,
    instruments-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [infrastructure, uac, execution, cost, migration, docspec]
related:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
  ]
created: 2026-04-20
authoritative_for:
  [
    Stage 3E G2 dev/staging/prod env-split placement for pricing / contracts / usage-metering / capability-claims /
    compliance-events,
  ]
referenced_by: [/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md]
owner:
last_reviewed:
code_refs:
---

# Stage 3E G2 — Env-split design (dev / staging / prod) for pricing, contracts, metering, claims, compliance

> **Purpose.** Decide where each piece of G2.x state lives across dev / staging / prod. Follows the existing
> [bucket-isolation-model.md](../../05-infrastructure/bucket-isolation-model.md) 3-tier pattern (`mock | dev | prod`)
> plus Firebase project split (`central-element-323112` today; `odum-staging` planned per
> [staging-odum-research-co-uk.md](../../14-customer-journeys/environments/staging-odum-research-co-uk.md)).
>
> **Design principle (operator directive 2026-04-20):** _"dev, staging and prod for data and auth is key. mock local
> cache vs cloud (gcs and firebase). case by case what makes sense factoring in data size and security."_
>
> **Five G2.x items** covered here — one per row. Every row declares `mock` / `dev` / `prod` sinks plus the promotion
> path.

---

## Summary matrix

| #   | Item                  | Size                                                         | Security                                                       | Mock (dev local)                                            | Staging (odum-research.co.uk)                                         | Prod (odum-research.com)                                    |
| --- | --------------------- | ------------------------------------------------------------ | -------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------- |
| 1   | **Pricing numbers**   | small (13-row table × 3 tiers × 3 depths)                    | HIGH (internal column is codex-private)                        | codex markdown → JSON loader                                | same (source-controlled; no per-env divergence)                       | same                                                        |
| 2   | **Client contracts**  | small (one doc per org)                                      | **HIGH** (negotiated discounts, exclusivity)                   | `.local-dev-cache/contracts/*.json`                         | Firestore `/contracts/{org_id}` in `odum-staging`                     | Firestore `/contracts/{org_id}` in `central-element-323112` |
| 3   | **Usage metering**    | **LARGE** (daily fills × chains × clients × analytics calls) | MEDIUM (per-client aggregates)                                 | `.local-dev-cache/usage/*.parquet` fixtures                 | GCS `odum-staging-usage-metering/` + BigQuery `staging_usage` dataset | GCS `odum-usage-metering/` + BigQuery `usage` dataset       |
| 4   | **Capability claims** | small (5-10 claims per user)                                 | **HIGH** (`pricing.read_internal` gates codex-private pricing) | `demo-provider.ts` seeds localStorage                       | Firebase custom claims on `odum-staging`                              | Firebase custom claims on `central-element-323112`          |
| 5   | **Compliance events** | medium (rule-07/08 violations per quote)                     | LOW (internal audit)                                           | local log file (`.local-dev-cache/compliance-events.jsonl`) | Pub/Sub `staging-compliance-events` topic + BigQuery staging sink     | Pub/Sub `compliance-events` + BigQuery prod sink            |

Default env binding per the 3-tier model:

- **`mock`** (= dev local): `CLOUD_MOCK_MODE=true`, `NEXT_PUBLIC_MOCK_API=true`, no Firebase
- **`dev`** (= staging): `ENVIRONMENT=staging`, `NEXT_PUBLIC_MOCK_API=false`, Firebase `odum-staging`
- **`prod`**: `ENVIRONMENT=prod`, `NEXT_PUBLIC_MOCK_API=false`, Firebase `central-element-323112`

---

## 1. Pricing numbers — codex markdown is the SSOT, no per-env divergence

**Why no split:** Pricing anchor ranges live in one markdown table
([pricing-building-blocks.md](../../14-customer-journeys/commercial-model/pricing-building-blocks.md)) + the richer IM /
Reg Umbrella mechanics in sibling files. Numbers are identical across all environments — staging uses the same Tier A /
Tier B tables as prod. Internal cost column stays codex-private per rule 08.

**Implementation:**

- **SSOT:** `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md` (locked ranges today;
  finance-committed point values land inline once signed off).
- **Loader (new):** `unified-trading-pm/scripts/propagation/sync-pricing-tables-to-uac.{sh,py}` — parses the markdown
  table, emits `unified-api-contracts/unified_api_contracts/internal/architecture_v2/pricing_manifest.json`. Pattern
  mirrors G1.8 archetype-capability-manifest.json.
- **UAC consumer:** `unified_api_contracts.strategy.cost()` reads from `pricing_manifest.json` at import time; falls
  back to `todo_numeric=True` shape-only quotes when the manifest is absent (siloed CI).
- **Drift gate:** QG hook in PM `scripts/quality-gates.sh` runs `sync-pricing-tables-to-uac.sh --check` on every push.
- **Internal-cost column:** stays in the markdown as `TBD` or populated values; loader explicitly **excludes** the
  internal column from the emitted manifest. `tier=internal` lookups in UAC go through a separate code path gated by the
  `pricing.read_internal` capability claim (item 4).

---

## 2. Client contracts — Firestore per env, admin-only reads

**Shape:** one doc per `org_id` keyed on the Firebase project. Each doc carries:

```typescript
interface ClientContract {
  org_id: string; // canonical org identifier
  service_family: "IM" | "DART" | "RegUmbrella" | "combo";
  fund_structure: "SMA" | "Pooled" | "NA";
  packages: {
    // signed blocks with tier per block
    block_id: string;
    tier: "tier_a" | "tier_b";
    sub_scope: string[]; // venues / chains / instrument_types
    integration_depth?: "basic_instruction_integration" | "richer_execution_constraints" | "custom_allocator_handling";
  }[];
  negotiated_discount_pct?: number; // applied to PriceQuote.monthly_variable
  exclusivity_tier?: "none" | "narrow" | "broad" | "full";
  signed_at: string; // ISO-8601
  renewal_at: string; // ISO-8601
  valid_until: string; // ISO-8601
}
```

**Security model:**

| Access                                         | Firestore rule                                                           |
| ---------------------------------------------- | ------------------------------------------------------------------------ |
| Anonymous                                      | DENIED                                                                   |
| Authenticated (non-admin)                      | read `/contracts/{org_id}` only if `request.auth.token.org_id == org_id` |
| Admin (custom claim `admin=true`)              | read + write any doc                                                     |
| IM_desk operator (custom claim `im_desk=true`) | read all, write denied                                                   |

**Env split:**

- **mock:** `.local-dev-cache/contracts/<persona_id>.json` — one file per persona; `lib/auth/demo-provider.ts` seeds
  from the questionnaire localStorage response. No negotiated discounts (prospects are pre-signed).
- **staging:** Firestore `/contracts/{org_id}` on `odum-staging` project. Pre-seeded with the 11 demo-persona contracts
  via `user-management-ui` admin flow.
- **prod:** Firestore `/contracts/{org_id}` on `central-element-323112`. One doc per paying client; admin-only writes
  via `user-management-ui`.

**New files (G2.x scope):**

- `unified-api-contracts/unified_api_contracts/internal/domain/contract_management/schemas.py` — Pydantic mirror of
  `ClientContract` TypeScript interface
- `unified-trading-pm/codex/14-customer-journeys/commercial-model/contract-schema.md` — contract-management SSOT doc
- Firestore security rules update in `unified-trading-system-ui/firestore.rules` (needs creating — see
  [§ Firestore rules, new](#firestore-rules-new) below)

---

## 3. Usage metering — GCS time-series per env, BigQuery aggregation

**Why GCS not Firestore:** Metering data is **LARGE** (fills accumulate across millions of ticks per client-month;
analytics-call counts accumulate per-request). Firestore is wrong (document size caps, read-cost explosion); GCS
parquet + BigQuery is the established pattern already in use for availability-manifest writes (see
[`02-data/availability-manifest-and-data-status.md`](../../02-data/availability-manifest-and-data-status.md)).

**Pattern:** time-partitioned parquet in `odum-<env>-usage-metering/` GCS bucket; BigQuery external table for
aggregation queries. Follows the Group B (env-suffixed) pattern from
[bucket-isolation-model.md](../../05-infrastructure/bucket-isolation-model.md).

**Path layout:**

```
odum-<env>-usage-metering/
  fills/
    year=2026/month=04/day=20/client_id=<id>/part-00000.parquet
  analytics_calls/
    year=2026/month=04/day=20/client_id=<id>/service=<svc>/part-00000.parquet
  defi_gas/
    year=2026/month=04/day=20/client_id=<id>/chain=<chain>/part-00000.parquet
  storage_gb/
    year=2026/month=04/day=20/client_id=<id>/bucket=<b>/snapshot.parquet
```

**Writers** (existing services that already emit availability-manifest rows):

| Writer service                       | Metering surface | Bucket prefix      |
| ------------------------------------ | ---------------- | ------------------ |
| execution-service                    | fills            | `fills/`           |
| analytics services (various)         | analytics_calls  | `analytics_calls/` |
| DeFi connectors (aave, uniswap, ...) | defi_gas         | `defi_gas/`        |
| instruments-service + MTDS           | storage_gb       | `storage_gb/`      |

Each writer emits a `UsageMeterRow` (new UAC schema, Pydantic) on every metered action; the UTL events plumbing +
ManifestWriter writes to parquet with `capture_status="captured"`.

**BigQuery aggregation:**

- `<env>_usage.fills_daily` — `SUM(notional_filled) GROUP BY client_id, day`
- `<env>_usage.analytics_calls_daily` — `COUNT(*) GROUP BY client_id, service, day`
- `<env>_usage.billing_rollup_monthly` — joins the above against `/contracts/{org_id}` for Tier A variable pricing input

**Env split:**

- **mock:** `.local-dev-cache/usage/*.parquet` — tiny fixtures per persona. `.coverage-floor-exception.md` excludes from
  QG.
- **staging:** `odum-staging-usage-metering/` GCS bucket + `staging_usage` BigQuery dataset.
- **prod:** `odum-usage-metering/` GCS bucket + `usage` BigQuery dataset.

**Billing service** (G2.x consumer): reads `<env>_usage.billing_rollup_monthly`, multiplies by Tier A cost-plus rate
from pricing-building-blocks (block-by-block), emits invoice via `unified-api-contracts/.../client_reporting/Invoice`.

---

## 4. Capability claims — Firebase custom claims per env, seeded via admin Cloud Function

**Pattern:** Firebase Authentication supports per-user custom claims (≤1KB per user). Claims live on the JWT; any
service verifying the ID token can read them.

**Initial claim set:**

| Claim                      | Type                                                                                            | Purpose                                                |
| -------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `role`                     | `"admin" \| "im_desk" \| "client" \| "internal"`                                                | Coarse role, matches `AuthUser.role`                   |
| `audience`                 | `"admin" \| "im_desk" \| "im_client" \| "trading_platform_subscriber" \| "reg_umbrella_client"` | Rule 12 service-family scope key                       |
| `org_id`                   | `string`                                                                                        | Firestore gate for `/contracts/{org_id}` reads         |
| `pricing.read_internal`    | `boolean`                                                                                       | Unlocks `tier=internal` column in `cost()`             |
| `strategy_catalogue_admin` | `boolean`                                                                                       | Unlocks admin toggle UI (rule 12 `IM_desk` or `admin`) |

**Setter (new Cloud Function):** `setCapabilityClaim({uid, claims})` — admin-only. Verifies caller has `admin=true`
claim; writes new claims via Firebase admin SDK; user must re-sign-in to pick up.

**Verifier (middleware):** each service's FastAPI `Depends(verify_firebase_token)` populates `UserContext` from the
decoded ID token. Already sketched in the G1.7 HTTP router; needs extension to read custom claims.

**Env split:**

- **mock:** `demo-provider.ts` seeds claims on the mock `AuthUser` object based on persona ID. Example: `admin` persona
  gets `pricing.read_internal=true`, `strategy_catalogue_admin=true`; `im-desk-operator` gets `im_desk`; `prospect-dart`
  gets nothing.
- **staging:** Firebase custom claims on `odum-staging` users. Seeded once per persona provisioning via the admin Cloud
  Function.
- **prod:** Firebase custom claims on prod users. Set by the onboarding flow + admin console.

**New files (G2.x):**

- `user-management-ui/functions/setCapabilityClaim.ts` — Cloud Function, admin-gated
- `unified-api-contracts/unified_api_contracts/internal/auth/capability_claims.py` — Pydantic `CapabilityClaims`
  schema + verification helpers
- `user-management-ui/app/(platform)/users/[id]/capability-claims/page.tsx` — admin UI for setting claims
- Firestore rule update — gate `/contracts/{org_id}` reads on `request.auth.token.org_id`

---

## 5. Compliance events — UTL → Pub/Sub per env

**Why UTL is the bus:** The `STANDARD_LIFECYCLE_EVENTS` registry is the canonical event taxonomy;
`publish_coordination_event` already routes through a per-env Pub/Sub topic. Rule 07 / rule 08 violations emitted from
UAC's `cost()` function plug in here.

**Two new UTL events (G2.x register):**

- `PRICING_RULE_07_VIOLATION` — BL-19 raw-data-framing on any tier; BL-12 licensing constraint breach
- `PRICING_RULE_08_VIOLATION` — exclusivity-on-tier-a; internal-cost-leakage; missing-12-month-minimum

**Payload:**

```python
class PricingViolationPayload(BaseModel):
    rule_id: Literal["07", "08"]
    violation_code: str               # e.g. "exclusivity_on_tier_a"
    combo_id: str
    caller_audience: ClientAudience
    org_id: str | None
    requested_tier: PricingTier
    details: str
    timestamp_utc: str
```

**Env split:**

- **mock:** UTL writes to local log file `.local-dev-cache/compliance-events.jsonl`; no Pub/Sub emission.
- **staging:** UTL emits to Pub/Sub topic `staging-compliance-events` (per env prefix in
  [staging-odum-research-co-uk.md](../../14-customer-journeys/environments/staging-odum-research-co-uk.md)).
- **prod:** UTL emits to Pub/Sub topic `compliance-events`; BigQuery sink to `compliance.violations` dataset; dashboards
  in Looker Studio.

**Wiring (short-term fix):** UAC `cost()` function's `Rule08Violation` branches raise/return the violation object; add a
`compliance_sink: ComplianceSink | None` parameter that the strategy-service pricing router populates from the running
service's UTL emitter. Dev fixture uses a `LocalFileComplianceSink`; staging/prod use `UTLComplianceSink` that calls
`publish_coordination_event`.

---

## Firestore rules (new)

Needs creating at `unified-trading-system-ui/firestore.rules` + deployment via `firebase deploy --only firestore:rules`.
Starter:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // G1.10 — public questionnaire
    match /questionnaires/{doc} {
      allow create: if true;                                     // anonymous submit
      allow read: if request.auth.token.admin == true
                  || request.auth.token.im_desk == true;         // admin + IM desk
      allow update, delete: if request.auth.token.admin == true;
    }

    // G2.x — client contracts
    match /contracts/{orgId} {
      allow read: if request.auth.token.admin == true
                  || request.auth.token.im_desk == true          // IM desk reads-all
                  || request.auth.token.org_id == orgId;         // client reads own
      allow write: if request.auth.token.admin == true;
    }

    // Per-user profile shards (existing pattern extended)
    match /users/{uid}/{document=**} {
      allow read: if request.auth.uid == uid
                  || request.auth.token.admin == true;
      allow write: if request.auth.token.admin == true;
    }
  }
}
```

---

## Setup walkthrough — staging (odum-research.co.uk)

Ordered by dependency:

### Step 1 — provision `odum-staging` Firebase project

```bash
firebase projects:create odum-staging --display-name "Odum Staging"
firebase use --add odum-staging --alias staging
```

Add to `.firebaserc` (new file, commit to both UI repos):

```json
{
  "projects": {
    "default": "central-element-323112",
    "staging": "odum-staging",
    "prod": "central-element-323112"
  }
}
```

### Step 2 — enable services on the staging project

```bash
firebase --project odum-staging use odum-staging
# In Firebase console:
#  - Authentication → enable Email/Password + Anonymous
#  - Firestore → create database (region: europe-west4, same as Cloud Run)
#  - Cloud Functions → enable (Node 20)
#  - Hosting → add odum-research.co.uk custom domain
```

### Step 3 — deploy Firestore rules

```bash
cd unified-trading-system-ui
# Create firestore.rules (see § Firestore rules above)
firebase --project odum-staging deploy --only firestore:rules
```

### Step 4 — seed persona user accounts

```bash
cd user-management-ui
# Admin provisioning flow at /platform/onboard or via Firebase console:
#  - Create 17 persona users (matches PERSONAS array from G1.4)
#  - For each, set custom claims via setCapabilityClaim Cloud Function
```

### Step 5 — deploy Cloud Functions

```bash
cd user-management-ui
firebase --project odum-staging deploy --only functions
# Includes: setCapabilityClaim, mintSeedDemoToken (G2.x)
```

### Step 6 — deploy unified-trading-system-ui to Cloud Run staging

```bash
cd unified-trading-system-ui
bash scripts/deploy-cloud-run.sh --env staging
```

### Step 7 — wire compliance Pub/Sub topic

```bash
gcloud --project=odum-staging-gcp pubsub topics create staging-compliance-events
gcloud --project=odum-staging-gcp pubsub subscriptions create staging-compliance-events-bq \
  --topic=staging-compliance-events \
  --bigquery-config-schema=PricingViolationPayload \
  --bigquery-config-table=staging-odum-staging-gcp:staging_compliance.violations
```

### Step 8 — provision usage-metering GCS bucket

```bash
gsutil mb -p odum-staging-gcp -l europe-west4 -c STANDARD gs://odum-staging-usage-metering/
# IAM: grant each writer service's service account object-writer on this bucket
```

### Step 9 — seed contracts collection

```bash
# For each of the 17 personas, write a demo contract doc via admin SDK:
npx tsx scripts/seed-staging-contracts.ts   # new script, reads PERSONAS + writes Firestore
```

### Step 10 — smoke test

```bash
# Log in as each persona on odum-research.co.uk
# Verify:
#  - Restriction profile resolves correctly (G1.7)
#  - Pricing cost endpoint returns expected PriceQuote (G2.x)
#  - Contract doc visible only to that org
#  - Compliance event flows when a rule-08 violation is triggered
```

---

## Promotion path (staging → prod)

Identical logic, only config diffs:

| File             | Staging value                         | Prod value                             |
| ---------------- | ------------------------------------- | -------------------------------------- |
| `.firebaserc`    | `projects.staging=odum-staging`       | `projects.prod=central-element-323112` |
| GCS bucket       | `odum-staging-usage-metering`         | `odum-usage-metering`                  |
| Pub/Sub topic    | `staging-compliance-events`           | `compliance-events`                    |
| BigQuery dataset | `staging_usage`, `staging_compliance` | `usage`, `compliance`                  |
| Firestore rules  | deployed to staging project           | deployed to prod project (same file)   |
| Secret Manager   | staging secrets only                  | prod secrets only                      |

**Rule 03 (same-system-principle) invariant:** any divergence in code, rules, or schema between staging and prod is a
violation. The only legitimate per-env difference is the values in config + the bucket / topic / dataset names.

---

## Cross-references

- [bucket-isolation-model.md](../../05-infrastructure/bucket-isolation-model.md) — 3-tier `mock | dev | prod` GCS
  pattern
- [staging-odum-research-co-uk.md](../../14-customer-journeys/environments/staging-odum-research-co-uk.md) — staging env
  SSOT
- [production-odum-research-com.md](../../14-customer-journeys/environments/production-odum-research-com.md) — prod env
  SSOT
- [local-dev.md](../../08-workflows/local-dev.md) — local dev pattern + mock-mode axis matrix
- [pricing-building-blocks.md](../../14-customer-journeys/commercial-model/pricing-building-blocks.md) — item #1 SSOT
- [`_ssot-rules/07-data-licensing-boundaries.md`](../../14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md)
- [`_ssot-rules/08-pricing-principles.md`](../../14-customer-journeys/_ssot-rules/08-pricing-principles.md)
- [`_ssot-rules/12-service-family-scope-rules.md`](../../14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md)
  — `UserContext.audience` + custom-claims mapping
- [stage-3c-derivation-engine.md](stage-3c-derivation-engine.md) §1.2 — `cost()` formula + rule 07/08 enforcement
- [deployment_topology_and_client_isolation_2026_04_17.plan.md](../../../plans/archive/deployment_topology_and_client_isolation_2026_04_17.plan.md)
  — runtime topology SSOT
