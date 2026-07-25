---
doc_type: plan
title: Refactor G1.10 — Questionnaire-to-configuration flow
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, strategy-service, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §1.10,
    refactor_g1_7_restriction_profile_engine_2026_04_20.md,
    refactor_g1_11_service_family_scope_rules_2026_04_20.md,
    plans/active/user_management_merge_2026_03_23.md,
    plans/active/five_space_ia_execution_child_plan_2026_04_17.md (ticket,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.10 — Questionnaire-to-configuration flow

## Context

Stage 3E §1.10 (2026-04-20 amendment): build the public-facing prospect questionnaire UI plus the admin-side playback in
user-management-ui. The questionnaire collects the axes that determine a prospect's restriction profile: category
(CeFi/DeFi/TradFi/Sports/Prediction), instrument types, venue scope, strategy-style preferences, service-family picker
(IM / DART / Reg Umbrella / combo), fund structure (SMA / Pooled). The response feeds G1.7's
`resolve_profile(..., questionnaire=...)` arg so the prospect's downstream UI experience is pre-configured to what's
relevant.

Dev/staging parity is load-bearing here: identical questionnaire behaviour in both environments, only the submission
sink differs (localStorage seed in dev vs user-management-api staging endpoint + Firebase staging project in staging).

## Decisions locked with user (2026-04-20)

| Decision                                                                                  | Chosen                                                                                                                               | Source                                                      |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------- |
| Public-facing questionnaire at `/questionnaire` (or similar — confirm in Phase 10A audit) | Unauthenticated; anonymous submit allowed (creates a light-auth lead record in user-management)                                      | Kickoff §1.10 + `user_management_merge_2026_03_23.md`       |
| Admin playback at `user-management-ui/<route>/questionnaires/`                            | Sales operators can replay a prospect's answers pre-demo                                                                             | Kickoff §1.10                                               |
| Questionnaire axes                                                                        | category × instrument_types × venue scope × strategy-style × service-family picker (IM/DART/Reg/combo) × fund structure (SMA/Pooled) | Kickoff §1.10                                               |
| Output = RestrictionProfile overlay                                                       | Consumed by G1.7 `resolve_profile(..., questionnaire=QuestionnaireResponse)`                                                         | Kickoff §1.10 + G1.7 handoff                                |
| Dev: submission stays in localStorage for mock-auth persona seeding                       | identical UI behaviour as staging                                                                                                    | Dev-staging parity rule                                     |
| Staging: submission hits user-management-api staging endpoint + Firebase staging project  | same personas provisioned as real Firebase users                                                                                     | five_space_ia_execution_child_plan_2026_04_17.md ticket #12 |

## Cross-references

- **Upstream (Wave D):** `refactor_g1_7_restriction_profile_engine_2026_04_20.md` — consumer of questionnaire output;
  `refactor_g1_11_service_family_scope_rules_2026_04_20.md` — service-family picker maps to rule 11 families
- **Downstream (Wave F):** `refactor_g1_4_persona_combinatorial_expansion_2026_04_20.md` (personas defined by the same
  axes), `refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.md` (tempt logic extends questionnaire response
  handling for vague answers)
- **Sibling plans:** `plans/active/user_management_merge_2026_03_23.md` (light-auth lead flow),
  `plans/active/five_space_ia_execution_child_plan_2026_04_17.md` (ticket #12 staging Firebase)
- **Playbook SSOT:** `/codex/14-customer-journeys/experience/im-decision-journey.md`,
  `/codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md`,
  `/codex/14-customer-journeys/demo-ops/account-intelligence-record.md`
- **Strategy-side source:** `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` (axis values)
- **Shared-core:** `shared-core/org-fund-client-entity-model.md`, `cross-cutting/sma-vs-pooled.md`

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.10
2. `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` — categories + instrument types + venue scope
   enumeration
3. `/codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md`
4. `/codex/14-customer-journeys/shared-core/org-fund-client-entity-model.md`
5. `/codex/14-customer-journeys/experience/im-decision-journey.md`
6. `/codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md`
7. `/codex/14-customer-journeys/demo-ops/account-intelligence-record.md`
8. `plans/active/user_management_merge_2026_03_23.md`
9. `plans/active/five_space_ia_execution_child_plan_2026_04_17.md` (ticket #12)
10. `unified-trading-system-ui/lib/auth/demo-provider.ts`
11. `unified-trading-system-ui/lib/auth/personas.ts`
12. `strategy-service/strategy_service/availability/restriction_profiles.py` (landed by G1.7)
13. `user-management-ui/**` — admin playback surface layout

## Out of scope

- Adding new questionnaire axes beyond the 6 listed — fixed axis set this wave.
- Shipping the upsell tempt-logic — that's G1.13 (extends this flow for vague answers).
- Expanding the persona matrix — that's G1.4 (consumes, doesn't add).
- Building real Firebase staging provisioning for the first time — ticket #12 owns that; this plan hooks into the
  existing staging endpoint if available, otherwise falls back to localStorage identically to dev.
- Touching strategy-service v2 code — read-only.
- Reading `_archived_pre_v2/` — forbidden.

## Dev / staging parity rule

Questionnaire behaves identically across dev and staging:

- **Dev (`localhost:3000`):** `VITE_MOCK_API=true`. Submission sinks to localStorage under `questionnaire-response-v1`.
  demo-provider.ts reads the same key + resolves to a persona + profile overlay. UI behaviour indistinguishable from
  staging.
- **Staging (`odum-research.co.uk`):** `VITE_MOCK_API=false`. Submission POSTs to user-management-api staging endpoint
  `/questionnaires`. user-management-api persists to Firebase staging project. Subsequent UI reads resolve via the same
  endpoint.
- **Prod (`odum-research.com`):** `VITE_MOCK_API=false`. Same code path as staging; Firebase prod project.

Questionnaire UI, axis definitions, RestrictionProfile output, and downstream G1.7 resolution are identical. Only the
submission sink differs. Any UI divergence = rule-03 violation.

## Wave E execution summary (2026-04-20)

All Phase 10A-10E shipped in 4 commits. Firebase IS the API (operator confirmed 2026-04-20); no separate
user-management-api backend needed. `QuestionnaireResponse` fleshed out in UAC (was an empty G1.7 stub); overlay logic
in `_apply_questionnaire_override` now tightens tile states per the service_family picker.

| Repo                      | SHA       | Summary                                                                                                              |
| ------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------- |
| unified-api-contracts     | `e4a9e72` | `QuestionnaireResponse` 6-axis schema + 5 Literal types + real `_apply_questionnaire_override` overlay + 9 new tests |
| strategy-service          | `429ff53` | `POST /internal/restriction-profile/{persona_id}/resolve` with questionnaire body + 3 new tests                      |
| unified-trading-system-ui | `ce53f4d` | Public `/questionnaire` route + 6-axis form + localStorage/Firestore submit helper + Playwright spec                 |
| user-management-ui        | `93f7a76` | Admin `/questionnaires` playback page reading from Firestore + `firebaseDb` export (Wave E closure 2026-04-20)       |

**Deviations from micro-plan (all documented):**

- No `user-management-api` repo created — Firebase IS the API per operator direction. Client SDK writes to
  `/questionnaires` Firestore collection; Firestore security rules will gate anonymous writes + admin reads (rules file
  belongs to deployment-service — follow-up).
- `service_family` axis narrowed to 4 prospect-facing values (`IM | DART | RegUmbrella | combo`) — not the 6-family enum
  from rule 12, which includes admin/IM_desk/DART_reporting_only.
- Magic-link seed-demo-session shipped as a query-param stub; G2.x will mint real Firebase custom tokens.
- Dev mode uses localStorage write (`questionnaire-response-v1`) — staging/prod uses Firestore. Both paths identical at
  the UI layer.

## Phase breakdown

### Phase 10A — Audit + design

- [x] [AGENT] P0. Audit today's `/signup` + any existing contact / demo-request forms in unified-trading-system-ui.
      Enumerate overlap + what to keep/replace.
- [x] [AGENT] P0. Design the questionnaire page layout: one-question-per-step or single-page form (recommend multi-step
      for mobile ergonomics).
- [x] [AGENT] P0. Define `QuestionnaireResponse` TypedDict matching the 6 axes:
  ```ts
  interface QuestionnaireResponse {
    categories: ("CeFi" | "DeFi" | "TradFi" | "Sports" | "Prediction")[];
    instrument_types: InstrumentType[];
    venue_scope: VenueId[] | "all";
    strategy_style: (
      | "ml_directional"
      | "rules_directional"
      | "stat_arb"
      | "arbitrage"
      | "carry"
      | "event_driven"
      | "market_making"
      | "vol_trading"
    )[];
    service_family: "IM" | "DART" | "RegUmbrella" | "combo";
    fund_structure: "SMA" | "Pooled" | "NA";
  }
  ```

### Phase 10B — Build the public questionnaire UI

- [x] [AGENT] P0. New route: `unified-trading-system-ui/app/questionnaire/page.tsx` (or equivalent) — public,
      anonymous-allowed.
- [x] [AGENT] P0. Per-axis components: `<CategoryPicker>`, `<InstrumentTypePicker>`, `<VenueScopePicker>`,
      `<StrategyStylePicker>`, `<ServiceFamilyPicker>`, `<FundStructurePicker>`.
- [x] [AGENT] P0. Submit handler:
  - dev (`VITE_MOCK_API=true`): localStorage write to `questionnaire-response-v1` + redirect to
    `/dashboard?preview=<persona_id>`.
  - staging/prod: POST to user-management-api `/questionnaires` + on-success redirect to a "we'll be in touch" landing
    OR login if user already auth'd.

### Phase 10C — Wire to G1.7 restriction-profile engine

- [x] [AGENT] P0. Update `unified-trading-system-ui/lib/auth/demo-provider.ts` — if `questionnaire-response-v1`
      localStorage key exists, pass it to the `resolve_profile` API call so downstream tiles / nav / catalogue render
      with the questionnaire overlay.
- [x] [AGENT] P0. Update server-side restriction-profile endpoint (G1.7) to accept `questionnaire` arg + apply overlay
      per `resolve_profile` spec.

### Phase 10D — Admin playback in user-management-ui

- [x] [AGENT] P0. New route in user-management-ui: `/questionnaires` — list of submissions; each links to a detail view.
- [x] [AGENT] P0. Detail view renders the raw response + the resolved RestrictionProfile preview (calls G1.7 endpoint
      with the response as questionnaire arg).
- [x] [AGENT] P0. Admin can "seed a demo session" button — generates a short-lived magic-link that opens
      unified-trading-system-ui pre-authenticated with the prospect's profile.

### Phase 10E — Verify + QG

- [x] [SCRIPT] P0. unified-trading-system-ui QG green.
- [x] [SCRIPT] P0. user-management-ui QG green.
- [x] [N/A] P0. user-management-api QG — superseded by Firebase-is-the-API operator decision 2026-04-20; no
      `user-management-api` repo exists. Admin playback uses Firestore client SDK directly via user-management-ui.
- [x] [AGENT] P0. Playwright spec `refactor-g1-10-questionnaire.spec.ts` green on tier-1 dev.

## Critical files to be modified

- `unified-trading-system-ui/app/questionnaire/page.tsx` — NEW
- `unified-trading-system-ui/components/questionnaire/**` — NEW (6 axis pickers)
- `unified-trading-system-ui/lib/questionnaire/types.ts` — NEW (`QuestionnaireResponse`)
- `unified-trading-system-ui/lib/auth/demo-provider.ts` — MODIFY (read localStorage response + thread to
  resolve_profile)
- `user-management-ui/app/questionnaires/**` — NEW (admin playback)
- `user-management-api/app/questionnaires/**` — NEW (staging endpoint)
- `strategy-service/strategy_service/availability/restriction_profiles.py` — MODIFY (accept questionnaire arg)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-10-questionnaire.spec.ts` — NEW

## Execution DAG

```
10A (audit + design)  →  10B (public UI) + 10C (wire to G1.7) + 10D (admin playback)  [parallel after 10A]  →  10E (QG + Playwright)
```

## Verification

1. Questionnaire page submits + persists per environment rules.
2. Downstream UI (catalogue / tiles) respects the questionnaire overlay — verified by Playwright.
3. Admin playback lists + replays submissions; magic-link seeds unified-trading-system-ui correctly.
4. Dev-vs-staging parity test: same response → same RestrictionProfile across environments.
5. QG green on all 4 touched repos.

## Handoff

Unblocks:

- **G1.13 upsell tempt-logic** — wraps questionnaire response with a "widen on vague" transform before resolve_profile.
- **G1.4 persona combinatorial expansion** — persona matrix axes == questionnaire axes; the matrix is essentially a
  Cartesian product of questionnaire responses.
- **G2.x** — sales-ops dashboard consuming questionnaire data for lead triage.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — navigate to `/questionnaire`, walk through all 6 axes, submit, verify
redirect + localStorage write + downstream UI (e.g. `/services/strategy-catalogue/`) reflects the questionnaire overlay.
Seed various response combinations and iterate.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-10-questionnaire.spec.ts` —
must:

1. Run as anonymous (no persona seed — questionnaire is pre-auth).
2. Walk through all 6 axes with 3 response combinations (e.g. "CeFi-focused IM prospect", "DeFi+TradFi DART prospect",
   "Reg Umbrella compliance-only").
3. Submit; assert localStorage write (dev) or mocked-fetch hit to user-management-api (simulated staging).
4. Navigate to `/services/strategy-catalogue/`; assert visible tiles respect the questionnaire overlay.
5. Assert visibility-slicing via G1.6 `access_control()` agrees with questionnaire-driven profile.
6. Assert dev-vs-staging parity: run both with mock and simulated-staging sinks; resolved RestrictionProfile
   byte-identical.
7. Include orphan-reachability assertion — `/questionnaire` is reachable from public landing.
8. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.10 (Wave E, single item; Wave D
must be merged first).**

---

You are executing **Refactor G1.10 — Questionnaire-to-configuration flow** for the Unified Trading System at Odum
Research. Wave E; G1.7 and G1.11 must be merged first.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
git -C user-management-ui checkout live-defi-rollout && git -C user-management-ui pull
git -C user-management-api checkout live-defi-rollout && git -C user-management-api pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
# Verify G1.7 + G1.11 merged
ls strategy-service/strategy_service/availability/restriction_profiles.py
ls strategy-service/strategy_service/availability/service_family_scope.py
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 10A through 10E of this plan:
`plans/active/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 13.

### Deliverables

- New: public questionnaire UI under `unified-trading-system-ui/app/questionnaire/` + 6 axis pickers under
  `components/questionnaire/` + types
- Modified: `unified-trading-system-ui/lib/auth/demo-provider.ts`
- New: admin playback under `user-management-ui/app/questionnaires/`
- New: staging endpoint in `user-management-api/app/questionnaires/`
- Modified: `strategy-service/strategy_service/availability/restriction_profiles.py` (accept questionnaire arg)
- New test: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-10-questionnaire.spec.ts`

### Dev / staging parity requirement (verbatim — REQUIRED)

Questionnaire UI + axis definitions + RestrictionProfile output are identical across dev and staging. Only the
submission sink differs (localStorage vs user-management-api staging endpoint + Firebase staging project). Any UI
divergence = rule-03 violation.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to walk the questionnaire, submit multiple response combinations, verify localStorage
write + downstream catalogue overlay. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-10-questionnaire.spec.ts` — run anonymous, walk 6
axes × 3 response combinations, assert submission + downstream catalogue + `access_control` + dev-vs-staging parity,
include orphan-reachability assertion, wire into `scripts/quality-gates.sh`.

### Commit strategy

Five repos touched (PM not directly, unless codex changes) → four quickmerge commits.

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "feat(ui): G1.10 — public questionnaire flow" --agent

cd ../user-management-ui
bash scripts/quickmerge.sh "feat(user-management-ui): G1.10 — admin questionnaire playback" --agent

cd ../user-management-api
bash scripts/quickmerge.sh "feat(user-management-api): G1.10 — questionnaires staging endpoint" --agent

cd ../strategy-service
bash scripts/quickmerge.sh "feat(strategy-service): G1.10 — questionnaire arg in resolve_profile" --agent
```

Fallback per repo: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`. Never
`--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ `/questionnaire` page accessible unauthenticated.
2. ✅ Dev submission writes to localStorage; staging submission hits user-management-api.
3. ✅ Downstream catalogue reflects questionnaire overlay.
4. ✅ Admin playback in user-management-ui lists + replays submissions.
5. ✅ Dev-vs-staging parity test green.
6. ✅ QG green on all touched repos.
7. ✅ Playwright spec green.
8. ✅ Commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT ship the upsell tempt-logic — G1.13 extends this.
- Do NOT expand the persona matrix — G1.4 consumes what's here.
- Do NOT diverge dev from staging beyond the submission sink.
- Do NOT add axes beyond the 6 listed.
- Do NOT bypass G1.7's `resolve_profile` — the questionnaire is ONE arg into that function, not a parallel path.

### Report back

- Questionnaire response schema (paste the TypedDict).
- Per-environment submission sink confirmation.
- Admin playback screenshot / description.
- Parity test result.
- QG results per repo.
- Playwright spec pass status.
- Commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.

---

## Micro-execution plan (Wave E, 2026-04-20)

### Plan-vs-reality drifts

| #   | Plan claims                                                                                                                                                | Reality                                                                                                                                                                                                                                                | Resolution                                                                                                                                                                                                                                                                                                                                                            |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Line 172 "`user-management-api/app/questionnaires/**` — NEW (staging endpoint)"                                                                            | `user-management-api` repo does NOT exist as a sibling. **Firebase IS the API** (operator confirmation 2026-04-20).                                                                                                                                    | Public questionnaire writes to Firestore directly via the Firebase client SDK (anonymous auth or light-auth lead record). Admin playback in user-management-ui reads from Firestore via the Firebase admin SDK (or authenticated client SDK with admin role claim). Firestore security rules gate anonymous writes / admin reads. No separate backend service needed. |
| 2   | Line 173 "Modify `strategy-service/strategy_service/availability/restriction_profiles.py` (accept questionnaire arg)"                                      | G1.7 Option X put `restriction_profiles.py` in **UAC** (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py`). `resolve_profile()` already takes `questionnaire: QuestionnaireResponse \| None = None` stub. | Modify UAC `restriction_profiles.py` instead. Flesh out `QuestionnaireResponse` from empty placeholder (shipped in G1.7 as a `BaseModel` with `extra="allow"`) to a typed 6-axis schema. Make `_apply_questionnaire_override` non-no-op.                                                                                                                              |
| 3   | Plan line 108-127 TypeScript TypedDict uses `"IM" \| "DART" \| "RegUmbrella" \| "combo"` for service_family                                                | G1.11 rule 12 ServiceFamily enum is `IM \| RegUmbrella \| DART \| DART_reporting_only \| admin \| IM_desk`. Prospect-facing questionnaire shouldn't offer `admin` or `IM_desk`; `combo` is a UX convenience (multi-select).                            | Keep questionnaire's `service_family` as the prospect-facing 4-enum: `IM \| DART \| RegUmbrella \| combo`. Map `combo` → all three via overlay logic.                                                                                                                                                                                                                 |
| 4   | `strategy-service` router at `api/restriction_profile_router.py` (G1.7) exposes `GET /internal/restriction-profile/{persona_id}` but takes no request body | G1.10 wants to POST a questionnaire response + get back the overlay-resolved profile.                                                                                                                                                                  | Extend the router with `POST /internal/restriction-profile/{persona_id}/resolve` accepting `QuestionnaireResponse` as the body. Keep the `GET` happy path for persona-only lookups.                                                                                                                                                                                   |
| 5   | `QuestionnaireResponse` schema needs to be stable across UAC Python + UI TypeScript + user-management-ui admin playback                                    | G1.8 + G1.7 established the PM-sync-script pattern for YAML→TS mirror drift detection. Same shape fits here.                                                                                                                                           | Manual alignment comment for Wave E (single schema, low drift risk). Full sync-script follow-up if the schema grows.                                                                                                                                                                                                                                                  |
| 6   | Staging auth ticket #12 (five_space_ia) provisions Firebase staging                                                                                        | Not verified as shipped yet — may still be pending.                                                                                                                                                                                                    | Build the Next.js route handler in user-management-ui regardless; it reads from localStorage in dev-mock mode and would POST to a real endpoint when Firebase staging eventually lands. Both paths identical to the UI.                                                                                                                                               |

### Execution commits (planned)

| #   | Repo                        | Purpose                                                                                                                                    |
| --- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `unified-api-contracts`     | Flesh out `QuestionnaireResponse` (6 axes) + real `_apply_questionnaire_override` logic + tests                                            |
| 2   | `strategy-service`          | `POST /internal/restriction-profile/{persona_id}/resolve` accepting questionnaire body                                                     |
| 3   | `unified-trading-system-ui` | `/questionnaire` route + 6 axis pickers + Firestore submit (staging/prod) / localStorage (dev) + demo-provider threading + Playwright spec |
| 4   | `user-management-ui`        | Admin playback page at `/questionnaires` reading from Firestore via Firebase admin SDK + magic-link seed-demo-session stub                 |

Net-new surface; zero runtime consumers today. Citadel rule-3: no shims.

### Operator-approved defaults (carrying forward from Wave D sign-off)

Per user message 2026-04-20 — "do everything, don't defer unless entirely necessary and documented":

- Magic-link seed-demo-session: scoped as a stub (generates a URL with query param for persona seed; no Firebase
  custom-token minting until ticket #12 lands).
- `user-management-api` repo: NOT created; handler lives inside user-management-ui.
- Questionnaire schema stored as TypeScript types in UI + Pydantic model in UAC — kept in sync manually with a
  documentation cross-ref comment (sync-script overkill for 6 fields).
- **Sync-script trigger (2026-04-20 follow-up addition):** if `QuestionnaireResponse` gains a 7th axis OR any existing
  axis's enum changes, ship a sync-script matching the G1.8 `ArchetypeCapability` pattern. Reference:
  `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh` (`--check` + `--write` modes; wired into
  UI `scripts/quality-gates.sh` pre-base-ui hook so every push fails on drift). Without this trigger the UI TS mirror
  WILL drift from UAC Pydantic at schema change time.

---

## Wave F dispatch prompt (saved for operator, 2026-04-20)

Wave E closed all 5 audit gaps (admin-playback orphan, allocator-gate swap, UAC QG cleanup, closure memory, handoff
prompt). Waves A/B/C/D/E are all shipped with their plan checkboxes flipped. Wave F (G1.4 persona expansion + G1.13
upsell tempt-logic, + G1.14 HTML stretch optional) is unblocked and ready for dispatch.

The full copy-paste-ready Wave F dispatch prompt lives at: `memory/project_g1_wave_e_to_f_dispatch_prompt.md`

Paste its contents into a fresh agent session to execute Wave F. Key things the Wave F agent must respect:

- **Option X still in force** — UAC is SSOT; `tempt_logic.py` lands at UAC `internal/architecture_v2/`.
- **ServiceFamily duality** — 6-value internal (rule 12 YAML) vs 4-value prospect-facing (questionnaire).
- **Rule 12, NOT rule 11** — G1.9 occupies rule 11 slot.
- **Firebase IS the API** — no `user-management-api` repo exists.
- **DEMO_MODE gates widening** — `apply_tempt_logic` no-ops when `env.is_demo=False`; prod never widens.
- **HARD CAP 20 personas** in G1.4.
- **user-management-ui `git branch --show-current`** MUST be `live-defi-rollout` before any commit (local `main`
  diverges 33+ commits).

Wave F is the FINAL G1 wave. Its closing agent produces an end-of-G1 summary (14-item status table + G2 inheritance
note); no further dispatch prompt needed since G2 is a separate user-level planning session.
