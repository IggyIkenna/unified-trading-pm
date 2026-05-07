---
name: fund-administration — Phase 6 + 4 follow-ups, single dispatch prompt (GCP + Firebase + MCP Playwright)
overview:
  Paste into a fresh Claude Code session. Finishes Cloud Run staging deploy, CRA entitlement backfill, fund-admin
  persistence swap-in, POD integration wiring (crypto-spot + crypto-derivatives tracks), briefings copy split, and
  questionnaire regulatory-notes field. Assumes the operator has GCP console access, Firebase access, and all CLIs
  logged in (gcloud, gh, firebase, npm, uv). MCP Playwright is available for autonomous UI verification.
type: meta
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-22
orphan_candidate: true
orphan_reason:
  "Pure agent dispatch prompt; work largely shipped via parent fund-administration-service plan + CRA backfill
  (8caae477)."
reconciliation_date: 2026-04-25
---

> **ORPHAN CANDIDATE 2026-04-25.** Scope appears unconnected to the live system. Reason: Pure agent dispatch prompt;
> work largely shipped via parent fund-administration-service plan + CRA backfill (8caae477). See
> `_reconciliation_evidence_map_2026_04_25.md` for the integration check.

# Finisher dispatch prompt

Paste the block below (between the two `<<<PASTE>>>` markers) into a fresh agent session.

<<<PASTE>>>

````
You are picking up the fund-administration-service Phase 6 + 4 follow-ups. Phases 0-5 already shipped.
Everything in this prompt is **local-test → push → operator-confirm** cadence. Act autonomously when safe;
stop + ask on anything that writes to production, creates durable external artefacts, or mutates shared
customer data.

# Mandatory rules

Read BEFORE any action:
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/.claude/CLAUDE.md`

Non-negotiable:
- Workspace root: `/Users/ikennaigboaka/Code/unified-trading-system-repos`
- Active feature branch: `live-defi-rollout` (read from `workspace-manifest.json` `active_feature_branch`)
- Never `git push --force`, `git reset --hard`, `git rebase -i`, `--dep-branch` with `--agent`, `--no-verify`
- Conventional commits only; `plans:` prefix rejected — use `docs(plans/...):` or `feat(...):`
- `uv pip install` not `pip install`; `basedpyright` not `pyright`
- Tests via `cd <repo> && bash scripts/quality-gates.sh` — never `pytest` directly
- Citadel UAC imports: `from unified_api_contracts import X` or `from unified_api_contracts.<domain> import X` — never `.canonical.*`, `.normalize_utils.*`, `.internal`
- **Parallel sessions are active on this workspace.** Before quickmerging a downstream consumer, check upstream dep repos (UAC/UTL/UCI/UEI/MTDS) for dirty working trees. If dirty, either (a) proceed with explicit operator go-ahead, (b) wait for them to land, or (c) push without quickmerge (direct `git push origin live-defi-rollout`) and let CI take the hit.
- **Operator has given blanket go-ahead: just `git push origin live-defi-rollout`; do NOT run `quickmerge --agent` on any repo during this dispatch.** CI + PR cleanup happens in a later pass.
- If pre-commit reformats your staged files + drops the commit, re-stage the reformatted files + re-commit with the same message. Do not skip hooks.

MCP Playwright is available for autonomous UI verification. Use it to close the acceptance-criteria loop on any UI work.

# Context — what already shipped

Local-branch commits on `live-defi-rollout`, pushed to origin unless noted:

| Repo | Top SHA | What |
|------|---------|------|
| unified-api-contracts | `f008ce8` | fund_administration domain + public facade + API request DTOs + FundTransferContext + AllocatorCashAccountView + CashAccountMovement |
| unified-trading-library | `9e18c904` | 10 fund-administration lifecycle events registered in `STANDARD_LIFECYCLE_EVENTS` |
| position-balance-monitor-service | `78afb1c` | TreasuryConfig.target_allocations + fund_id / share_class keying |
| execution-service | `f545a507` | TransferAdapter fund_context kw-arg (FundTransferContext from UAC) |
| fund-administration-service | `bcd6090` | **NEW repo — pushed to `github.com/IggyIkenna/fund-administration-service`**; scaffold + state machines + CapitalRouter + REST API + PM workflow templates + cloudbuild.yaml |
| unified-trading-system-ui | `1b17fc8` | `/services/im/funds/*` routes + mock fixtures + tests |
| client-reporting-api | `f214286` | allocator routes with entitlement enforcement |
| unified-trading-pm | `9d2384ad` | codex custody model + manifest registration + Phase 6 walkthrough + 5 follow-up plans |

Parent plan: `plans/active/fund_administration_service_and_pooled_subscription_redemption_2026_04_20.plan.md`.

# Your scope — 6 workstreams, ordered by dependency

## Workstream A — Cloud Run staging deploy of fund-administration-service  [operator + agent pair]

Dependency: none (can start immediately).

**Agent steps:**
1. Read `fund-administration-service/cloudbuild.yaml` — verify it's the canonical API template variant.
2. Create a Cloud Build trigger pointing at `github.com/IggyIkenna/fund-administration-service` on `live-defi-rollout` branch:
   ```bash
   gcloud builds triggers create github \
     --repo-owner=IggyIkenna --repo-name=fund-administration-service \
     --branch-pattern='^live-defi-rollout$' \
     --build-config=cloudbuild.yaml \
     --name=fund-administration-service-live-defi-rollout \
     --project=central-element-323112
   ```
3. First manual `gcloud builds submit --config=cloudbuild.yaml --substitutions=_SERVICE_NAME=fund-administration-service,_REGISTRY_REPO=unified-trading-system` from `fund-administration-service/` to seed Artifact Registry. Verify the image lands at `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/fund-administration-service:latest`.
4. Create a Cloud Run staging service:
   ```bash
   gcloud run deploy fund-administration-service \
     --image=asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/fund-administration-service:latest \
     --region=asia-northeast1 \
     --service-account=fund-administration-sa@central-element-323112.iam.gserviceaccount.com \
     --set-env-vars=MODE=staging,GCP_PROJECT_ID=central-element-323112,PERSISTENCE_BACKEND=memory \
     --no-allow-unauthenticated \
     --min-instances=0 --max-instances=3 \
     --project=central-element-323112
   ```
   Create the service account if it does not exist; grant it Secret Manager Secret Accessor + Firestore User + Cloud Logging Writer on `central-element-323112`.
5. Hit the health endpoint via `gcloud run services proxy fund-administration-service --region=asia-northeast1 --port=8888` then `curl localhost:8888/healthz` — expect HTTP 200 with `{"status":"ok",...}`.
6. Add `fund-administration-service` to `deployment-service/stable_versions.yaml` per the existing pattern (see how `client-reporting-api` is wired — grep for it first) so future dispatch-based deploys work.

**Acceptance:**
- Cloud Build trigger exists + has succeeded at least once
- Cloud Run service in `asia-northeast1` shows READY with the `:latest` image
- `/healthz` returns 200 from the authenticated proxy
- `deployment-service/stable_versions.yaml` entry committed + pushed

## Workstream B — Briefings copy split + questionnaire regulatory_notes  [code + UI]

Dependency: none (can start immediately, parallel with A).

Plan: `plans/active/pod_crypto_administrator_integration_2026_04_22.plan.md` §"Briefings copy" + §"Questionnaire wiring".

**Steps:**
1. **UAC** — extend `QuestionnaireResponse` in `unified_api_contracts/internal/domain/.../questionnaire.py` (grep for the existing type location first) with `regulatory_notes: str = ""` (optional free text, Field max_length=4000).
2. **Questionnaire UI** — `unified-trading-system-ui/app/(public)/questionnaire/page.tsx`: add a textarea for `regulatory_notes` with label "Regulatory context (optional)" and helper text "Anything about your jurisdiction, investor profile, or licensing we should know before the second call — e.g. 'US-based end-investors requiring 506(c)' or 'AUSTRAC-registered Australian fund'." Wire into submission payload.
3. **Admin view** — `app/(platform)/admin/organizations/[id]/questionnaire/page.tsx` (find + extend; create if missing): surface `regulatory_notes` + a derived `fund_track_recommendation` field.
4. **Fund-track resolver** — add a helper in `unified-trading-library` (or the questionnaire lib) `resolve_fund_track(QuestionnaireResponse) -> Literal["CRYPTO_SPOT", "CRYPTO_DERIVATIVES", "BOTH", "TRADFI_PENDING", "NOT_APPLICABLE"]` per the plan's §"Fund-type resolution" rules. Unit-test edge cases.
5. **Briefings copy split** — `unified-trading-system-ui/lib/briefings/content.ts`:
   - IM briefing (`slug: "investment-management"`), "Pooled custody — qualified custodian and portal subscriptions" section: split into two short sub-sections — "Crypto-spot fund" (BTC/ETH/major-cap; spot venues; no leverage; daily NAV) and "Crypto-derivatives fund" (BTC/ETH perps + dated futures; CeFi venues; leverage capped per mandate; daily NAV with intraday refresh). Keep "regulated fund administrator" generic; never name POD on public copy.
   - Same split on `/briefings/regulatory` Pooled section (if applicable).
   - TradFi Pooled: add a single sentence noting "TradFi Pooled funds require a different administrator (to be selected per mandate) and are out of scope of the crypto Pooled rail."
6. **Marketing pages** — `unified-trading-system-ui/app/(public)/investment-management/page.tsx`: if fund-type is surfaced at this level, add the same split; otherwise link to `/briefings/investment-management`.
7. **Playwright E2E** — `tests/e2e/public/questionnaire.spec.ts` (create if missing): walk the 4 paths — crypto-spot selection, crypto-derivatives selection, both, TradFi. Assert the correct `fund_track_recommendation` surfaces in the response payload. Use MCP Playwright to iterate on selectors/waits.

**Acceptance:**
- Questionnaire accepts regulatory_notes + persists via existing Firestore / localStorage submission sink
- Admin view shows regulatory_notes + fund_track_recommendation
- Briefings copy cleanly splits crypto-spot vs crypto-derivatives
- Playwright spec passes 4/4 paths
- `cd unified-trading-system-ui && CI=true npm test -- --run` green
- `cd unified-api-contracts && bash scripts/quality-gates.sh` green

## Workstream C — CRA entitlement backfill on existing reporting routes  [code]

Dependency: none (parallel with A + B).

Plan: `plans/active/cra_entitlement_backfill_existing_reporting_routes_2026_04_22.plan.md`.

**Steps:**
1. Pre-audit — enumerate every route in `client-reporting-api/client_reporting_api/api/routes/` taking a `client_id` query/path param. Capture into a pre-audit table in the plan's §"Pre-audit manifest".
2. Extract `_enforce_entitlement` from `allocators.py` into `client_reporting_api/core/entitlement.py` — same semantics, shared helper.
3. Apply to every `client_id`-scoped route. Add a `require_internal(auth)` helper for internal-only routes (reconciliation, ops).
4. For each edited route, add a unit test: (a) same-client_id returns 200, (b) cross-client_id returns 403, (c) internal caller bypasses.
5. Emit `REPORTING_ENTITLEMENT_DENIED` event on every 403 rejection with caller.org_id + requested client_id + route name. Add the event to UTL `STANDARD_LIFECYCLE_EVENTS` if not already there.
6. `cd client-reporting-api && bash scripts/quality-gates.sh` must pass. Coverage ratchet held.

**Acceptance:**
- Every `client_id`-scoped route enforces entitlement
- `REPORTING_ENTITLEMENT_DENIED` event fires on every denial
- Red-team test: an external client's API key reading another client's data returns 403 (verify in staging via `curl` once deployed)
- QG green

## Workstream D — fund-admin persistence swap-in (Firestore)  [code + infra]

Dependency: A (Cloud Run service exists so Firestore can be wired in).

Plan: `plans/active/fund_administration_persistence_swap_in_2026_04_22.plan.md`.

**Steps:**
1. Provision Firestore Native mode database in `central-element-323112` project (region `asia-northeast1`). Check first — it might already exist from earlier work.
2. Add `FirestorePersistenceStore` impl satisfying the existing `PersistenceStore` Protocol. Collections: `fund_admin_subscriptions`, `fund_admin_redemptions`, `fund_admin_allocations`. Document id = resource_id.
3. Wire via config: `PERSISTENCE_BACKEND` env var picks impl (`memory` default, `firestore` for staging/prod). Firestore client uses Application Default Credentials via Workload Identity (the Cloud Run service account).
4. Unit test against the Firestore emulator (`gcloud emulators firestore start`).
5. Integration test in staging: subscription → approve → settle → restart Cloud Run service → confirm history still there.
6. Update the Cloud Run service env in Workstream A deploy to `PERSISTENCE_BACKEND=firestore`.

**Acceptance:**
- Service survives restart with state intact in staging
- Firestore collections visible in Firebase console
- `cd fund-administration-service && bash scripts/quality-gates.sh` green with Firestore emulator fixture
- Integration smoke test passes end-to-end

## Workstream E — POD integration wiring (adapters only; gated on POD contract)  [code]

Dependency: A, D.

Plan: `plans/active/pod_crypto_administrator_integration_2026_04_22.plan.md`.

**Scope for THIS dispatch — adapters only, no real POD creds yet.** Real POD auth + contract is a business task; this dispatch only lands the Protocol + real-ish implementations behind a feature flag so that flipping to POD creds later is a config change, not a rewrite.

**Steps:**
1. Add `PodClient` Protocol to `fund_administration_service/integrations/pod/client.py` — method surface: `fetch_investor_aml_status(investor_id) → AmlStatus`, `fetch_nav(fund_id, as_of) → NavSnapshot`, `submit_withdrawal(redemption_id, destination, amount) → PodWithdrawalReceipt`, `fetch_withdrawal_status(receipt_id) → WithdrawalStatus`.
2. Add `HttpPodClient` impl using httpx with auth-header injection (secret from Secret Manager via `ApiKeyReloader`). Rate-limit + retry with exponential backoff per codex Secret Manager + shard-level-failure-isolation rules.
3. Add `SandboxPodClient` impl returning deterministic fixtures so local dev + CI works without real POD.
4. Swap `AmlKycGate` / `NavProvider` / `SettlementExecutor` to route through the `PodClient` Protocol. Sandbox impl auto-approves, returns a deterministic NAV, and logs fake withdrawal receipts. Real impl is wired but gated on `POD_INTEGRATION_MODE=real` env var (defaults to `sandbox`).
5. Add `FundTrack` enum to UAC `fund_administration`: `CRYPTO_SPOT`, `CRYPTO_DERIVATIVES`, `TRADFI_PENDING`. Thread through `AllocatorSubscription` / `AllocatorRedemption` as a new optional `fund_track: FundTrack | None = None` field (additive, default None for back-compat). Fund-track resolver (Workstream B) populates it.
6. Circuit breaker around PodClient calls — on POD unreachability, queue subscription/redemption as PENDING and emit a `POD_UNAVAILABLE` alert event (add to UTL STANDARD_LIFECYCLE_EVENTS). Do NOT fail the request.
7. Tests: `responses` library faking POD; both sandbox + real impl exercised.

**Acceptance:**
- Feature flag `POD_INTEGRATION_MODE=sandbox` (default) runs the whole flow with deterministic fake POD
- `POD_INTEGRATION_MODE=real` fails fast if `POD_API_URL` + `POD_API_KEY_SECRET_NAME` are unset
- Fund-track resolver (from Workstream B) populates AllocatorSubscription.fund_track correctly
- UAC + fund-administration-service + UTL QG all green

## Workstream F — Report-back (last; only after A-E are all green)

Prepare a status block for the operator covering:
1. Cloud Run staging URL for fund-administration-service + `/healthz` response.
2. Firebase Firestore collections created + row count per collection (post-smoke).
3. CRA entitlement audit: list of routes updated, red-team test results.
4. Fund-track resolver test matrix + example recommendations.
5. Briefings copy: side-by-side diff of the old Pooled section vs new crypto-spot / crypto-derivatives split.
6. POD integration mode: sandbox vs real wiring state; what's needed to flip to real.
7. All commit SHAs per repo (final tip + diff-from-start).
8. Any items deferred + why.

# Cross-cutting protocol

- **Push protocol**: after each logical chunk lands (per repo), `git push origin live-defi-rollout`. Do NOT `quickmerge --agent` during this dispatch. PRs + semver bumps come later once the parallel-session churn settles.
- **Upstream dep-repo dirty check**: before pushing a consumer repo, `cd <dep-repo> && git status` on UAC/UTL. If dep is dirty, (a) proceed if your changes don't touch the dirty surface AND your pushed branch links to `origin/<dep>` at its last-pushed tip, (b) otherwise pause + report.
- **Conventional commit types**: `feat build chore ci docs fix perf refactor revert style test`. Never `plans:`.
- **Secret handling**: never commit secret values; always `gcloud secrets create` + reference by name.
- **MCP Playwright**: use liberally for UI verification — it's much faster than typing test scripts and running vitest against a dev server for exploratory QA.
- **Autonomous loop**: when a test fails, fix + re-run. Do not report "test failing, need help" unless (a) the fix requires a decision you cannot make autonomously, (b) the test asserts against external service state you cannot mutate, or (c) 3 fix attempts have failed.

# Out of scope (operator task, not agent)

- TradFi Pooled administrator selection — see `plans/active/tradfi_fund_administrator_selection_2026_04_22.plan.md` (RFP + contract negotiation is business-only).
- Real POD contract signing + production credentials — business-only; this dispatch lands the adapter wiring only.
- Production Cloud Run deploy (vs staging) — do not deploy to a `main`-merged prod config without explicit operator instruction. Staging only.

Go.
````

<<<END PASTE>>>

# Operator notes

- Single-session dispatch estimated ~3-4 hours of wall time + 1-2 hours of GCP operator side-work (trigger creation,
  service-account IAM, Firestore DB provisioning).
- The POD integration (Workstream E) lands the code scaffolding but defers real integration until a POD contract is
  signed. That's the intended split: adapters + Protocol now, real creds later.
- TradFi administrator selection is NOT in this dispatch. Operator / business runs that as a separate RFP process (see
  `tradfi_fund_administrator_selection_2026_04_22.plan.md`).
- Expect parallel-session churn during the dispatch. The prompt instructs the agent to push-only (no quickmerge) so PR
  cleanup is deferred.

# What to do after the dispatch returns

1. Review the Workstream F report block.
2. Run the Phase 6 sign-off walkthrough (`plans/active/fund_administration_signoff_walkthrough_2026_04_22.md`) against
   staging.
3. Sign off or capture defects.
4. Start the POD contract / TradFi RFP conversations separately.
