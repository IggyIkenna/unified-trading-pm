---
doc_type: plan
title: Data-status catalogue explorer — Phase 2 true-catalogue (expected-universe) source
summary: >-
  Phase-2 follow-up forked from data_status_page_ux_and_canonicalisation_2026_07_16.md's P6 (catalogue explorer). Phase
  1 ("captured instruments, availability-derived") is shipped. This plan builds the true-catalogue / expected-universe
  side so the explorer can also show instruments that EXIST but were never captured — a published instruments-service
  projection read by deployment-api (T4-safe: artifact contract, no service→service import), not a swap of the phase-1
  read path.
status: active
nature: process
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [cross-cutting]; forked from
  # data_status_page_ux_and_canonicalisation_2026_07_16.md (retagged ui same pass), same deployment-ui/deployment-api scope
stage: [meta]
repos: [deployment-ui, deployment-api, instruments-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [data-status, catalogue, instruments-service, canonicalisation, honest-coverage, single-walk]
related:
  [
    /plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    /plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: ui_developer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan-hygiene line-cap remediation (2026-07-24) — forked out of
  data_status_page_ux_and_canonicalisation_2026_07_16.md's P6 section per
  plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #10 (bucket c, clean-partition). The parent plan's own
  P6 phase-2 todo (below) is moved here verbatim, unedited; only frontmatter + this orienting header are new.
context_scope:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    deployment-api/deployment_api/routes/data_status/_catalogue.py,
    instruments-service/scripts/enumerate_expected_universe.py,
  ]
---

# Data-status catalogue explorer — Phase 2 true-catalogue (expected-universe) source

> **Human/LOCAL plan** (`assigned_vm: NA`) — forked 2026-07-24 out of
> `/plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md` (P6 — Instrument catalogue explorer)
> as part of the plan line-cap remediation. That parent plan retains ~2000 lines of shipped history (P1-P10, including
> P6 Phase 1) as the durable record — read it for full P6 context (design guide, what exists, the MVP predicate, the
> phase-1 shipped commits). This child carries forward only the one still-open workstream: the Phase-2 true-catalogue
> source. The todo below is moved **verbatim** from the parent — nothing summarized or rewritten.

## Codex SSOTs (this plan references, does not duplicate)

- `/codex/04-architecture/tier-and-import-architecture.md` — T4 (no service→service deps; integrate by API
  contract/published artifact, same pattern MTDS uses to consume IS's outputs).
- `/codex/02-data/availability-manifest-and-data-status.md` + `…/honest-absence-downstream-handling.md` — why the
  identity-catalogue shortcut (prototyped + reverted, see below) would have fabricated `capture_status` for sports.
- `/codex/06-coding-standards/script-homes.md` — `instruments-service/scripts/enumerate_expected_universe.py` +
  `scripts/expected_universe.py` already compute the expected universe this plan's projection publishes from.

## Background (orienting summary, not a relocation of history — see parent for the shipped Phase-1 record)

Phase 1 shipped `GET /data-status/catalogue` (+ CSV twin) in deployment-api, built on `read_availability_index`
(single-walk discipline), labeled honestly as **"captured instruments (availability-derived)"** — parent plan
@1e3c7b4/@90eba8c/@9648f42/@57d913d/@8958345, operator-decided "BOTH, phased" 2026-07-16. That label is correct but
incomplete: it can only ever show what was captured, never what exists in the catalogue but was never captured. This
plan is that other half.

## Open todo (moved verbatim from the parent, 2026-07-24)

- [ ] [BACKEND] P3. _(phase 2)_ True-catalogue source — add a deployment-api→instruments-service read path OR a
      manifest-backed catalogue projection so the explorer can list instruments that EXIST in the catalogue (not just
      captured). Respect T4 (integrate by contract/projection, not a direct service→service import).

      **NOT DONE — but DESIGNED + de-risked on real data 2026-07-17. The obvious implementation was investigated,
                  PROTOTYPED, and DELIBERATELY REVERTED as wrong; read this before starting, it will save you the same detour.**

                  **1. The tempting shortcut, and why it is NOT the answer.** The natural move is to extend
                  `_IDENTITY_CATALOGUE_ASSET_GROUPS` (`routes/data_status/_catalogue.py`) so prediction+sports also read
                  `prod/catalog.parquet`, since cefi/defi/tradfi already do post-@62cc10f and the gap looks enormous — measured live:
                  | AG | explorer shows today | `prod/catalog.parquet` | missing | object |
                  | --- | --- | --- | --- | --- |
                  | sports | **1,786** non-blank ids | **27,250** | 25,464 (94%) | 0.6 MB |
                  | prediction | 12,921 non-blank ids (**and only 79 survive `_dedupe_latest`** — see finding 4) | **2,673,230** | ~2.66M (99.5%) | 184.5 MB |
                  I prototyped exactly this for sports (0.6 MB, so no latency cost) and **reverted it**, because driving the shipped
                  code against real GCS showed it trades correctness for correctness rather than winning:
                  - the sports identity catalogue has **`venue=''`** on every row (sports keys on `league_id`, not venue) → the
                  explorer's venue narrow would silently return nothing for sports, a regression vs the `_index` path which carries
                  a real venue;
                  - it carries **no `capture_status`/`error_reason`/`attempted_at`** (manifest-only per-shard fields), which the
                  identity path defaults to `captured`/`""`/`""`. That default is defensible for cefi/defi/tradfi (their `_index`
                  has literally zero per-instrument rows, so it is "something vs nothing"), but for sports it would **stamp
                  `captured` on ~25k rows whose real per-day status the `_index` already knows** — a fabricated status, which is
                  precisely what the honest-absence rule forbids;
                  - its `instrument_type` is lowercase legacy (`'team'`) — see the sports non-canonical todo above.

                  **2. The load-bearing realisation (this is the actual reason phase-2 is "architecturally open-ended").**
                  `prod/catalog.parquet` is **not** the true catalogue. It is *"every instrument we ever CAPTURED, rolled up with
                  lifecycle windows"* (`build_instrument_catalogue.py` walks the `by_date` capture snapshots). So it **cannot answer
                  "what EXISTS but was never captured" for ANY asset group** — swapping sources just changes *which* captured-derived
                  projection you read. The phase-1 label "captured instruments (availability-derived)" therefore stays HONEST even
                  for the identity-catalogue asset groups. This todo's ask genuinely requires the **expected-universe** side.

                  **3. Concrete design direction (T4-safe).** instruments-service already computes the expected universe —
                  `scripts/enumerate_expected_universe.py` + `scripts/expected_universe.py` (and the `expected_unattempted` manifest
                  state is materialised from it by the WRITER). The right phase-2 shape is therefore **a published projection, not a
                  read path**: have instruments-service publish a small per-AG `_catalogue/expected_universe.parquet`
                  (instrument_id + venue/league_id + instrument_type + lifecycle + `is_expected`), and have deployment-api read that
                  ONE bounded object alongside the identity catalogue, tagging each row `exists_in_catalogue` vs `captured`. That
                  integrates by **artifact contract** (exactly like MTDS consumes IS's published outputs) with **no service→service
                  import**, satisfying T4 — whereas a deployment-api→IS HTTP read path would add the T4-banned edge.

                  **4. Prerequisite (found while scoping, must be fixed first or phase-2 inherits it).** `/catalogue` for
                  **prediction** currently reports `total_count=79` on real data — 12,921 non-blank `_index` ids collapse to 79 after
                  `_dedupe_latest`, because prediction `_index` rows key on the cqg BUNDLE, not the per-market instrument. So the
                  Prediction tab of the explorer is effectively empty today and phase-2 should not be built on top of that path.
                  (Distinct from the `/prediction-catalogue` browser, which reads the real 2.67M-row catalogue and works.)

                  **5. Perf constraint (already measured, see the two PERF todos above).** Any prediction phase-2 MUST come with the
                  projected artifact: its catalogue object is 184.5 MB / ~84s cold transpacific, which is exactly why the
                  `/prediction-catalogue` first-hit residual is ~157s. A source swap without a narrowed artifact would import that
                  latency into `/catalogue` too.

## Progress Log

_(none yet — this plan was created 2026-07-24 by the plan line-cap remediation split; the todo above carries its full
prior design history verbatim from the parent plan's Progress Log.)_

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — LOCAL/human plan; the sole todo is self-described
  'architecturally open-ended' with a prerequisite (the prediction /catalogue 79-row collapse) that must be decided
  first.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries) -- dropped script-homes.md,
  added the actual deployment-api catalogue route + the instruments-service expected-universe script the P3 todo builds
  a read path against.
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-a6d668)**: KEEP-NA, valid — same as 2026-07-30; the sole
  todo is self-described architecturally open-ended with a prerequisite (prediction /catalogue 79-row collapse) that
  must be decided first.
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (6 entries).
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, valid — same as 2026-07-30/2026-08-06; the sole todo
  remains self-described architecturally open-ended with the prediction /catalogue 79-row-collapse prerequisite still
  unresolved.
- **context-scout 2026-08-15**: refreshed context_scope (6 entries), no change needed.
