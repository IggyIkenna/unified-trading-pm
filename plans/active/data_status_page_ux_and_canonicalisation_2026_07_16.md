---
doc_type: plan
title: Data-status page — honest-coverage fix (shipped) + UX & canonicalisation follow-ups (P1–P8)
summary:
  Eight operator issues on the instruments-service data-status page (deployment-ui + deployment-api), each
  code/live-verified via a multi-agent audit. P1 (Honest Coverage rendering only DeFi) is ROOT-CAUSED and FIXED — the
  daily writer OOM'd on an 8GB VM and wrote a silent partial coverage.json; RAM bump + writer partial-stamping + card
  banner shipped and verified live. P2–P8 are the remaining designs — new-listings/expiries + prediction catalogue
  browser + instrument-type canonicalisation (SPOT_ASSET already exists in UAC) + drilldown de-duplication + catalogue
  explorer + cefi chain-axis drift + sports league-drilldown consistency. Each point carries a self-contained design
  guide; operator decisions are all resolved.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, instruments-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-status,
    honest-coverage,
    deployment-ui,
    deployment-api,
    instruments,
    canonicalisation,
    prediction,
    sports,
    catalogue,
    ux,
  ]
related:
  [
    data_status_tab_and_downloads_remediation_2026_06_16.md,
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
    instruments_catalogue_incremental_rollup_2026_06_29.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 5.4
assigned_role: ui_developer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: operator request 2026-07-16 (data-status page review) + multi-agent audit workflow wf_872e8051-00a
---

# Data-status page — honest-coverage fix + UX & canonicalisation follow-ups

> **Human/LOCAL plan** (`assigned_vm: NA`) — operator-driven, not AO-dispatched. Source: operator review of
> `/service/instruments-service/data-status` on 2026-07-16 + a 16-agent audit (workflow `wf_872e8051-00a`, findings
> cross-checked against live code, the UAC SSOTs, and live GCS reads). **Every point below is self-contained** — read
> the point's `Design guide`, then do its `- [ ]` todos. Line numbers are 2026-07-16 anchors — always grep-confirm the
> symbol before editing (files drift).

## Codex SSOTs (this plan references, does not duplicate)

- `codex/02-data/honest-coverage-model.md` — Honest Coverage v2 two-layer model (P1, P4).
- `codex/02-data/availability-manifest-and-data-status.md` + `…/honest-absence-downstream-handling.md` — manifest
  shard-atom identity + no-silent-placeholders (P1, P4, P7, P8).
- `unified-api-contracts/.../registry/data_status_axis_matrix.py` — the shard/display axis SSOT: cefi = `("venue",)`,
  defi adds `chain`; sports = `("data_type","league_id")` (P5, P7, P8).
- `unified-api-contracts/.../_instrument_enums.py` — canonical `InstrumentType` (SPOT_PAIR/PERPETUAL/SPOT_ASSET/…) (P4).
- `unified-api-contracts/.../internal/reference/instrument.py` — `InstrumentRecord` address fields (P4-SPOT_ASSET).
- `instruments-service/docs/PREDICTION_INSTRUMENTS.md` — prediction catalogue + `canonical_question_group` (P3).
- `codex/06-coding-standards/ui-testing-layers.md` — the `[UI]` + `pw:L2` gate for every deployment-ui tick.

## Root-cause summary (audit findings, all code/live-verified)

| #   | Issue                                       | Verdict                                                      | Where it lives                                                                          |
| --- | ------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| P1  | Honest Coverage card = DeFi only            | **OOM on 8GB VM → silent partial coverage.json** (FIXED)     | `measure_honest_coverage.py` writer; `_live_coverage.py` endpoint; `HonestCoverageCard` |
| P2  | New listings + upcoming expiries            | Feasible read-only from `catalog.parquet`                    | deployment-api `catalogue_lifecycle` (new) + deployment-ui cards                        |
| P3  | Prediction category dropdown                | Canonical grouping already exists                            | `canonical_question_group` + `PredictionMarketCategory` + a new catalogue browser       |
| P4  | Non-canonical instrument types / SPOT_ASSET | Summary shows RAW manifest values; SPOT_ASSET already in UAC | deployment-ui labels + instruments-service catalogue/SPOT_ASSET population              |
| P5  | Hierarchical drilldown redundant            | Redundant for instruments-service only                       | `DataStatusTab.tsx` (gate one drilldown off for IS)                                     |
| P6  | Catalogue explorer                          | Blocks exist but scattered; no MVP filter on lists           | deployment-api `_instruments.py`/`_csv_export.py` + a new catalogue surface             |
| P7  | CeFi chain axis (solana/zksync)             | Axis-matrix drift confirmed                                  | deployment-api/ui chain-derivation gated on `asset_group=='defi'`                       |
| P8  | Sports league-drilldown inconsistency       | Axis-policy + real TEAMS data-correctness drift              | deployment-api `sports_helpers.py` (reclassify TEAMS) + UI affordance                   |

---

## Execution guide (next agent — READ FIRST)

**Repos + how to run quality gates (QG-green tree is the commit contract):**

- Python repos (`deployment-api`, `instruments-service`, `unified-api-contracts`, `deployment-service`): from the repo
  root, `bash scripts/quality-gates.sh` (full) or `bash scripts/quality-gates.sh --no-fix` when committing only your own
  named files. **Never run `pytest` directly.** No `os.getenv()` / `Any` / `# type: ignore` / inline `gs://` / direct
  `google.cloud`/`boto3`; UTC datetimes; UAC types via `unified_api_contracts.{domain}` (no deep paths).
- `deployment-ui` (React/TS, **no Python tooling**): `npx tsc --noEmit`, `npx eslint <files>`, `npx vitest run <spec>`,
  and the **`[UI]` + `pw:L2` gate** — every UI tick needs a cited Playwright/Vitest regression spec
  (`codex/06-coding-standards/ui-testing-layers.md`). Prettier `.ts/.tsx/.json/.css` before commit.

**Shipping each unit (commit-push-flip in the SAME turn — HARD RULE):**

1. `git status && git diff --cached --stat` (NO path arg) → stage ONLY your files by name (never `git add -A`).
2. Ship code via `bash scripts/quickmerge.sh "<conventional msg>" --agent --files '<paths>'` (lands on
   `live-defi-rollout`, runs the gates). This repo's branch is busy — if quickmerge/commit is blocked by the
   branch-drift hook, `git pull --rebase --autostash origin live-defi-rollout` then retry.
3. In the same turn, flip this plan's checkbox: `- [x] N. ✅ [TAG] … — <repo>@<sha> + Evidence: <test/run>`, and commit
   the plan with the `docs(plans):` prefix. A done claim MUST cite `<repo>@<sha>` + a resolving test/build.

**Recommended order** (points are independent; this front-loads confidence):

1. **Quick wins (no new data, high confidence):** P7 (cefi chain gate) → P5 (drilldown gate) → P4-A (UI label
   normalization). Each is a small, localized change with a pw:L2 spec.
2. **P1 remaining** (deploy the nightly path so the fix is permanent) — small INFRA + a defence-in-depth DATA todo.
3. **P4-B catalogue address columns → SPOT_ASSET** (the enabling projection+regen, then the backfill).
4. **P2** (new-listings/expiries cards) → **P8** (TEAMS reclassify + affordance) → **P3** (prediction browser) → **P6**
   (catalogue explorer).

**Golden rules for this plan specifically:**

- **Shard-atom identity** — never rewrite a manifest grouping/query KEY to make a label prettier (P4). Fix labels at the
  DISPLAY layer, or fix the WRITER + a migration; the query value the UI sends back must stay the raw manifest value.
- **Single-walk discipline** — any NEW whole-corpus GCS walk is review-blocking (P2, P6). Build on
  `read_availability_index` or ONE bounded single-day `_shard_prefix` walk with a `max_results` cap.
- **Honest-absence** — never fabricate a value to fill a gap (P3 titles, P4 CeFi addresses, P8 global entities). A blank
  / slug / explicit "no per-league breakdown" affordance is the honest answer.
- **Trace-first, don't guess** — where a todo says "trace the derivation point" (P7) or "find the predicate" (P5), grep
  then READ the candidate before editing; the audit did not pin every exact line.

---

## Progress Log

### 2026-07-17 — P2/P3 remaining-work session (`/autonomous`) — working the 13 deprioritized follow-ups

Session working the 13 open P2/P3 todos in the Deferred table below. Journal per unit; each ships commit-push-flip.

**Operating context (READ THIS FIRST if you are a fresh/compressed context):** a **second agent is live in this same
checkout** right now — confirmed by mtime, not assumed (`deployment-api/deployment_api/services/fixtures_browser.py` +
`routes/fixtures_browse.py` + `tests/unit/test_fixtures_browser.py` were being edited seconds before this session's
first tool call; they are extending the fixtures browser with a `team=` filter + absolute `start_date`/`end_date`
window). Consequences, all of which bite:

1. **`deployment-api`'s full `quality-gates.sh` is RED and not mine to fix** — the LINT stage fails on that agent's live
   WIP (`fixtures_browse.py` E501, `fixtures_browser.py` RUF100). Every deployment-api unit this session therefore
   scope-verifies (`ruff check` + `ruff format --check` + `basedpyright` + targeted pytest on MY files only) and cites
   the carve-out, same precedent as `12c94be`/`e27ba4b`.
2. **basedpyright is A/B'd against HEAD per unit** rather than trusted absolutely — these files carry pre-existing
   `reportAny`/`dict[Hashable, Any]` errors, so "0 errors" is unachievable; "**0 NEW** errors vs the HEAD copy of the
   same file" is the real bar and is what each checkbox cites.
3. **quickmerge needs `--skip-preflight`** (the flag it documents "for multi-agent use") because deployment-service
   carries foreign-live `terraform.tfvars` → the dirty-deps pre-flight blocks. Verified safe per unit: that tfvars is a
   features-service-sports Cloud Run image pin, unrelated to anything shipped here. Same carve-out as `@62cc10f`.
4. **Post-ship `git show --name-only` is checked EVERY time** to prove quickmerge's whole-file `git add` didn't sweep
   the foreign hunks (the failure mode that produced `12c94be` + `57d913d`). Zero sweeps so far.

**Shipped this session** (see each checkbox for full evidence): A1 `resolved_date`/`requested_date` on
`get_honest_coverage` (deployment-api@4e996f8); A3 new-listings false-positive guard (deployment-api@a9b6207 +
deployment-ui@179c7ce).

**Method note worth keeping**: A3's todo said "quantify the rate (real-GCS query, not a guess)" — doing that FIRST
changed the outcome. The todo's premise ("legacy rows … inflate 'new'") implied a broad legacy problem; the measurement
showed the corpus-wide rate (0.87%) is nearly irrelevant to the actual card, which shows a 30-day window where the rate
is **0.02% and 100% attributable to one venue onboarded 7 days ago**. That reframed the fix from "exclude legacy rows"
(which would have hidden real listings for no measurable benefit) to "surface a fact about the one real cluster". The
guard was then re-verified by driving the _shipped service_ against real GCS, not just its fixtures.

### 2026-07-17 — Playwright re-verification found + fixed a month-old mock-api.ts bug shadowing every /api/data-status/* endpoint

Doing a fresh Playwright pass (mock mode, `VITE_MOCK_API=true`, port 5199) against everything shipped this plan found a
crash in `CatalogueExplorer` (`TypeError: Cannot read properties of undefined (reading 'length')`) on first render, and
found the Prediction Catalogue silently showing "No prediction markets match the current filters" despite the mock
having representative rows for every category. Root cause (traced via `page.evaluate` calling `fetch(...)` directly in
the live page, NOT assumption): `src/lib/mock-api.ts` has had a catch-all
`if (path.match(/^\/api\/data-status/)) { return json(MOCK_DATA_STATUS); }` sitting near the top of the ~2,700-line
`handleRoute` function since `deployment-ui@687d4ce` (2026-06-16) — **every** more-specific
`/api/data-status/<endpoint>` handler added to this file AFTER that date and BEFORE this catch-all's position in file
order (honest-coverage, turbo/manifest, venue-filters, list-files, instruments-for-shard, download-catalogue-csv,
catalogue, instruments, instrument-availability, prediction-catalogue — essentially every data-status mock endpoint
shipped over the past month, including this session's own P2/P3/P6 UI work) was silently shadowed, always receiving the
generic turbo coverage-summary payload instead of its own real response shape. This is exactly why so many earlier
verification passes this session (Phase A, the P3/P6 real-data checks) kept coming back INCONCLUSIVE/empty against mock
mode — the mock layer itself was broken the whole time, independent of whether the actual shipped code was correct.

**Fixed**: moved the catch-all to be the true last-resort fallback (immediately before the function's existing
`404 "Mock: no handler"` response), so every specific handler gets first crack at matching. Also added defensive
`?? []`/`?? 0` fallbacks in `CatalogueExplorer.tsx` for `data.instruments`/`data.total_count` so a future malformed
response degrades gracefully instead of crashing. Verified end-to-end via Playwright:
`fetch('/api/data-status/ catalogue?...')` now returns the correct
`{instruments: [...4 rows], total_count: 4, label: "captured instruments (availability-derived)"}` shape (previously
returned the turbo coverage payload with no `instruments` key at all); `/api/data-status/prediction-catalogue` now
returns 8 rows across all 7 categories. Full-page screenshot confirms both panels render real mock data with correct
capture_status/MVP badges. Full Vitest suite re-run clean (93 files, 990 tests, 0 regressions) — the routing reorder
didn't change behavior for any OTHER endpoint, confirming nothing else in the codebase was relying on the old (buggy)
shadowing behavior. — `deployment-ui@0c817d2`.

**Why this wasn't caught by any of this plan's own Vitest specs**: every affected component's own test file mocks
`fetchInstrumentCatalogue`/`fetchPredictionCatalogue` etc. directly (jest/vitest `vi.mock`), never actually routing
through the real `mock-api.ts` `handleRoute` dispatcher — so unit tests stayed green throughout the entire month this
bug existed. Only a REAL browser hitting the REAL mock server (i.e. what `pw:L2` is supposed to be, not just "Vitest
passed") would ever have caught it. Worth flagging as a broader lesson for this workspace's `[UI] + pw:L2` gate: a
Vitest pass proves the component logic is correct GIVEN its mocked inputs, not that the actual mock-server wiring
delivers those inputs in the browser.

### 2026-07-17 — Honest-coverage cron verification uncovered + fixed a FRESH production regression (unrelated to P1's original fix)

Checking this plan's own P1 acceptance criterion ("tomorrow's 00:30 UTC file has `asset_groups_measured` = all 5 AND
`partial: false`") found the 2026-07-17 00:30 UTC cron had produced **nothing at all** —
`gs://central-element-323112-honest-coverage/2026-07-17/` didn't exist, and the Cloud Run launcher execution showed
`STATUS=False` (vs. `STATUS=True` the two nights prior). Root-caused via Cloud Logging:
`/tmp/launcher.sh: line 50: /tmp/lib/launcher_common.sh: No such file or directory`. Full root-cause + fix +
blast-radius check: `plans/active/issues/honest_coverage_launcher_missing_lib_dependency_2026_07_17.md`. Short version:
the `honest-coverage-daily-launcher` Cloud Run Job's container command does a single-file `gsutil cp` of the launcher
script and runs it — but that script had gained a `source lib/launcher_common.sh` dependency from an unrelated
fleet-wide rollout (`deployment-service@b5bd336`), and neither the `vm/lib/` directory (never published to GCS) nor the
Cloud Run job's fetch command (never updated) accounted for it. This regression only manifested tonight because this
plan's OWN 2026-07-16 P1 fix (`4f10b9b`) did a targeted single-file re-upload of the launcher script (the full tarball
republish being blocked by an unrelated dirty file) — the 07-16 cron fire happened before that upload, so it ran the old
script; tonight was the first real run of the newly-uploaded one.

**Fixed and verified end-to-end**: uploaded the two missing `vm/lib/*.sh` files to GCS; updated the Cloud Run job's
fetch command to also pull `vm/lib/` — both imperatively (`gcloud run jobs update`, so this test would immediately pass)
and in the Terraform source `terraform/gcp/honest_coverage_scheduler.tf` (the file's own header declares Terraform the
IaC SSOT for this resource, so an imperative-only fix would silently revert on the next `terraform apply`) —
`deployment-service@6c7a079e1`. Manually re-triggered the launcher (first retry, GCS-upload-only, still failed
identically — confirming the Cloud Run job command itself was the real gap, not just a missing file; second retry, after
the command fix, succeeded in 41s). Confirmed `coverage.json` for 2026-07-17 now shows `asset_groups_measured` = all 5,
`partial: false`. This plan's original P1 acceptance criterion is now genuinely met.

Checked blast radius on 2 other similar-sounding nightly Cloud Run jobs (`expected-universe-v2-defi`,
`lifecycle-catalogue-regen-defi`) — both use baked container images, not the fetch-a-script pattern, so unaffected. Not
an exhaustive fleet audit; flagged as a follow-up in the issue doc.

### 2026-07-16/17 — P9 round-2 execution complete (TradFi/CeFi/DeFi migrations + UI relabel + perf), fixtures browser in flight

Wraps up the "P9 round-2" thread referenced below. TradFi (Q2), CeFi (Q2), DeFi (Q2) migrations all applied + verified
on real infra (see their individual checkbox evidence above); sports Q3 root-caused as not-a-bug; Q4 unique-instruments
relabel shipped. Symbol-search 44s perf item also closed (deployment-api@8e1221b, root-caused to sequential per-venue
GCS reads, parallelized with ThreadPoolExecutor). Fixtures browser (operator request, item 6) still in flight via
sub-agent at session-end.

**Two side-discovered bugs found + fixed while validating locally against real GCS** (not pre-existing plan todos,
captured here per the discovery-capture rule):

1. `unified_api_contracts.canonical.domain.predictions.classifiers` logged `OTHER_BUCKET_MEMBER_ADDED` at INFO on every
   per-row prediction-market classification — ~1M log lines per catalogue cache-miss sweep, the actual cause of a ~2min
   local dev-server stall. Downgraded to DEBUG — unified-api-contracts@d4523602.
2. `deployment_api/services/data_status/coverage.py::_build_breakdowns` crashed the live coverage-summary endpoint with
   `TypeError: boolean value of NA is ambiguous` whenever a `groupby(...).sum(min_count=1)` group had zero non-NA
   `instrument_count` values (pandas `pd.NA`, not NaN — its `__bool__` deliberately raises). A bare `if v and v > 0`
   choked; fixed to `if pd.notna(v) and v > 0`. This was actively 500-ing the exact endpoint used to verify tonight's
   TradFi/CeFi/DeFi migrations — found because validation kept failing until this shipped. Added a regression test
   (`test_all_na_instrument_count_group_does_not_crash`) — deployment-api@e754a60.

**Workspace-hygiene note**: this session ran with 4 dispatched sub-agents in the SAME shared checkouts (not isolated
worktrees) for extended periods (hours). Confirmed multiple times that "no active commits + no active processes" does
NOT mean stalled — sub-agents idle between their own background-watchdog notifications; direct `SendMessage` check-ins
were the effective unstick mechanism each time. Also hit: local dev servers (uvicorn/vite) launched via
`nohup ... & disown` still died unexpectedly more than once over a multi-hour session — relaunched as needed, no root
cause chased (out of scope for tonight).

### 2026-07-16 — Continuation session (Phase B: P3, P2 UI, P8 UI-P2, P3 UI, P6 backend+UI, P1 column-prune, P4-B) — `/autonomous` engaged

Second continuation session (distinct from the "P9 round-2" thread above, which is a DIFFERENT concurrent Claude session
— see collision note below). Worked through the plan's remaining Phase B todos via dispatched sub-agents, each
commit-push-flip in its own turn:

| Point                     | What shipped                                                                                                                                                                                                 | Commit(s)                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| P3 backend + UAC facade   | `read_prediction_catalogue` (cqg derived on-the-fly, NOT a stored column — see below) + `category_for_group`                                                                                                 | deployment-api@9238983, unified-api-contracts@72fd959d1          |
| P2 UI                     | New-listings + upcoming-expiries lifecycle cards                                                                                                                                                             | deployment-ui@c6b1c09                                            |
| P8 UI-P2                  | FIXTURES-only deep-drill note                                                                                                                                                                                | deployment-ui@b0525e5 (+ 12c94be, see incident)                  |
| P3 UI                     | Prediction Catalogue browser (category → cqg → search)                                                                                                                                                       | deployment-ui@3bdb4e4                                            |
| P6 backend phase-1        | `mvp_only`+`is_mvp` tag on instrument list/CSV + new `/catalogue`+`/download-catalogue-csv`                                                                                                                  | deployment-api@abcce0b, @1e3c7b4                                 |
| P6 UI phase-1             | MVP-only toggle + badge on `InstrumentsModalStandard`; Catalogue Explorer panel; + a separately-surfaced InstrumentsModal reachability fix (see checkbox evidence)                                           | deployment-ui@90eba8c, @9648f42, @57d913d (fwd-fix), @8958345    |
| P1 DATA P2 (column-prune) | Metadata-deferred dictionary-encoded read (not row-group streaming) — 28.5% peak-RSS cut, 2 real correctness footguns found+fixed (categorical `.map()` sort order, `groupby(observed=False)` phantom cells) | instruments-service@6c9f604f                                     |
| P4-B                      | Live SPOT_ASSET emission at discovery time shipped; defi/cefi `catalog.parquet` full-mode regen running on real infra (2370/2666 day-partitions); backfill script drafted, not yet run                       | instruments-service@ce56d499 (regen + backfill script in flight) |

**Key finding (P3 backend, correcting the plan's literal wording)**: `canonical_question_group` is NOT a stored
per-market column on `prod/catalog.parquet` (verified against `build_instrument_catalogue.py`'s `CATALOG_COLUMNS` — only
a shard-tracking bundle row carries it). The service derives cqg per row via the SAME deterministic classifiers IS
adapters use at capture time, cached per unique venue+raw_symbol.

**Incident (documented separately, see `issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`
2026-07-16 update)**: a P8 UI-P2 ship briefly swept another concurrent agent's uncommitted `FixturesBrowser` WIP into a
commit via `quickmerge --files`'s whole-file staging — caught immediately, reverted (`deployment-ui@12c94be`), zero data
loss. Subsequent UI ships (P3 UI, P6 UI) used a patch-isolation/stash-protect procedure to avoid recurrence — held up
cleanly since.

**Operating-context deviation from `AUTONOMOUS_AGENT_RULES.md` rule 4 ("assume no one else is working")**: confirmed,
via `Co-Authored-By: Claude Opus 4.8` trailers on commits this session didn't make, that a SECOND independent Claude
session is actively working this exact plan concurrently in this slot (see the "P9 round-2" Progress Log entry below —
its own thread) — it shipped its own P2 UI work, the P9 operator-round-2 findings, a symbol-search fix, a rollup-cache
staleness fix, and is mid-way through a `FixturesBrowser` feature (backend+UI) as of this writing. Rather than assume
single-ownership, this session has been checking `git status`/mtimes before every shared-file edit and using the
stash/patch-isolation procedure above. Both sessions' work is being reconciled onto the same plan file via careful
`git pull --ff-only` immediately before every edit — no content has been lost so far.

**Model-tier note**: `/autonomous` invoked 2026-07-16 — self-check flagged Sonnet-on-opus-required (this is a cross-repo
main-orchestrator dispatch per `CLAUDE.md`'s model-tier rule). Operator explicitly confirmed continuing on Sonnet 5
(already set via `/model sonnet` earlier this session) rather than switching — documented per rule 1/2
(decide-and-document on an operator-answerable-but-already-answered question, not a silent violation).

**Still open** (see current `- [ ]` checkboxes throughout): P4-B backfill script needs to actually RUN once the
defi/cefi regens finish (script existing ≠ script run, per the plan's evidence discipline) + CeFi-spot leg mapping + the
P4-B UI surface; P1 INFRA tarball republish (BLOCKED — confirmed live foreign WIP in
`deployment-service/terraform.tfvars`, re-checked multiple times this session, still dirty); P1's "verify tomorrow's
00:30 UTC cron" (cannot be checked before 2026-07-17 00:30 UTC — genuinely time-gated, not deferred); several P2/P9 DATA
follow-ups explicitly marked lower-priority in their own sections. P6 UI phase-1 (toggle + badge + Catalogue Explorer +
the InstrumentsModal reachability fix) completed in a later continuation of this same session — see its checkbox
evidence for the foreign-hunk incident/fix + the reachability finding/fix; `pw:L2` deferred both times on
`.playwright-mcp` contention (code+mock+Vitest evidence stands in per this session's established carve-out).

### 2026-07-16 — P9 round-2 execution (sports root-cause, TradFi/DeFi migrations, UI relabel) + a side-discovered perf fix

Executed per operator instruction on the P9 round-2 todos (Q2 TradFi/DeFi/CeFi migrations, Q3 sports root-cause, Q4
label). Sports Q3: root-caused as NOT a bug (see the P9 Q3 checkbox above + its issue doc). TradFi + DeFi `data_type`/
`instrument_type` migrations: shipped + applied on real infra, verified live via direct API calls against the local
full-stack dev server (curl against `/api/data-status/coverage-summary` post-migration shows TradFi `instrument_type` 0%
`__legacy__` and DeFi `data_type` 100% `instruments`, no `instrument-catalog` residual). CeFi migration was still
in-flight (sub-agent) at last check — the same live endpoint still shows the pre-migration `perpetual`/`spot` lowercase
counts, confirming the check is genuinely live, not cached. UI Q4 relabel shipped + verified (totals match: 2,970,317
all-time / 123,563 latest-day).

**Side-discovery while validating locally**: the local dev server took ~2 minutes to become responsive on first request
(health checks timing out) — root-caused to `unified_api_contracts.canonical.domain.predictions.classifiers` logging
`OTHER_BUCKET_MEMBER_ADDED` at **INFO** level on every per-row prediction-market classification fallback — a hot path
called for the FULL prediction catalogue on every cache-miss sweep (~1M log lines observed in one sweep), not just
genuinely-new markets. Downgraded to DEBUG (2 call sites + their docstrings + the 2 tests pinning
`caplog.at_level(logging.INFO, ...)`) — unified-api-contracts@d4523602. Unrelated to the P9 Q7 symbol-search-44s perf
item (different code path — `deployment-api`'s `data_query_service.py` corpus loader vs this UAC classifier), tracked
here since it wasn't a pre-existing todo.

### 2026-07-16 — Session batch (P7, P5, P4-A, P1-remaining, P4-B enabler, P8, P2 backend)

Shipped this session (each commit-push-flip, QG-green + evidence-cited):

| Point        | What shipped                                                                     | Commit(s)                    |
| ------------ | -------------------------------------------------------------------------------- | ---------------------------- |
| P7 backend   | cefi chains sub-dimension gated on `defi` only                                   | deployment-api@47a7f67       |
| P7 UI-P2     | "instruments breakdown" button — resolved by P5 (grid link is the single one)    | deployment-ui@953fa81        |
| P5 UI        | redundant IS cefi/tradfi/defi drilldown suppressed (axis-comparison)             | deployment-ui@953fa81        |
| P4-A UI      | axis-aware value labels + canonical instrument_type aliases (raw on hover)       | deployment-ui@7853409        |
| P1 INFRA     | nightly cron launcher 16GB→32GB (real launcher + GCS upload) + issue doc         | deployment-service@4f10b9b   |
| P4-B enabler | 4 on-chain contract-address columns added to CATALOG_COLUMNS + projection        | instruments-service@77f0fdaa |
| P8 backend   | TEAMS `global_trigger_date`→`per_league_trigger_date` + codex matrix + tests     | deployment-api@fb0eec8       |
| P8 UI        | global-reference honest-absence affordance (LEAGUES/VENUES)                      | deployment-ui@43818c9        |
| P2 backend   | `catalogue_lifecycle` service + `/instruments/new-listings`+`/upcoming-expiries` | deployment-api@25865c0       |

**Big finding (issue doc):** the nightly honest-coverage cron ran on 16GB for weeks (launcher SSOT drift + a false
"column-prune shipped" commit) → 1-AG partial `coverage.json`. Fixed the real cron launcher + logged the drift in
`plans/active/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md`.

**Traced-unsafe correction:** P1 DATA P2 "drop `instrument_id`" corrupts the coverage denominator (breaks the prd+oracle
merge) — re-scoped in-place with the correct fix (streaming/metadata-deferred read).

## Deferred / remaining work (refreshed 2026-07-17 — 1:1 with the 13 open `- [ ]` todos above; every P1/P9-operator item is DONE)

> All P0/P1 correctness work + every P9 operator-round-2 item (symbol search, TradFi/CeFi/DeFi canonicalisation
> migrations, sports-source root-cause, unique-instruments relabel, fixtures browser, and the P6-catalogue-empty bug
> @62cc10f) is **shipped + flipped**. What remains is 13 lower-priority (P2/P3) follow-ups — none block the page. Rows
> below map 1:1 onto the open checkboxes above so nothing is lost.
>
> **Row-10 correction (2026-07-17) — there is NO outstanding sports TEAMS work.** Row 10 previously read "Sports TEAMS
> data-correctness | P8 (B) | scoped, not attempted this session — data-correctness items 1-5 in the P8 (B) block". That
> row was a **mislabel, and the work behind it does not exist**: (a) the P8 section contains five todos and **all five
> are `- [x]`** — there is no "P8 (B) block" and no "items 1-5" in it (P8's TEAMS→per-league reclassification shipped at
> deployment-api@fb0eec8); (b) walking the 13 rows against the 13 real open checkboxes, row 10 lands on the **P4-B UI**
> todo, whose own text reads "_(B)_ … (data-correctness items 1-5 above, the actual substance of **P4-B**, took priority
> and are done+verified)". So the original author read that todo's `_(B)_` as **P8(B)** instead of **P4(B)**, and read
> P4-B's already-completed SPOT_ASSET items 1-5 as sports items. Row 10 now names the todo it actually maps to, keeping
> the table honestly 1:1. Verified by grep before relabelling, not assumed.

| #   | Remaining item (open `- [ ]` todo)                            | Point         | Pri | Why deferred / next step                                                                                   |
| --- | ------------------------------------------------------------- | ------------- | --- | ---------------------------------------------------------------------------------------------------------- |
| 1   | Enrich `mock-api.ts` IS data-status fixtures                  | P5/P7 mock    | P3  | lets local mock-mode render cefi/tradfi/defi cards; LIVE deploy already exercises P4-A/P5/P7.              |
| 2   | ~~Canonicalise cefi manifest split rows~~                     | P7 follow-up  | P2  | ✅ **DONE 2026-07-17** — were PHANTOM pointers (0 objects at split venue); 80,615→79,943 @e6c31507.        |
| 3   | ~~Republish instruments-service tarball~~                     | P1 follow-up  | P2  | ✅ **DONE 2026-07-17** — fleet republished clean @11:00Z; live coverage.json carries `partial`.            |
| 4   | ~~`resolved_date`/`requested_date` on `get_honest_coverage`~~ | P1 stretch    | P3  | ✅ **DONE 2026-07-17** — deployment-api@4e996f8 (additive fields + 4 new specs).                           |
| 5   | Distinct `expiry` column in `CATALOG_COLUMNS`                 | P2 clean-LT   | P2  | long-term catalogue schema (expiry currently inferred).                                                    |
| 6   | ~~New-listings false-positive guard~~                         | P2            | P2  | ✅ **DONE 2026-07-17** — measured 99/439,940 (0.02%, all COINBASE-CDE); provenance flag @a9b6207+@179c7ce. |
| 7   | Real `question`/`title` column (polymarket/kalshi adapters)   | P3 follow-up  | P3  | upgrade prediction label from slug → human-readable title.                                                 |
| 8   | Root-cause remaining DeFi legacy `instrument_type`            | P4-A (A)      | P2  | grep IS writer for where legacy values still emit (display alias already in place).                        |
| 9   | ~~Drain residual `LENDING`~~                                  | P4-A (A)      | P2  | ✅ **DONE 2026-07-17** — 893 stale originals DELETED (re-splitting would've made 1,766 dupes) @e4fdd56c.   |
| 10  | ~~Surface `base_asset_contract_address` in the drilldown~~    | **P4 (B)**    | P2  | ✅ **DONE 2026-07-17** — backend @13a8f0b + copyable UI @a860937 (473/473 real-GCS non-null).              |
| 11  | True-catalogue source                                         | P6 phase-2    | P3  | deployment-api→IS read path OR projection; availability-derived phase-1 shipped @1e3c7b4.                  |
| 12  | ~~`/prediction-catalogue` latency~~                           | P3 perf       | P3  | ✅ **DONE 2026-07-17** — real cost ~173s not 39s; paging was re-paying it, now 0.00s @0e39a53.             |
| 13  | ~~`/catalogue` unpaginated large-AG cost~~                    | P6 perf (NEW) | P3  | ✅ **DONE 2026-07-17** — tradfi 61.3s→14.9s (4.1x), cefi 6.5x, page byte-identical @0e39a53.               |

### 2026-07-16 — Phase A browser-validation of P5/P7/P4-A/P8 (INCONCLUSIVE — mock-fixture gaps, not code bugs)

Continuation session drove `deployment-ui` locally in mock mode (`VITE_MOCK_API=true`, dedicated port 5199) with the
Playwright MCP to visually confirm the already-unit-tested P5/P7/P4-A/P8 changes. Result: **static code review + the
cited unit tests all confirm correct behavior, but the local mock fixtures can't fully exercise 3 of the 4 checks** —
this is a pre-existing gap in `deployment-ui/src/lib/mock-api.ts`, not a defect in the shipped commits:

- **P5/P7 (Instrument Coverage Summary drilldown suppression + chain-axis gate):** `/api/data-status/coverage-summary`'s
  mock handler (`mock-api.ts:3758-3795`) is hardcoded to return a single `PREDICTION` entry regardless of the requested
  service, and `/api/config/shard-axis-matrix` (`mock-api.ts:3334-3349`) declares `shard_axes` only for
  `market-tick-data-service.prediction` — no `instruments-service` key at all. So cefi/tradfi/defi never render as cards
  in that panel in mock mode, and `isHierarchicalDrilldownRedundant` can't be exercised either way. What DID verify: the
  separate TURBO "Data Coverage" grid (a different, richer mock) correctly shows CeFi venues only
  (BINANCE-SPOT/BINANCE-FUTURES/DERIBIT, no SOLANA/ZKSYNC rows), and PREDICTION correctly retains its drilldown.
- **P4-A (canonical instrument_type labels):** `BreakdownsAccordion` only mounts when `breakdown_axes` is non-empty for
  the asset group; since the mock shard-axis-matrix has no `instruments-service` entry at all, the accordion never
  renders on this page in mock mode — INCONCLUSIVE. Static review of `data-status-helpers.ts:106-134` +
  `BreakdownsAccordion.tsx:96-104` reads correct (alias map, hover tooltip, `(unlabeled)` vs `(legacy — pre-job_id)`
  scoping) and matches the cited passing Vitest specs.
- **P8 (TEAMS per-league drilldown + global-reference affordance):** `_mkSportsByDataType()` (`mock-api.ts:340-450`)
  only defines FIXTURES/LEAGUES/FIXTURE_EVENTS — no TEAMS/STANDINGS/VENUES fixtures exist, so the TEAMS-reclassification
  claim is INCONCLUSIVE (nothing to compare). What DID verify (PASS): LEAGUES renders the "Global reference entity — no
  per-league breakdown (axis: global_periodic)" affordance, and FIXTURES shows a real per-league drilldown.

Screenshots: `01-instrument-coverage-summary.png`, `02-sports-breakdown-leagues-affordance.png`,
`03-cefi-breakdown-venues-only.png` (session scratchpad, not repo-committed). Zero console errors.

**Why not fixed now:** enriching `mock-api.ts` with instruments-service shard-axis-matrix entries + cefi/tradfi/defi
coverage-summary rows + TEAMS/STANDINGS/VENUES sports fixtures is itself a non-trivial, correctness-sensitive addition
(wrong mock shapes would give false confidence) and out of this plan's scope. The stronger, lower-risk verification path
is the LIVE Cloud Run deployment once `deployment-ui`'s LDR→main promote (currently gated on a fresh SIT-validation
cycle for the tree that includes today's P5/P7/P4-A/P1/P4-B/P8/P2-backend commits — `full-workspace-sit` ran green
09:50-09:57 UTC, `ldr-to-main-promote-fleet` ticks hourly-ish) catches up and redeploys — real production data has
cefi/defi/tradfi variety and TEAMS data, so it would resolve all three INCONCLUSIVE checks in one pass.

- [ ] [DATA] P3. _(new, low-priority)_ Enrich `deployment-ui/src/lib/mock-api.ts` so `instruments-service` data-status
      mock fixtures cover: (a) `shard_axes` entries for cefi/tradfi/defi/sports in `/api/config/shard-axis-matrix`, (b)
      per-asset-group entries (not just PREDICTION) in `/api/data-status/coverage-summary` with a mix of canonical +
      legacy-lowercase `instrument_type` values (to exercise `BreakdownsAccordion`), (c) TEAMS/STANDINGS/VENUES sports
      `data_type` fixtures. Unlocks fully self-contained Playwright verification of this page without needing a live
      deployment. Not required for this plan's P5/P7/P4-A/P8 acceptance (already unit-tested) — tracked as a follow-up.

### 2026-07-16 — P7 CeFi chain-axis gate (backend P1) shipped

- **Root cause (trace-first, live-verified against the cefi availability index):** the cefi manifest
  (`gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet`) holds BOTH the canonical
  combined form (`venue=PACIFICA-SOLANA`, empty chain) AND residual split rows (`venue=PACIFICA, chain=SOLANA` /
  `venue=LIGHTER, chain=ZKSYNC`) — 4617 chain-nonempty rows, whose ONLY distinct chains are `SOLANA` + `ZKSYNC`. The
  Instrument-Coverage-Summary's `extras["chains"]` sub-dimension (`_build_v4_sub_dimensions`) built a chains breakdown
  from ANY populated `chain` column, so cefi manufactured `SOLANA`/`ZKSYNC` chain sub-rows. `_build_breakdowns` was
  already clean (UAC `BREAKDOWN_AXES[(is,cefi)] = (instrument_type, data_type)`, no chain).
- **Fix:** gated the `extras["chains"]` sub-dimension on `cat == 'defi'` (read-side display gate; manifest query key
  unchanged). UI grid renders `extras["chains"]` verbatim → no UI change needed. `deployment-api@47a7f67`.
- **DEFERRED finding (manifest-level drift, out of P7 read-side scope):** the split rows `venue=PACIFICA chain=SOLANA` /
  `venue=LIGHTER chain=ZKSYNC` are a WRITER-side shard-atom drift — cefi keys on `venue` alone, so a chain should never
  be stamped. These split rows ALSO duplicate the venue axis (`PACIFICA` vs `PACIFICA-SOLANA` render as two venues).
  This is a data-correctness finding requiring a manifest canonicalization migration (collapse
  `venue=PACIFICA,chain=SOLANA` → `venue=PACIFICA-SOLANA,chain=""`), tracked as P7-followup below — NOT fixed by the
  read-side gate.

- [x] [DATA] P2. ✅ _(P7 follow-up — manifest drift)_ Canonicalized the cefi split rows —
      `scripts/canonicalize_cefi_split_venue_chain_2026_07_17.py`, **applied + independently verified on real prod
      infra**. **This turned out to be more than a cosmetic venue-axis fix: the split rows were PHANTOM POINTERS.**
      Traced the real by_date layout (`…/day=<D>/pipeline_mode=<M>/asset_group=cefi/venue=<V>/instruments.parquet`) and
      checked GCS directly: the objects live under the GLUED venue (`venue=LIGHTER-ZKSYNC`), while `venue=LIGHTER` /
      `venue=PACIFICA` hold **zero objects**. The script's own pre-write guard proved this at full scale —
      **1,078/1,078** captured split rows have a real object at the CANONICAL venue (a 60-row sample found **0/60** at
      the split venue). So each split row claimed a capture at a path that does not exist, and 493 of them were
      `captured` rows whose canonical twin was **absent entirely** — i.e. the migration REPAIRS the manifest↔object
      correspondence rather than just merging two venue labels. **Writer root-cause — already fixed upstream for BOTH
      venues (verified by reading code + the live registry, so this cannot recur; no writer change was needed):** (a)
      `writers._canonical_manifest_venue_chain` short-circuits
      `if VENUE_TO_ASSET_GROUP.get(venue_str) == "cefi": return venue_str, ""` — live registry resolves `LIGHTER-ZKSYNC`
      → `'cefi'`, so the DeFi `PROTOCOL-CHAIN` split no longer fires; (b) `PACIFICA-SOLANA` → `None` (removed from the
      registry entirely, operator 2026-07-16 Solana-perp-DEX ruling), so nothing enumerates it and that writer path is
      dead. The 4,617 rows were pure history. **Safety design**: explicit `_SPLIT_PAIRS` allowlist (not a generic "any
      cefi row with a chain" rule, which could silently rewrite an unexpected row); dedup on the manifest's REAL
      composite identity (`manifest_writer._ROW_KEY_COLUMNS` — `chain` is itself a key member, which is _why_ collapsing
      collides), winner = **capture_status FIRST, recency second** (a newer `empty_confirmed` must never evict older
      `captured` evidence — the footgun the defi data_type migration's dry-run caught); aborts rather than promoting a
      capture claim onto a path with no object. — instruments-service@e6c31507 + **Evidence (real infra, independently
      re-read — not the script's own log)**: `80,615 → 79,943` rows (−672 = exactly the modelled collisions); residual
      split rows / `LIGHTER` / `PACIFICA` / chain-nonempty all **0** (was 4,617 / 2,413 / 2,204 / 4,617);
      `LIGHTER-ZKSYNC` 1,424→**3,643**, `PACIFICA-SOLANA` 1,426→**3,152** (venue axis no longer double-counts).
      **Out-of-scope guard: all 27 other cefi venues byte-identical.** `capture_status` deltas match the model exactly
      (captured −585, empty_confirmed −87, expected_unattempted/attempted_failed **unchanged**), and every collision was
      status-identical (captured→captured 585, empty→empty 87) so no evidence was traded away. **Decisive no-loss
      proof:** LIGHTER-ZKSYNC captured rows `910 → 716` while **distinct captured dates `716 → 716`**; PACIFICA-SOLANA
      `802 → 411` rows with **distinct dates `411 → 411`** — the dedup removed only same-key duplicates; every distinct
      captured date survived. Rollback snapshot:
      `gs://instruments-store-cefi-prd-central-element-323112/_index/snapshots/pre_cefi_split_venue_chain_canon_2026_07_17_20260717-105532.bak.parquet`.
      Unit: `tests/unit/migrations/test_canonicalize_cefi_split_venue_chain.py` 9 passed (collapse; allowlist-only;
      collision dedup; **captured-beats-newer-empty**; gap-filling row kept; idempotent re-run; **None-vs-`""` chain
      normalisation** — without it the row-key compare silently misses and the duplicate venue survives).

### 2026-07-16 — P1 Honest Coverage FIXED (immediate + durable), verified live

- **Root cause (live-verified):** the Honest Coverage card is a verbatim mirror of
  `gs://central-element-323112-honest-coverage/{date}/coverage.json` (endpoint `get_honest_coverage` returns the bytes
  unchanged). The daily writer ran on an **8 GB `e2-standard-2`**; `measure_honest_coverage._read_parquet_safe` loads
  each asset-group's full availability-index parquet into pandas and **swallows exceptions → returns None**, so a
  MemoryError on the growing cefi/tradfi/sports parquets silently skips that AG. `main()` then wrote
  `asset_groups_measured = only-the-AGs-that-fit` with no error. Live proof: `asset_groups_measured` swung
  `['cefi','defi','tradfi','sports','prediction']` (07-09/07-11) → `['cefi']` (07-13) → `['defi']` (07-15/07-16).
- **Immediate fix (verified):** launched `honest-coverage-20260716-073157` on `e2-highmem-4` (32 GB) → today's
  `coverage.json` regenerated (`generated_at 2026-07-16T06:39:00Z`) with **all 5 asset groups**. VM auto-shut-down.
- Shipped:
  - `- [x]` **[INFRA] P0. ✅ Right-size the scheduled honest-coverage VM e2-standard-2 → e2-highmem-4 (32 GB)** —
    `deployment-service@9d97eb2` + Evidence: VM `honest-coverage-20260716-073157` re-measured all 5 AGs (`coverage.json`
    `asset_groups_measured=['cefi','defi','tradfi','sports','prediction']`, `generated_at 2026-07-16T06:39:00Z`).
  - `- [x]` **[DATA] P0. ✅ Writer stamps `partial`/`asset_groups_failed`/`asset_groups_requested` + logs ERROR on a
    partial run** (honest-absence — never serve a partial as complete) — `instruments-service@a29e483`.
  - `- [x]` **[UI] P0. ✅ Honest Coverage card renders an amber "coverage incomplete" banner (lists failed groups) and a
    stale banner + tinted date when the 14-day fallback serves an older file** — `deployment-ui@8ef7a95` + Evidence:
    `HonestCoverageCard.test.tsx` 8 specs green (tsc/eslint clean).

---

## P1 — Honest Coverage: remaining hardening

**Design guide.** The user-facing bug is already fixed and verified (Progress Log). What remains: (a) make the fix
_permanent for the nightly cron_, and (b) defence-in-depth so a future OOM can't recur.

- _Nightly path:_ today's fix was a manual VM run on the new `e2-highmem-4` launcher, but the **scheduled** cron
  (`honest-coverage-daily`, 00:30 UTC → `launch-honest-coverage-vm.sh` → a code tarball in
  `gs://deployment-scripts-central-element-323112/`) uses whatever tarball is published. The RAM bump + the writer
  partial-stamping only reach the nightly run once the tarballs are republished.
- _Memory driver:_ `measure_honest_coverage._read_parquet_safe`
  (`instruments-service/scripts/measure_honest_coverage.py` ~226) reads `_READ_COLUMNS` = all 6 incl. `instrument_id`
  (the high-cardinality column). Dropping `instrument_id` where the coverage math doesn't need it removes the OOM cliff
  entirely.
- _Endpoint:_ `get_honest_coverage` (`deployment-api/deployment_api/routes/data_status/_live_coverage.py:598-683`) walks
  back up to 14 days and returns the file verbatim; the card infers staleness from the payload `date`.
- **Acceptance:** tomorrow's 00:30 UTC file has `asset_groups_measured` = all 5 AND `partial: false`
  (`gcloud storage cat gs://central-element-323112-honest-coverage/<YYYY-MM-DD>/coverage.json`).

- [x] [INFRA] P1. ✅ Nightly cron now launches `e2-highmem-4` (32GB). **BIG FINDING (issue doc):** the plan's INFRA P0
      fix targeted the WRONG launcher — the live cron is `Cloud Scheduler honest-coverage-daily (00:30 UTC)` →
      `Cloud Run Job honest-coverage-daily-launcher` → fetches `gs://…/vm/launch-measure-honest-coverage-vm.sh` (NOT
      `launch-honest-coverage-vm.sh` which P0 `9d97eb2` fixed). That real launcher was downsized to `e2-standard-4`
      (16GB) on 2026-06-16 citing a column-prune that was never shipped → the nightly wrote 1-AG partial `coverage.json`
      for weeks (07-12 `[defi]`, 07-13 `[cefi]`, 07-15 `[defi]`; full-5 files were off-schedule manual runs). Reverted
      to the proven 32GB + uploaded to the cron's GCS path. — deployment-service@4f10b9b + Evidence:
      `gcloud storage cat gs://deployment-scripts-central-element-323112/vm/launch-measure-honest-coverage-vm.sh` shows
      `--machine-type=e2-highmem-4` (Update Time 2026-07-16T08:36Z); tonight's 00:30 UTC run will use 32GB. Issue doc:
      `plans/active/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md`. _(Tarball
      republish for partial-stamping is BLOCKED — see follow-up below; NOT required for a full 5-AG run at 32GB.)_
- [x] [INFRA] P2. ✅ _(P1 follow-up)_ Republish the instruments-service tarball so the nightly writer carries
      partial-stamping — **UNBLOCKED + VERIFIED DONE 2026-07-17; no `--allow-dirty-tarball` was ever used.** Re-checked
      the blocker as instructed rather than assuming it persisted: the whole CORE fleet was **republished from CLEAN
      trees at ~10:00–11:00Z today** (`git_status_clean: true` on every manifest) — UAC `@825878f` 10:30:53Z, UTL
      `@61bf7444` 10:04:17Z, deployment-service `@821250ab` 11:00:55Z, **instruments-service `@e6c31507` 11:00:55Z**.
      The dirty `terraform.tfvars` that blocked this yesterday was committed/clean during that window, so the republish
      simply succeeded. (deployment-service is dirty again NOW — 3 foreign files, one touched 9 min before this check —
      but that is NEW unrelated work and no longer gates this item. Confirmed the constraint was real, not imagined:
      `deployment-service` is in `CORE_REPOS`, which the script ALWAYS includes, and its dirty check is per-repo
      `git -C <repo> diff-index --quiet HEAD` — so there is no way to scope it out; waiting was the only correct path,
      exactly as the todo instructed.) **Evidence — proven by CONTENT and by the live artifact, not by ancestry alone:**
      (a) `git merge-base --is-ancestor a29e483c e6c31507` → **true**, the published tarball SHA descends from the
      partial-stamping fix; (b) reading the PUBLISHED SHA's own file,
      `git show e6c31507:scripts/measure_honest_coverage.py` contains `partial = bool(asset_groups_failed)` +
      `asset_groups_failed` + `"asset_groups_requested"` (lines ~819-840); (c) **the decisive end-to-end proof** — the
      LIVE nightly artifact `gs://central-element-323112-honest-coverage/2026-07-17/coverage.json` carries
      `partial: False`, `asset_groups_failed: []` and `asset_groups_requested` **present**, alongside
      `asset_groups_measured = ['cefi','defi','tradfi','sports','prediction']` (generated_at 2026-07-17T09:09:21Z).
      Those three fields can only exist if the writer that produced the file carries `a29e483` — which IS this plan's
      stated P1 acceptance ("tomorrow's 00:30 UTC file has `asset_groups_measured` = all 5 AND `partial: false`"), now
      met by the real cron output rather than a manual run. The launcher SSOT drift half was separately resolved earlier
      today (`deployment-service@6c7a079e1` — Cloud Run job fetch command + the Terraform IaC SSOT both updated; see the
      2026-07-17 launcher Progress Log entry +
      `plans/active/issues/honest_coverage_launcher_missing_lib_dependency_2026_07_17.md`), and today's successful 5-AG
      cron output is the proof it holds.
- [x] [DATA] P2. ✅ Column-prune the writer read so the read stops scaling toward OOM regardless of VM RAM. **Approach
      taken = metadata-deferred read (Option 2), NOT row-group streaming:** the availability-index parquet already
      stores every `_READ_COLUMNS` column PLAIN_DICTIONARY-encoded per row-group (verified via pyarrow row-group
      metadata on real prd buckets) — `pd.read_parquet(..., read_dictionary=<cols>)` (forwarded to
      `pyarrow.parquet.read_table`) preserves that on-disk encoding as pandas `category` dtype instead of pandas'
      default of expanding every row into a python-object string, at effectively zero correctness risk (same values,
      only the dtype changes). Applied to `_read_parquet_safe` (all 4 fallback tiers) + `_read_parquet_eu_only`.
      TRACED-UNSAFE concern from the original todo (naive `instrument_id` drop corrupting `_merge_manifests`'s shard-key
      dedup) does not apply — `instrument_id` is still read, just compactly. Two correctness footguns found + fixed
      empirically (not assumed) while implementing this: (a) `Series.map()` on a Categorical column returns a
      Categorical whose sort order is category-discovery-order, not numeric order, which would make `_merge_manifests`
      keep the WRONG "best status" per shard — fixed via `.astype("int64")` after the priority `.map()`; (b) pandas
      `groupby` defaults to `observed=False`, synthesising a phantom empty group for every unobserved category
      combination — fixed via `observed=True` on all 5 `_compute_coverage` groupby calls (no-op on legacy object-dtype
      buckets). — instruments-service@6c9f604f + Evidence: real production A/B comparison against the sports-prd bucket
      (1,958,498 raw rows — cefi/tradfi/defi/prediction were mid-write by a concurrent pipeline during this session,
      sports was the only stable target) — byte-identical `_compute_coverage` output (every projection incl. Layer-1
      missing/stray tuples) between the old object-dtype code path and the new category-dtype path; peak RSS 447.1MB →
      319.8MB (-28.5%); retained merged-DataFrame memory 27.19MB → 0.93MB (~29x); read wall-time 413s → 218s (~1.9x
      faster, bonus). 6 new unit tests added to `test_measure_honest_coverage.py` (real local-parquet dictionary
      round-trip across 2 fallback tiers + the eu_only reader, a regression test for each of the 2 footguns, and a
      categorical-vs-object-dtype equivalence test). Full `tests/unit/` suite green (4387 passed/3 skipped in one run
      this session). Enables downsizing the cron VM back to 16GB — **not done here**, a separate operator/infra
      decision; `deployment-service`'s launcher was not touched (noted in passing: that repo currently carries unrelated
      live foreign WIP in `terraform.tfvars`, left alone).
- [x] [BACKEND] P3. ✅ _(stretch, optional)_ Added `resolved_date`/`requested_date` to `get_honest_coverage` so the card
      can distinguish "today's file" from a 14-day fallback precisely. `requested_date` = the day the caller asked for
      (explicit `?date=`, else today UTC — i.e. `candidate_dates[0]`, true in both branches); `resolved_date` = the day
      whose file was actually read. Equal ⇒ today's file; `resolved_date < requested_date` ⇒ the walk-back served an
      older measurement. **Contract change (deliberate, documented in the docstring):** the endpoint previously returned
      the GCS bytes _verbatim_; it now parses + re-serialises to inject the two fields. Kept honest: the writer's own
      `date` is NOT overwritten, every pre-existing key passes through untouched (test-pinned), and a payload that is
      not a JSON object has nothing to hang provenance on so it is still served verbatim rather than reshaped. UI not
      wired — the todo's scope is the field ("so the card CAN distinguish"); the card's existing `date`-inference still
      works unchanged. — deployment-api@4e996f8 + Evidence: `test_honest_coverage_route.py` 11 passed
      (`-p no:randomly`), including new `TestFallbackProvenanceFields` ×4 — direct-hit ⇒ requested==resolved; walk-back
      ⇒ requested=today / resolved=today-2 (asserts the real fallback pair); additive-and-preserves-payload (every
      `SAMPLE_COVERAGE` key byte-equal, added keys == exactly the 2); non-object payload served verbatim. ruff clean +
      `ruff format` clean on both files; basedpyright: **zero new errors** — the file's 7 `reportAny` errors are
      pre-existing and identical at HEAD (verified by A/B-ing the HEAD copy through basedpyright: same 7, shifted 19
      lines by this diff), and the `cast("object", …)` + isinstance-narrow avoids the `Any` ban rather than suppressing
      it. _(Ship notes: full `quality-gates.sh --no-fix` is RED in this tree on a **concurrent agent's live WIP** —
      `fixtures_browse.py` E501 + `fixtures_browser.py` RUF100, mtimes ~2min old at ship time, zero overlap with this
      diff; my 2 files verified clean in isolation — same collision carve-out precedent as this plan's
      `12c94be`/`e27ba4b` entries. Shipped `--skip-preflight` (the flag quickmerge documents "for multi-agent use")
      because the dirty dep is deployment-service's foreign-live `terraform.tfvars` — a features-service-sports Cloud
      Run tfvars with zero relationship to this endpoint; same dirty-deps carve-out as `@62cc10f`. Post-ship verified
      `git show --name-only` landed exactly 2 files and the foreign WIP is still intact + uncommitted.)_

## P2 — New Listings + Upcoming Expiries (catalogue-derived, user thresholds)

**Design guide.** Today the IS data-status page has exactly one forward-looking panel, **"Upcoming fixtures"**, which is
the exact pattern to clone (it already has a threshold input).

- _Existing pattern (mirror this end-to-end):_ route `deployment-api/deployment_api/routes/fixtures.py:15-24`
  (`GET /fixtures/upcoming?days=<1..31>&league_id=` — `days` is already a `Query(7, ge=1, le=31)`); service
  `deployment-api/deployment_api/services/upcoming_fixtures.py` (per-day window read, 5-min TTL cache, shard-isolated,
  TypedDict return); UI `deployment-ui/src/components/UpcomingFixtures.tsx:74-152` (Card + clamped numeric input +
  refetch-on-change); client `deployment-ui/src/api/client.ts:944-959`; mount point `DataStatusTab.tsx:1741` under the
  `serviceName === "instruments-service"` guard.
- _Data source:_ per-AG lifecycle catalogue `gs://instruments-store-{ag}-{env}-{pid}/{env}/catalog.parquet`
  (`instruments-service/scripts/build_instrument_catalogue.py`). Columns: `available_from` = listing date
  (MIN(first-observed, venue-declared)); `available_to` = a **4-way** value (delisted_at / expiry / None-if-active /
  last-observed — `build_instrument_catalogue.py:1034-1041`). Read the parquet DIRECTLY (deployment-api cannot call
  `list_instruments()` — no reader registered, T4). Bucket resolve via
  `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group=ag)` (prediction:
  `kind="instruments-store-prediction"`).
- _The load-bearing rule:_ **Upcoming Expiries MUST filter `instrument_type ∈ {FUTURE, OPTION, COMBO}` AND
  `available_to ∈ [today, today+within_days]`.** Because delistings + last-observed values are always ≤ today, the
  forward window admits only genuine future expiries — the type filter + forward window together make it correct even
  though `available_to` is overloaded.
- **Acceptance:** two endpoints honour mock mode; two cards with numeric threshold inputs render next to Upcoming
  fixtures; a pw:L2 spec drives a threshold change and asserts the list refetches.

- [x] [BACKEND] P1. ✅ New service `deployment_api/services/catalogue_lifecycle.py` (mirrors `upcoming_fixtures.py`:
      5-min TTL, shard-isolated per-AG `prod/catalog.parquet` reads, prediction = own bucket kind):
      `list_new_listings(max_age_days, asset_group?, venue?)` (`available_from ∈ [today - max_age_days, today]`,
      newest-first) + `list_upcoming_expiries(within_days, asset_group?, venue?)`
      (`instrument_type ∈     {FUTURE,OPTION,COMBO}` AND `available_to ∈ [today, today+within_days]`, soonest-first). A
      missing/failed AG parquet is skipped, never a cross-AG raise. — deployment-api@25865c0 + Evidence:
      `test_catalogue_lifecycle.py` 3 specs green (window filter, type+forward-window expiry filter, shard-isolation) +
      `quality-gates.sh --no-fix` green (exit 0; 1 unrelated pre-existing xdist-flaky `hung_provider` test, passes in
      isolation).
- [x] [BACKEND] P1. ✅ Routes `GET /api/instruments/new-listings?max_age_days=<1..365>&asset_group=&venue=` +
      `GET /api/instruments/upcoming-expiries?within_days=<1..365>&asset_group=&venue=`
      (`routes/catalogue_lifecycle.py`, mirrors `routes/fixtures.py`; honours `_cfg.is_mock_mode()`); registered beside
      the fixtures router in `main.py`. — deployment-api@25865c0. _(NOTE: new real service modules must be registered in
      `tests/unit/conftest.py`'s `_ensure_services_mocked` allowlist — the stub services package has `__path__=[]`, so a
      dotted import of an unregistered new module fails with "unknown location" under pytest. Added
      `catalogue_lifecycle` there.)_
- [x] [UI] P1. ✅ Two sibling cards `NewListingsCard`/`UpcomingExpiriesCard`
      (`deployment-ui/src/components/     LifecycleCards.tsx`, shared internal `useLifecycleRows`/`LifecycleCard`)
      mounted next to `<UpcomingFixtures/>` in `DataStatusTab.tsx` (IS-only guard); numeric threshold inputs ("new if
      listed within N days" default 30, "expiring within M days" default 7) + `fetchNewListings`/`fetchUpcomingExpiries`
      client helpers + `CatalogueLifecycleRow` interface in `client.ts` (mirrors `fetchUpcomingFixtures`). Added
      mock-api.ts handlers for both routes (representative cefi/defi/tradfi rows) since neither was mocked before. —
      deployment-ui@c6b1c09 + Evidence: `LifecycleCards.test.tsx` 6 specs green (renders rows, empty state,
      threshold-change refetch with new param value, refresh button) + full UI QG green (tsc/eslint/vitest 88
      tests/build). `[UI]` + pw:L2 (Vitest regression spec, per this plan's stated acceptance). _(Live Playwright MCP
      browser check deferred — the shared `.playwright-mcp` browser was actively held by another concurrent agent in
      this workspace at ship time; the mock-api handlers are committed and unit-verified, so the browser check is a
      nice-to-have follow-up, not a blocker.)_
- [ ] [DATA] P2. _(clean long-term)_ Add a distinct `expiry` column to `CATALOG_COLUMNS`
      (`build_instrument_catalogue.py`) so expiry is stored separately from the overloaded `available_to`; then regen.
- [x] [BACKEND] P2. ✅ New-listings false-positive guard — **quantified on real prod GCS first, then chose SHOW
      PROVENANCE over exclude.** Root cause confirmed by reading the writer (not assumed): `available_from` =
      `MIN(first_day_observed, declared_from)` (`build_instrument_catalogue.py:1086-1092`), and when a venue declares no
      listing date that MIN silently degrades to _the day the pipeline first saw the instrument_. **Measured** (all 5
      AGs, 4,310,720 catalogue rows, 2026-07-17): 37,308 rows (0.87%) corpus-wide carry the signature, but only **99 of
      the 439,940 rows inside the live 30-day new-listings window (0.02%)** — a SINGLE cluster, `COINBASE-CDE` @
      2026-07-10, all 99 with `market_created_at` empty (no venue-truth date existed) and expiries running to
      **2030-12-20**: a long-established venue cannot have listed a 2030 future 7 days ago, so these are
      pipeline-onboarding artifacts, not listings. **Control proves the signature discriminates**: onboarding floods
      score high (`BITGET-SPOT` 61% of rows on its first day, `LIGHTER-ZKSYNC` 100%) while established venues are
      negligible (`DERIBIT` 0.09% of 334,468), and a genuine new listing on an established venue is never tagged.
      **Decision — surface, don't exclude**: at 0.02%, dropping rows would hide possibly-real listings, and the
      catalogue stores only the MIN _result_ (not which side won), so a venue that genuinely launched on its first
      captured day is indistinguishable. The new field `available_from_is_venue_first_day` therefore states a **fact**
      ("this row's available_from is the earliest date we hold for this venue") and lets the reader judge —
      honest-absence per this plan's golden rules, not a fabricated verdict. Computed over the WHOLE per-AG catalogue
      **before** the date window narrows the frame (tagging after windowing would make every row trivially match the
      window's own min — regression-pinned). Also computed on the expiries path so the shared row type never reports a
      silent `false`. — deployment-api@a9b6207 + deployment-ui@179c7ce + Evidence: **real-GCS run of the SHIPPED
      service** (not just fixtures) — `list_new_listings(max_age_days=30, asset_group="cefi")` returns 10,563 rows,
      flags exactly **99**, all `COINBASE-CDE 2026-07-10` (samples:
      `COINBASE-CDE:FUTURE:BTC-USD@LIN-20301220 from=2026-07-10 to=2030-12-20`), 0 unflagged CDE rows, and DERIBIT's
      7,599 in-window rows stay unflagged. Unit: `test_catalogue_lifecycle.py` 8 passed incl. new
      `TestNewListingFalsePositiveGuard` ×5 (flood tagged / genuine-new-on-established NOT tagged /
      rows-surfaced-not-excluded / tag-computed-before-windowing / expiries-tag-truthful). UI: `LifecycleCards.test.tsx`
      8 passed incl. 2 new specs (amber "⚠ listing date unconfirmed" affordance with a full explanatory `title`, row
      still rendered; established venue unflagged) + full `quality-gates.sh` **green (24s: tsc/eslint/vitest/build)**.
      `[UI]` + pw:L2 via Vitest per this plan's accepted pattern; mock-api.ts carries a representative COINBASE-CDE
      flood row so mock mode renders the affordance. basedpyright: **zero new errors** (A/B'd vs HEAD — same 6
      pre-existing). _(deployment-api's full gate is red on a concurrent agent's live
      `fixtures_browser`/`fixtures_browse` WIP — zero overlap; my files verified clean in isolation. Same collision +
      `--skip-preflight` dirty-deps carve-out as A1 above.)_

## P3 — Prediction markets: category dropdown → human-readable catalogue browser

**Design guide.** Prediction is fully onboarded (venues `POLYMARKET`+`KALSHI`, `InstrumentType.PREDICTION_MARKET`); the
canonical grouping already exists. Build a browse-the-live-catalogue surface, decided to ship on the slug for v1.

- _Grouping (already canonical, already stored):_ `canonical_question_group` (cqg) is a manifest column + the prediction
  shard axis (`deployment-api/deployment_api/services/data_status_hierarchical.py:16,367-401`; projected in
  `manifest_source.py:84,92`). The coarse category = `PredictionMarketCategory`
  (`unified-api-contracts/.../canonical/domain/prediction/prediction_mapping.py:23`, values crypto/politics/sports/…) —
  **NOT facade-exported today.** `underlying_for_group(cqg)` + `_category_for_underlying(...)` already exist
  (`.../predictions/cross_venue_mapping.py:279-328`), so `category_for_group(cqg)` is a 2-line composition.
- _Live source:_ `prod/catalog.parquet` in `instruments-store-pred-{env}-{pid}` (deployment-api already reads it for the
  unique-count at `manifest_source.py:216-222`, projecting only `instrument_id` — just widen the `columns=`).
- _Label (v1, honest fallback):_ `raw_symbol` slug (e.g. `bitcoin-up-or-down-june-24-2026`) → `base_asset` (first 50
  chars of the raw question for OTHER) → Polymarket `event_title` → `instrument_id`. **Never fabricate a title.** Data
  caveat: `prod/catalog.parquet` may hold NaN `raw_symbol`/`base_asset` until a regen
  (`PREDICTION_INSTRUMENTS.md:324-326`) — the fallback chain handles it.
- **Acceptance:** category `<select>` → cqg sub-filter → a paginated, searchable table of human-readable markets with
  venue chip + resolution/close date; pw:L2 asserts category change narrows the list.

- [x] [BACKEND] P1. ✅ `read_prediction_catalogue(category?, canonical_question_group?, venue?, search?, limit, offset)`
      — new `deployment_api/services/prediction_catalogue.py`, widening the same prediction `prod/catalog.parquet` read
      `manifest_source.read_unique_instrument_count` uses, to project
      `underlying/raw_symbol/base_asset/venue/instrument_type/available_from/available_to/data_type/mvp` (schema-aware).
      **Deviation from the literal plan wording:** `canonical_question_group` is NOT a per-market column on
      `catalog.parquet` (verified against `build_instrument_catalogue.py`'s `CATALOG_COLUMNS` — only a separate
      shard-tracking bundle row carries it, `data_type=prediction_canonical_question_group`/`instrument_id=cqg`; real
      per-market cqg only lives in the availability MANIFEST, a different parquet). So the service DERIVES cqg per row
      via the SAME deterministic classifiers the IS adapters call at capture time
      (`classify_kalshi_to_canonical_group`/`classify_polymarket_to_canonical_group`, cached per unique
      venue+raw_symbol), then composes `category_for_group(cqg)` (cached per unique cqg) — bundle-grain rows are
      excluded (never a browsable market). Facet counts (`category_counts`/`cqg_counts`) computed over the
      venue+search-filtered set so the UI `<select>` always renders every bucket. Honest label fallback `raw_symbol` →
      `base_asset` (50 chars) → `event_title` (schema-checked, absent today) → `instrument_id`. Route
      `GET /api/data-status/prediction-catalogue` (`routes/prediction_catalogue.py`, mirrors
      `routes/catalogue_lifecycle.py`, mock-mode aware, registered in `main.py`). — deployment-api@9238983 + Evidence:
      `test_prediction_catalogue.py` 4 specs green (category facet+filter, cqg sub-filter, search+pagination,
      label-fallback/bundle-exclusion/honest-empty-on-read-failure) + `quality-gates.sh --no-fix` green (4549 passed; 5
      pre-existing baseline codex-compliance violations within tolerance, 0 new).
- [x] [BACKEND] P1. ✅ UAC facade — added `PredictionMarketCategory` + `category_for_group(cqg)` to the
      `unified_api_contracts.predictions` public facade (composes the existing `underlying_for_group` +
      `_category_for_underlying`). **Lives in `cross_venue_mapping.py`, not `two_axis.py`** as the plan suggested — a
      circular-import check confirmed `cross_venue_mapping.py` already imports `underlying_for_group` FROM `two_axis.py`
      and already has `_category_for_underlying` + `PredictionMarketCategory` imported, so composing there needs no new
      dependency edge (`two_axis.py` importing FROM `cross_venue_mapping.py` would have cycled). —
      unified-api-contracts@72fd959 + Evidence:
      `test_prediction_cross_venue_mapping.py::test_category_for_group_composes_across_all_categories` (crypto/
      financial/sports/weather/entertainment/politics/other) green + `quality-gates.sh --no-fix` green (188s).
- [x] [UI] P1. ✅ Prediction "Catalogue" surface — category `<select>` (crypto/politics/sports/… with MVP badge) → cqg
      sub-filter → paginated searchable table (label = fallback chain above, venue chip, resolution date). `[UI]` +
      pw:L2. — `PredictionCatalogueCard` (`src/components/PredictionCatalogue.tsx`), mirrors `LifecycleCards.tsx`'s
      `useX(...)` + loading/error/empty pattern; `fetchPredictionCatalogue` +
      `PredictionCatalogueRow`/`PredictionCatalogueResult` added to `client.ts`; representative mock rows (one per
      `PredictionMarketCategory`) added to `mock-api.ts`; mounted in `DataStatusTab.tsx` alongside its sibling lifecycle
      cards (`serviceName === "instruments-service"`). cqg sub-filter narrows to the selected category via a
      client-accumulated `cqg -> category` map built from rows seen so far (`cqg_counts` itself is NOT category-scoped
      server-side — see `deployment-api/services/prediction_catalogue.py`). MVP badge renders per-row (next to the
      category chip), not on the `<select>` itself — deviation from the literal wording, since MVP is a per-market
      attribute, not a per-category one. — deployment-ui@3bdb4e4 + Evidence: `PredictionCatalogue.test.tsx` 6 specs
      green (initial load, empty state, category-select narrows via new fetch call, debounced search triggers refetch,
      pagination Next/Prev, refresh) + `quality-gates.sh` full gate green (196s: tsc/eslint/89 unit tests/74.62%
      coverage/build all passed). `pw:L2` satisfied via Vitest per this plan's accepted pattern (live Playwright MCP
      browser was contended — multiple long-running `.playwright-mcp` Chrome processes from other concurrent sessions —
      not exercised live, same as the P2 UI unit).
- [x] **DECIDED (operator 2026-07-16): slug for v1 + document the follow-up.** Category from `canonical_question_group`;
      human label from the slug/base_asset/event_title fallback chain. Confirmed parseable from existing fields
      (`PREDICTION_INSTRUMENTS.md:217,230,247-266`). Never fabricate a title.
- [ ] [DATA] P3. _(follow-up)_ Add a real `question`/`title` column to the polymarket/kalshi adapters +
      `CATALOG_COLUMNS` + a regen so the label is the true question text (upstream title exists at parse time —
      `event_title` 100% hit for Polymarket sports — and is dropped before roll-up).

## P4 — Instrument Coverage Summary: canonical labels (A) + SPOT_ASSET population (B)

**Design guide.** Two INDEPENDENT workstreams. (A) is a small display fix; (B) is a data/backfill effort. Do (A) as a
quick win; (B) after the catalogue-address enabler.

**(A) Canonical labels.** The "Instrument Coverage Summary" is manifest-derived and shows RAW string values with no UAC
normalization: `coverage.py:_build_breakdowns` / `_build_latest_day_breakdown` group
`index[axis].fillna("").astype(str)` (~223-293), a blank → the `"__legacy__"` sentinel (`coverage.py:227,240`), and
`BreakdownsAccordion.tsx:84` `formatValueLabel` renders `__legacy__` → "(legacy — pre-job_id)" for EVERY axis (wrong on
instrument_type/data_type; it only means pre-job_id on the `job_id` axis). The canonical enum is
`_instrument_enums.py:17-82` (UPPERCASE SPOT_PAIR/PERPETUAL/… with a legacy→canonical map in the docstring lines 24-27).
**DO NOT rewrite the manifest grouping key** — `DataStatusTab.tsx:1863-1870` sends `{axis,value}` back verbatim as a
secondary-axis manifest query (shard-atom identity). Fix at the DISPLAY layer, raw value kept on hover. NOTE: the DeFi
type mix (LENDING vs A_TOKEN/DEBT_TOKEN, STAKING/YIELD_BEARING/LST) is CANONICAL-but-mid-migration — do not "fix" it;
only drain residual LENDING.

**(B) SPOT_ASSET population** (operator-approved). `SPOT_ASSET` is ALREADY a canonical type (`_instrument_enums.py:59`),
mapped to `LedgerAssetClass.SPOT_TOKEN`, with a `spot_assets` data-type family, and `InstrumentRecord` already carries
the address fields (`instrument.py`: `pool_address:213`, `base_asset_contract_address:221`,
`quote_asset_contract_address:225`, `atoken_address:235`, `debt_token_address:239`; validator 325-390 requires
`pool_address` OR `base_asset_contract_address` for on-chain types) — but **no live adapter emits SPOT_ASSET yet**. The
addresses already exist in the per-date parquet schema (`instrument.py:205-206`) and the catalogue builder already reads
`pool_address` (`build_instrument_catalogue.py` `_pool_address_of`; DeFi POOL `instrument_id == pool_address.lower()`);
they're just not projected into `CATALOG_COLUMNS` (`build_instrument_catalogue.py:264-303`). So the enabler is a
**projection + regen, not a re-fetch**. Goal: one SPOT_ASSET per unique (chain, token → contract_address) so every base
AND quote leg of a SPOT_PAIR/POOL (and LST/A_TOKEN/DEBT_TOKEN underlyings) resolves to a copy-pastable contract address.

- **Acceptance (A):** the summary shows canonical UPPERCASE labels / "(unlabeled)" for blank type/data_type; "(legacy —
  pre-job_id)" appears ONLY on the job_id axis; raw value visible on hover; the manifest query still works (key
  unchanged); pw:L2 spec on `BreakdownsAccordion`.
- **Acceptance (B):** `catalog.parquet` carries `pool_address` + `base_asset_contract_address` +
  `quote_asset_contract_address`; SPOT_ASSET records exist for every distinct DeFi + spot-CeFi token leg with an address
  (verified row counts on real infra); UI can show + copy the contract address; discovery-time emission keeps it
  current.

- [x] [UI] P1. ✅ _(A)_ Axis-aware `formatValueLabel(axis, value)` (`BreakdownsAccordion.tsx`) — the `__legacy__`
      sentinel renders "(legacy — pre-job_id)" ONLY on the `job_id` axis; "(unlabeled)" on every other axis
      (instrument_type/data_type/…). — deployment-ui@7853409 + Evidence: `BreakdownsAccordion.test.tsx` "labels
      **legacy** as '(unlabeled)' on a NON-job_id axis" + the existing job_id legacy test both green. `[UI]` + pw:L2.
- [x] [UI] P1. ✅ _(A)_ Display-only canonical alias map `canonicalInstrumentTypeLabel`
      (`deployment-ui/src/lib/data-status-helpers.ts`, from the UAC `_instrument_enums.py InstrumentType` docstring:
      spot→SPOT_PAIR, perp/perpetual→PERPETUAL, futures/future→FUTURE, option→OPTION, pool→POOL,
      lending_market/lending→LENDING, lst→LST, yield→YIELD_BEARING, etf→ETF), applied AFTER grouping to the
      `instrument_type` axis only. Unmapped values (already-canonical + DeFi mid-migration A_TOKEN/DEBT_TOKEN/STAKING)
      return verbatim (honest — never force-uppercased). Raw value stays the manifest query key + shows on hover
      (`title="raw: <value>"`). — deployment-ui@7853409 + Evidence: `data-status-helpers.test.ts`
      "canonicalInstrumentTypeLabel" + `BreakdownsAccordion.test.tsx` "canonicalises legacy instrument_type labels but
      keeps the raw query key" (asserts display=SPOT_PAIR, hover=`raw: spot`, onSelectValue sends raw `spot`) green.
      `[UI]` + pw:L2.
- [ ] [DATA] P2. _(A)_ Root-cause the legacy values — grep the instruments-service catalogue/manifest writer for where
      `instrument_type` is stamped; ensure new rows emit `InstrumentType.value` (uppercase); author a one-off legacy-row
      canonicalization migration (pattern `scripts/canonicalize_*_2026_*.py`). NOTE: `instrument_type` is a SHARD axis
      for MTDS/MDPS/features — the migration must preserve shard-atom identity across those services, not just IS.

      **ROOT-CAUSED 2026-07-17 — the finding reframes this todo; migration IN FLIGHT (dispatched sub-agent).** Measured
                              every asset group's live `_index/availability_index.parquet` against the UAC `InstrumentType` enum (31 values):
                              - **Non-canonical VALUES are already GONE** for cefi / defi / tradfi / prediction — **0** each. This todo's original
                                target (the lowercase/legacy DeFi values) was fully resolved by the P9 round-2 migrations (`@6f87a251` cefi
                                lowercase, `@66258618` tradfi blanks, `@4d63822d` defi data_type). Nothing left to root-cause there.
                              - **The REAL residual is BLANK `instrument_type` on CAPTURED rows** — the `__legacy__` sentinel the P9 table logged
                                as "CEFI `__legacy__` 4.85M / DEFI `__legacy__` 3.85M". Crosstab of `capture_status` × blank on live data:
                                **tradfi 0** ✅ (P9's migration met its stated bar), but **cefi 13,046** and **defi 65,443** captured rows are
                                still blank — **78,489 rows** total. Blank on NON-captured rows (empty_confirmed / expected_unattempted /
                                attempted_failed) is **honest and must stay** (those shards captured zero instruments, so they have no type).
                              - **Root cause = the same bug P9 already documented, with only PART of the fix applied**: the shared cefi/tradfi/defi
                                writer `writers.py::_write_venue` hardcoded `instrument_type=""` on `record_captured(...)`. **The WRITER IS
                                ALREADY FIXED for all three** (`b475ae8e` → `91fc7bd2` `_split_by_instrument_type`, called from `_write_venue`,
                                shared by every AG — verified by reading it at HEAD; **no writer change needed**). But the **backfill migration
                                only ever ran for tradfi** (`canonicalize_tradfi_instrument_type_2026_07_16.py` is hardcoded
                                `asset_group="tradfi"`). So cefi/defi simply never got their history backfilled.
                              - **Remaining work = generalise that migration to cefi + defi** (targeted per-shard object reads re-deriving the
                                type from each shard's own `instruments.parquet`; single-walk discipline; honest-blank when an object is
                                missing). Dispatched to a sub-agent with the full rule set; acceptance = **0 captured blank rows in cefi AND
                                defi**, non-captured blanks preserved, cross-service shard-atom re-confirmed (P9 established MTDS/MDPS/features
                                do NOT read `instrument_type` from this IS manifest for their own shard keys — each stamps its own — so the
                                tradfi migration was safely IS-only; that must be re-confirmed for cefi/defi before applying).
                              - **Also measured (NEW, out of this todo's scope — sports only):** the ONLY remaining non-canonical values anywhere
                                are in the **sports** index: `odds` 561,260 rows (BETFAIR/BETMGM…, 561,099 captured), `prediction_market` 1,709,
                                `prediction` 37, `SPORT` 16 (ODDS_API). Canonical members `EXCHANGE_ODDS` / `FIXED_ODDS` / `PREDICTION_MARKET`
                                exist, so these look mappable — but sports keys on `("data_type","league_id")` (UAC `SHARD_AXIS_MATRIX`), so
                                `instrument_type` is display-only there, a different axis and a different blast radius from this (A) todo.
                                Tracked as its own todo below rather than silently folded in.

- [x] [DATA] P2. ✅ _(A)_ Drained residual `LENDING` — **but NOT by "finishing the split", which would have corrupted
      the catalogue.** `scripts/drain_residual_lending_rows_2026_07_17.py`, **applied + independently verified on real
      prod infra**. **Correction to this todo's premise (the important part):** the instruction was to re-run the
      `canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py` pattern "for the remaining 3". Tested that
      first by running **that script's own pure `migrate()` over live prod data**: it would have written **1,766
      duplicate `instrument_id`s** (880 A_TOKEN + 880 DEBT_TOKEN) — it has **no dedup at all**, and the split twins
      **already exist**. Root cause: the 2026-07-13 run ADDED the A_TOKEN/DEBT_TOKEN rows but never REMOVED its LENDING
      sources (the plan's own P4-B note corroborates: "+904 rows, 9,456→10,360" is the 1:2 split _output_ with sources
      kept, not a net +452). So the residual was never "unsplit markets" — it was **already-split markets whose stale
      original was left behind**, and the correct fix is a guarded DELETE. **Also stale in this todo's wording
      (measured, not assumed):** residual = **893 rows = MORPHO 861 + COMPOUND_V3 26 + FLUID 6**. COMPOUND_V3 is in the
      residual (not listed in the todo); **AAVE_PLASMA does not exist as a venue in the catalogue at all** (no
      AAVE/PLASMA venue match); AAVE_V3 is already fully drained (0 LENDING). All 893 are delisted/aged (**0 active**) —
      no live row was mislabeled — but `LENDING` is **not a real `InstrumentType` enum member**, so historical-identity
      consumers (backtests, PnL recon) still hit the crash/mislabel class, and the pair falsely reads as "market
      delisted 2026-06-24, different one listed" when only our labelling changed. **Safety design — delete ONLY where a
      twin provably supersedes**: per row the required twin id(s) are derived from the row's OWN key shape
      (`:LENDING_MARKET:<pair>` → BOTH `:A_TOKEN:A<pair>` AND `:DEBT_TOKEN:DEBT<pair>`; `:SUPPLY:<sym>` →
      `:A_TOKEN:<sym>`; `:BORROW:<sym>` → `:DEBT_TOKEN:<sym>`) and EACH must exist **and** have `available_from <=` the
      original's. Anything failing is KEPT + reported — losing real lifecycle history is far worse than a stale label. —
      instruments-service@e4fdd56c + **Evidence (real infra, independently re-read — not the script's own log)**:
      pre-flight proof that the twins are complete — **867/867** MORPHO/FLUID and **26/26** COMPOUND_V3 LENDING rows
      have their twin, and **867/867 + 26/26 twins start EARLIER-OR-EQUAL** (0 start later; byte-identical in practice,
      e.g. `MORPHO-ETHEREUM:LENDING_MARKET:cbBTC-USDT:0x2b8019` from 2023-12-28 vs its `:A_TOKEN:AcbBTC-USDT:0x2b8019`
      twin from 2023-12-28). Run: `11,776 → 10,883` rows (−893); guard reported
      `deletable=893, kept_no_twin=0, kept_twin_starts_later=0, kept_unknown_shape=0`. Post-verify (fresh read):
      **LENDING = 0**, **zero non-enum instrument_type values remain**, all **9 other instrument_types byte-identical**
      (delete-only, A_TOKEN stays 1,117 / DEBT_TOKEN 1,060), and **all 893 deleted markets are still fully represented
      by their twins — 0 orphaned**. Rollback:
      `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.20260717-111412.lendingdrain.defi.bak.parquet`.
      Unit: `tests/unit/migrations/test_drain_residual_lending_rows.py` 10 passed — each safety branch pinned
      individually (deleted-when-twins-complete; **KEPT when a required twin is missing**; **KEPT when a twin starts
      later (history would be lost)**; kept on unknown key shape; wider twin OK; non-LENDING never touched; idempotent).
- [ ] [DATA] P3. _(NEW — side-discovery 2026-07-17, measured while root-causing the (A) legacy-values todo above)_
      **Sports is the last asset group carrying non-canonical `instrument_type` values.** Live sports
      `_index/availability_index.parquet` (5,353,331 rows) holds `odds` **561,260** rows (BETFAIR / BETFAIR_EX_EU /
      BETFAIR_EX_UK / BETFAIR_SB_UK / BETMGM …; 561,099 of them `captured`), `prediction_market` **1,709**
      (KALSHI/POLYMARKET), `prediction` **37**, `SPORT` **16** (ODDS_API) — none are UAC `InstrumentType` members, while
      plausible canonical targets DO exist (`EXCHANGE_ODDS` / `FIXED_ODDS` for exchange-vs-sportsbook venues,
      `PREDICTION_MARKET`). cefi/defi/tradfi/prediction are all **0** non-canonical, so sports is the only remainder.
      **Deliberately NOT folded into the (A) todo**: sports keys on `("data_type","league_id")` (UAC
      `SHARD_AXIS_MATRIX`), so `instrument_type` is a DISPLAY axis there rather than a shard axis — different blast
      radius, and the `odds` → `EXCHANGE_ODDS` vs `FIXED_ODDS` split is a real per-venue semantic decision (Betfair
      EXCHANGE vs sportsbook), not a mechanical uppercase. Needs a root-cause of the sports writer's stamping site + an
      operator-confirmable mapping before any migration.
- [ ] [DATA] P3. _(NEW — side-discovery 2026-07-17, found while verifying the LENDING drain)_ **DeFi POOL
      `instrument_id` is not unique across chains.** The live defi catalogue carries **6 duplicated `instrument_id`s (12
      rows)** where the SAME pool contract address is deployed on TWO chains and both rows key on
      `instrument_id == pool_address.lower()`: `0x004c167d…` = CURVE on **AVALANCHE + OPTIMISM**; `0x01abc00e…`,
      `0x03cd191f…`, `0x06df3b2b…`, `0xc6a5032d…`, `0xfeadd389…` = BALANCER on **ETHEREUM + POLYGON** (deterministic EVM
      deployment puts the same address on multiple chains). Each pair has a DIFFERENT `available_from`, so they are
      genuinely distinct instruments colliding on one id. Pre-existing and **out of scope for the LENDING drain (left
      untouched — verified still exactly 6 before and after)**. Blast radius is small (6 of 10,883) but the CLASS is an
      identity-uniqueness violation: any consumer keying on `instrument_id` alone silently picks one chain's pool. Fix
      direction: include `chain` in the DeFi POOL identity (or dedupe key) — needs a shard-atom check across
      MTDS/MDPS/features before changing, same as any identity migration.
- [x] **DECIDED (operator 2026-07-16): POPULATE SPOT_ASSET for every distinct token leg** (DeFi + spot-CeFi). Decomposed
      below.
- [x] [DATA] P1. ✅ _(B, enabler)_ Catalogue regen **completed on real infra**, safely. `--mode full` was evaluated
      first and found to CONFLICT with prior direct-patch migrations: the 2026-07-13 atokendebttoken migration alone
      added 904 non-reproducible rows (9,456→10,360 rows — MORPHO/FLUID 1:2 splits of already-catalogued historical
      rows; see `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` §Stage 4) that a from-scratch raw walk
      cannot regenerate (they're not derived from repeatable rollup logic). Confirmed via a real `--mode full` attempt
      that hit `CATALOGUE_SHRINK_BLOCKED` (new=9,461 < current=10,303) — the monotonic guard correctly refused to
      promote, which would otherwise have SILENTLY REVERTED that completed migration plus other direct-patch fixes
      (drift/pacifica removal, etc.). Root-caused (not just retried) and switched to `--mode incremental` instead — safe
      by construction: loads the previous catalogue, re-walks only a bounded recent window (self-widening, 21 days this
      run), and preserves the frozen historical tail untouched, so it can only ADD the new columns to recently-active
      rows, never regress prior migrations. — Evidence (real infra, independently re-verified via a fresh
      `pd.read_parquet` after the fact, not just the run's own log): defi `catalog.parquet` `10303→10387` rows
      (monotonic ACCEPT), `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` new GCS
      generation confirmed via `gcloud storage ls -l`; 24 columns (was 18); non-null counts `pool_address=7175/10387`,
      `base_asset_contract_address=8534/10387`, `quote_asset_contract_address=8183/10387`, `atoken_address=181/10387`,
      `debt_token_address=14/10387` (sparse — only Aave populates it, expected). CeFi needed NO regen for this enabler:
      cefi rows are centralized-exchange listings with no on-chain address of their own, so all 4 new columns are
      correctly, honestly blank for all 424,670 cefi rows (verified) — not a gap, the accurate state. **Known limitation
      (documented, not silently dropped):** the incremental window means historical/delisted defi rows OUTSIDE the last
      ~21 days (1,455 "frozen-tail" rows per the run's own merge log) still lack the new address columns — a full
      historical column-backfill without disturbing prior migrations would need a dedicated targeted script (read
      existing row → look up its own historical by_date snapshot → patch just the 4 columns), not a `--mode full`
      rebuild; tracked as a follow-up, not blocking SPOT_ASSET population (which only derives from rows that DO have
      addresses — honest-absence for the rest).
- [x] [DATA] P1. ✅ _(B)_ SPOT_ASSET backfill/migration — `scripts/backfill_spot_asset_population_2026_07_16.py` derives
      one SPOT_ASSET row per unique `(chain, address)` from the now-regenerated catalogue: DeFi walks SPOT_PAIR/POOL
      (base+quote legs)/LST/A_TOKEN (underlying + Aave receipt `atoken_address` when populated)/ DEBT_TOKEN rows;
      quote-leg symbols (no standalone `quote_asset` column in `CATALOG_COLUMNS`) are parsed best-effort from the
      DEX-pool `glued_pair_id` projection, honest-absence otherwise. Idempotent (dedups against existing
      `instrument_id`s — verified: re-running post-apply adds 0 rows). — instruments-service@e66a57b6 (shipped via
      `quickmerge.sh --agent --files`) + **run on real infra, independently verified**: defi `catalog.parquet`
      `10387→11776` rows (+1,389 SPOT_ASSET, 100% non-blank `base_asset_contract_address`, 0 duplicate `instrument_id`,
      9 real chains represented ARBITRUM/AVALANCHE/BASE/BSC/ETHEREUM/LINEA/OPTIMISM/POLYGON/SOLANA — Solana addresses
      independently confirmed correctly base58-formatted, not corrupted EVM hex); pre-existing 10,387 rows byte-for-byte
      unchanged (instrument_type crosstab sums identically). Backup snapshots:
      `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.20260717-090927.spotasset.defi.bak.parquet`,
      `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.20260717-090945.spotasset.cefi.bak.parquet`.
- [x] [DATA] P1. ✅ _(B)_ CeFi-spot leg mapping — folded into the same backfill script's `derive_cefi_spot_assets`:
      every distinct cefi `base_asset` symbol mapped through the Ethereum-mainnet `DEFI_MAJOR_ASSET_ADDRESSES` registry
      (native ETH/BTC redirected to their canonical wrapped WETH/WBTC form first, matching the plan's "ETH → WETH/native
      on ethereum" spec and `token_wrapping.py`'s wrap-direction convention); a symbol absent from the registry is
      skipped + logged, never fabricated. — **run on real infra, independently verified**: cefi `catalog.parquet`
      `424670→424699` rows (+29 SPOT_ASSET, all ETHEREUM chain, 100% non-blank addresses, 0 duplicates); 3,325 distinct
      cefi symbols had NO registry entry (mostly tokenized-stock/leveraged/exotic long-tail symbols, e.g.
      `AAPLX`/`BTC3L`/`1000PEPE` — honestly logged as unresolved, not invented). **Known gap (documented, matches the
      plan's own "if present — check" framing):** `catalog.parquet` has no standalone `quote_asset` column for cefi rows
      either, so this covers cefi BASE legs only; quote legs (a handful of majors/stables that mostly already resolve
      via their OWN base_asset row elsewhere) are a follow-up.
- [x] [BACKEND] P1. ✅ _(B)_ Make SPOT_ASSET emission normal at token-pair discovery time (future backfills + live) so
      the dump is continuous, not a one-off migration. curve/uniswap_v2/uniswap_v3 (pool base+quote legs) and
      renzo/etherfi/solend (LST/A_TOKEN/DEBT_TOKEN's own receipt-token leg) now emit a SPOT_ASSET sibling
      `InstrumentRecord` alongside their primary record, reusing the SAME on-chain address + decimals already resolved
      (no re-fetch). Shared pure helpers `build_spot_asset_record`/`build_spot_asset_siblings_for_pool` in
      `defi_utils.py`. Honest-absence: a leg with no resolvable contract address or decimals is skipped, never
      fabricated. LST siblings correctly label the actual on-chain receipt token (EZETH/WEETH), not the primary record's
      economic-peg "ETH" label. — instruments-service@ce56d499 + Evidence: ruff/basedpyright clean (full tree); pytest
      4379 passed / 8 failed (all 8 in `test_measure_honest_coverage.py` — a different concurrent agent's live WIP in
      this shared slot-3 checkout, untouched here — and `test_understat_adapter_coverage.py`, a pre-existing
      sports-adapter failure with zero overlap; none of the 10 files in this commit appear in the failure list —
      collision carve-out, precedent: this plan's P8 UI todo deployment-ui@12c94be). New/updated unit coverage:
      `test_defi_adapters_comprehensive.py` (Curve/UniswapV2/UniswapV3/EtherFi SPOT_ASSET-sibling assertions),
      `test_renzo_metadata.py`, `test_solend.py` (per-reserve single SPOT_ASSET sibling, not duplicated across the
      A_TOKEN/DEBT_TOKEN pair). _(Shipped via direct push, not quickmerge — self-caught process error, flagging per
      honesty; content verified green per the evidence above.)_
- [x] [UI] P2. ✅ _(B)_ Surfaced `base_asset_contract_address` as a **copyable** field on the instrument drilldown rows.
      The prior session's TWO-REPO scoping finding was **re-verified and still held**
      (`rg base_asset_contract_address     deployment_api/` → 0 hits), so this shipped as backend-then-UI. **Backend**
      (deployment-api@13a8f0b): the address is a genuine per-row column of the (venue, day) bundle parquet the drilldown
      ALREADY loads — verified against real prod GCS: a live `UNISWAP_V3-ETHEREUM` day file carries
      `base_asset_contract_address` **484/484 non-null** with true mainnet addresses. So no new read and nothing
      invented: extracted a shared `_column_by_symbol(df, symbol_col, value_col)` helper and routed BOTH `base_asset`
      (pre-existing) and the new address through it, so the two cannot drift on absent/blank handling. **Honest absence
      is encoded in the shape**: a bundle WITHOUT the column omits the field entirely (all of CeFi — no on-chain address
      exists), while a present-but-blank cell normalises to `null` — "not applicable" and "we looked and found none"
      stay distinguishable, and a zero/placeholder address is never emitted. (`chain` deliberately NOT added: it is
      **not** a bundle column — it lives in the venue name (`UNISWAP_V3-ETHEREUM`) and the UI already holds it on the
      resolved `detail.coord` for defi, which is a real shard axis there. Deriving a second copy would have been
      fabrication.) **UI** (deployment-ui@a860937): new `CopyableAddress` button on the standard instrument row — elided
      `0xa0b8…eb48` display (rows are dense) with the FULL address in both the `title` tooltip and `data-address`, and
      click-to-copy writing the **full** value, mirroring the house clipboard pattern in `DeploymentResult.tsx` (copy →
      "✓ copied" → 2s reset). Renders only when the backend actually supplied an address. **Routing verified, not
      assumed — this nearly bit**: my first specs failed and the investigation showed the modal has TWO row paths
      (`BundleRow` vs the standard row). Confirmed by reading `_bundling_mode()` that instruments-service resolves to
      **`per_venue_day_bundle`**, and the UI gates `isBundled` on **`per_underlying`** ONLY — so IS rows genuinely flow
      through the standard path this change edits. Had it been the other way, the field would have been invisible for
      exactly the rows that carry addresses. + Evidence: **real-GCS run of the SHIPPED backend** —
      `_expand_per_venue_day_bundle` over the live `UNISWAP_V3-ETHEREUM` 2026-07-16 bundle returns **473/473 entries
      carrying `base_asset_contract_address`** with genuine values (`1INCH` →
      `0x111111111117dc0aa78b770fa6a738034120c302`, the real mainnet address). Backend unit:
      `test_data_status_drilldown.py` **43 passed** incl. new `TestBaseAssetContractAddress` ×3 (address reaches the
      entry and is **per-row, not smeared**; a bundle without the column **omits** the field; a blank cell → `None`). UI
      unit: `DataStatusDrilldown.test.tsx` **19 passed** incl. 3 new specs (renders the affordance + full address
      reachable via title/data-address; **copies the FULL address, not the elided display**; no affordance at all for a
      row without one). Full `quality-gates.sh` **green (174s: tsc/eslint/vitest/build)**; backend ruff clean +
      basedpyright **0 errors (= HEAD's 0)**. `[UI]` + pw:L2 via Vitest per this plan's accepted pattern; mock-api.ts
      carries a real WETH address on the captured row and deliberately omits it on the other two so mock mode exercises
      both branches. _(Spec note: the 3 UI specs reuse the test file's existing prediction coord fixture rather than an
      instruments-service one — the address rendering is service-agnostic (it only checks the field), and the
      IS-routes-to-the-standard-path question is settled by the `_bundling_mode` analysis above rather than by the
      fixture.)_
- [x] **DECIDED (default): summary shows the CANONICAL label with the raw value on hover** — covered by the two (A)
      todos above.

## P5 — Remove the redundant hierarchical-drilldown button (instruments-service only)

**Design guide.** `DataStatusTab.tsx:1884` renders `LazyDrilldownDetails` → `HierarchicalShardDrilldown` inside each
asset-group box of the Instrument Coverage Summary, for every service. For **instruments-service** the axes collapse to
`venue → [chain] → date` (`data_status_axis_matrix.py:63-70`) — a strict, shallower SUBSET of the TURBO "Data Coverage"
grid right below it (`DataStatusTab.tsx:3383+`, which drills the same axes and opens a richer 4-tab `ShardDetailModal`).
The two features that would make the tree non-redundant (per-instrument_id load-more; per-leaf pipeline_mode/source
provenance) don't fire for IS (single-source venue-level reference data). **Keep the component** — it's the primary
drilldown for prediction (`DataStatusTab.tsx:4111`) + MTDS/features/sports.

- _Gotcha:_ do NOT gate on a blanket `serviceName !== "instruments-service"` — the `:1884` drilldown also renders for
  IS-sports and IS-prediction, whose axes the grid does NOT cover. Use an **axis-comparison predicate** (compare the
  pair's hierarchical axes vs what the grid already expands) so only IS cefi/tradfi/defi are suppressed.
- **Acceptance:** on the IS page the Data Coverage grid renders but the redundant Instrument-Coverage-Summary drilldown
  button is gone for cefi/tradfi/defi; prediction (`:4111`) + sports drilldowns intact; other services unchanged. pw:L2.

- [x] [UI] P1. ✅ Gated the `:1884` `LazyDrilldownDetails` behind the axis-comparison predicate
      `isHierarchicalDrilldownRedundant(service, assetGroup, shardAxisMatrix)` — suppresses the drilldown ONLY for
      instruments-service asset groups whose shard axes ⊆ `{venue, chain}` (cefi/tradfi/defi); IS sports (`league_id`) +
      prediction (`canonical_question_group`) + every other service keep it. Predicate is a pure helper in
      `data-status-helpers.ts` (testable in isolation; `HierarchicalShardDrilldown.tsx` + `LazyDrilldownDetails`
      untouched). — deployment-ui@953fa81 + Evidence: `data-status-helpers.test.ts` 5 specs green
      (cefi/tradfi/defi→true, sports/prediction/MTDS→false, case-insensitive, fail-open) + full UI QG green
      (tsc/eslint/vitest 87/build). `[UI]` + pw:L2 (Vitest regression spec). _(Minor file-scope note: the pure predicate
      lives in `data-status-helpers.ts` rather than inline in `DataStatusTab.tsx` — the plan's "DataStatusTab.tsx only"
      note was to keep `HierarchicalShardDrilldown`/`LazyDrilldownDetails` untouched, which holds; a pure exported
      helper is far more testable.)_

## P6 — Instrument catalogue explorer (per-AG list, CSV, search, MVP filter)

**Design guide.** The building blocks exist but don't compose, and the MVP filter is only on the coverage grid.

- _What exists:_ per-AG drill `GET /data-status/drilldown/{service}/{ag}` (`_deploy_turbo.py:59`); instrument LIST only
  at the deepest leaf (`list_instruments_for_shard`, `_instruments.py:357` — single day + full tuple); CSV at leaf
  (`build_csv_export`, `_csv_export.py:133`) + per-venue bundle (`_csv_export.py:345`); leaf search
  (`_apply_search_and_pagination`, `_instruments.py:272`, caps `DEFAULT=50/MAX=500/SEARCH=100` at `:243-247`); cross-AG
  search `GET /data-status/instruments/search` (`data_query_service.py:283`). `get_instruments_list`
  (`data_query_service.py:192`) is effectively stale (its `{venue}/{folder}/` prefix mismatches the live
  `instrument_availability/by_date/day=/venue=/` layout — `_instruments.py:64-86`).
- _MVP:_ `is_mvp(asset_group, venue, instrument_type, data_type, *, base_asset, league_id, market_group, source)`
  (`_mvp_scope_predicate.py:229`) + `filter_to_mvp` (`_coverage_scope.py:72-114`) power the grid's `scope=mvp` toggle
  ONLY (`VenueCoverageTable.tsx`, default 'mvp'); the LIST + CSV paths never call it.
- _Decision:_ BOTH, phased. Phase 1 = availability-derived; Phase 2 = a true-catalogue projection.
- _Gotchas:_ **single-walk discipline** — build the new `/catalogue` on `read_availability_index` or ONE bounded
  single-day `_shard_prefix` walk (`_collect_parquet_files`, `max_results` cap); NO whole-corpus walk. **Label it
  "captured instruments (availability-derived)", NOT "the catalogue"** — deployment-api cannot reach the IS
  `InstrumentCatalogReader` SSOT (T4).
- **Acceptance:** an MVP-only toggle + per-row is_mvp badge on the instrument list; "Download CSV" == the on-screen
  filtered (search+mvp) view; a per-AG explorer lists instruments with id-substring search + MVP filter + CSV. pw:L2.

- [x] [BACKEND] P1. ✅ _(phase 1)_ Added `mvp_only` + a per-row `is_mvp` tag to `list_instruments_for_shard` (calls UAC
      `is_mvp(...)`, mirroring `filter_to_mvp`), and `search` + `mvp_only` to `build_csv_export` so CSV == filtered list
      (both read the SAME cached `_list_instruments_full` tag — structurally cannot drift). Threaded through
      `_query_meta.py` (`/instruments-for-shard`) + `_downloads.py` (`/download-csv`). TRACE-FIRST finding: confirmed
      against the LIVE availability_index.parquet schema (cefi/tradfi/prediction) that `base_asset`/`market_group` are
      NOT real manifest columns (42/41 cols, neither present) — `filter_to_mvp`'s read of those has been a silent no-op
      in production wherever the MVP rule demands them (CeFi base_ccys / TradFi underliers / Prediction market_groups
      are all non-empty). Not fabricated here: `base_asset` is sourced from the instruments-service bundle parquet's own
      column (genuine, varies per-instrument) when available; `league_id`/`source` from the existing manifest join (real
      v9 columns); `market_group` stays honestly `None` (no real source at this leaf). Pre-existing gap, out of this
      unit's scope — flagged for follow-up. — deployment-api@abcce0b + Evidence: `TestMvpOnlyAndIsMvpTag` (4 tests:
      is_mvp tag present, base_asset→base_ccy plumbing from bundle parquet, mvp_only narrows total_count, CSV/list
      row-count parity) in `test_data_status_drilldown.py`; full `quality-gates.sh` green (4561 passed; 1 unrelated
      pre-existing failure in `test_route_deployments_inventory_aws.py::test_inventory_route_includes_aws_items`, zero
      import/code overlap).
- [x] [BACKEND] P2. ✅ _(phase 1)_ New `GET /data-status/catalogue` (+ `/download-catalogue-csv` twin) in a new
      `_catalogue.py` submodule, parameterised by pinned `(service, asset_group)` + optional venue/instrument_type/
      data_type + search + mvp_only → de-duped (latest-written_at-wins) instrument list with `is_mvp` +
      `capture_status`. Built ONLY on `_read_availability_index` (single-walk discipline — no whole-corpus GCS walk).
      Labeled `"captured instruments (availability-derived)"` in every response. Refactored
      `_coverage_scope.py::filter_to_mvp` to extract a shared `is_mvp_for_manifest_row` predicate (pure refactor, no
      behaviour change) so the coverage grid's `scope=mvp` toggle and this new explorer can't drift on axis sourcing. —
      deployment-api@1e3c7b4 + Evidence: `test_route_data_status_catalogue.py` (6 tests: de-dupe, mvp_only filter,
      search substring, venue narrow, manifest-read-failure→500, CSV/JSON row-count parity); full `quality-gates.sh`
      green (same run as P1, no incremental failures).
- [x] [UI] P2. ✅ _(phase 1)_ `InstrumentsModalStandard` (`DataStatusDrilldown.tsx:481`) — "MVP only" toggle (checkbox,
      resets pagination like `debouncedSearch`) + per-row MVP badge + `mvp_only` threaded into
      `fetchInstrumentsForShard` + `buildCsvDownloadUrl` (CSV/list parity; `search` was already NOT threaded into the
      CSV builder pre-existing — out of this unit's explicit scope). New `CatalogueExplorer.tsx` panel: asset_group
      select + debounced venue/instrument_type/data_type/search narrows + MVP toggle + pagination, driven by new
      `fetchInstrumentCatalogue` +`buildCatalogueCsvDownloadUrl` (+ `InstrumentCatalogueRow`/`Response` types) in
      `client.ts`; renders the `"captured instruments (availability-derived)"` label verbatim; "Download CSV" carries
      the SAME filters as the on-screen view. Mock handlers for `/catalogue`+`/download-catalogue-csv` (4 rows spanning
      captured/empty_confirmed/attempted_failed × mixed `is_mvp`). Mounted IS-only in `DataStatusTab.tsx`, sibling to
      `PredictionCatalogueCard`. — deployment-ui@90eba8c (toggle+badge), @9648f42 (Catalogue Explorer — this commit ALSO
      accidentally swept a concurrent agent's uncommitted `FixturesBrowser` hunk into `client.ts`/`mock-api.ts` via
      quickmerge `--files`'s whole-file `git add`, same failure class as the `12c94be` incident above), @57d913d
      (forward-fix: surgically reverted exactly those 2 foreign hunks — 87 lines, byte-diffed against the original
      uncommitted patch to confirm exact scope; the other agent's untracked `FixturesBrowser.tsx`/`.test.tsx` files were
      never touched).

      **Separately-surfaced + fixed same session**: `InstrumentsModalStandard` (via exported `InstrumentsModal`) had
                                                                                                                              been UNREACHABLE from the live UI since `f4a8e4e` (2026-04-24) rerouted its only opener (CeFi per-data-type
                                                                                                                              date-chip clicks) to `ShardDetailModal` without deleting the now-dead `instrumentsModal` state/import/render call
                                                                                                                              in `DataStatusTab.tsx` — today's MVP-toggle work was code-correct but invisible to any user until fixed.
                                                                                                                              Confirmed `ShardDetailModal` is NOT a superset (its payload tab is a read-only non-searchable non-paginated
                                                                                                                              truncated table; download tab is one combined parquet/CSV, no per-instrument multi-select) — so nested
                                                                                                                              `InstrumentsModal` inside `ShardDetailModal`'s `grouped`-shard_class payload tab via a new "Browse & search all
                                                                                                                              instruments →" trigger (uses `detail.coord` — the server-resolved axes, not the caller's possibly-`"AUTO"`
                                                                                                                              guess), mirroring the existing `schemaOpen` nested-modal pattern in `DataStatusDrilldown.tsx`. Deleted the dead
                                                                                                                              `instrumentsModal` state/import/render call (no shim). — deployment-ui@8958345.

                                                                                                                              Evidence: `DataStatusDrilldown.test.tsx` +3 specs (MVP toggle → `mvp_only=true` refetch; badge only on
                                                                                                                              `is_mvp:true` rows; CSV URL threads `mvp_only`); new `CatalogueExplorer.test.tsx` (8 specs: initial render+label,
                                                                                                                              empty state, MVP badge, MVP toggle refetch, debounced search, pagination, CSV/on-screen filter parity, refresh);
                                                                                                                              `ShardDetailModal.test.tsx` +1 spec (nested-modal reachability, asserts the resolved coord reaches
                                                                                                                              `fetchInstrumentsForShard`). Full `quality-gates.sh` green ×3 (one per shipped commit, 90-227s) — host hit severe
                                                                                                                              transient multi-agent contention mid-unit (load avg peaked ~82-90/10 cores), flaking 3 DIFFERENT unrelated
                                                                                                                              pre-existing tests across retries (`capability-verdict-matrix-loader`, `DeploymentsList`, `DeployMissingButton`/
                                                                                                                              `MlExperiments`), each confirmed zero diff-overlap + passing in isolation; final runs green once load eased.
                                                                                                                              `[UI]` — pw:L2 NOT run: `.playwright-mcp`'s shared profile was actively driven by another concurrent agent
                                                                                                                              (sustained 130-145% CPU Chrome renderer, confirmed via `ps aux` at both start and end of this unit) — same
                                                                                                                              carve-out as this session's P2/P3 UI units; code+mock+Vitest evidence stands in.

- [x] **DECIDED (operator 2026-07-16): BOTH, phased.** Phase 1 above; Phase 2 below.
- [ ] [BACKEND] P3. _(phase 2)_ True-catalogue source — add a deployment-api→instruments-service read path OR a
      manifest-backed catalogue projection so the explorer can list instruments that EXIST in the catalogue (not just
      captured). Respect T4 (integrate by contract/projection, not a direct service→service import).

## P7 — Data Coverage breakdown: CeFi chain-axis drift + "instruments breakdown" button

**Design guide.** Confirmed against the SSOT: the shard/display axis for cefi is `("venue",)` and only defi adds `chain`
(`data_status_axis_matrix.py:67-69`). But the cefi CLOB-perp venues `PACIFICA-SOLANA` and `LIGHTER-ZKSYNC`
(`unified-api-contracts/.../registry/venue_constants.py:445-447`) use the DeFi-style `{PROTOCOL}-{CHAIN}` naming, so a
chain-deriving parser (splitting the venue name on `-`) manufactures `SOLANA`/`ZKSYNC` chains in the cefi breakdown.
Those venues are already unique by name — cefi must not be chain-keyed; only multi-chain DeFi protocols (Aave deployed
across chains) need the chain axis.

- _TRACE-FIRST (not pinned by the audit):_ grep the TURBO grid renderer + breakdown builder for where a `chain` is
  derived from the venue string (likely a `split("-")` / `rsplit`), then gate that derivation on `asset_group == 'defi'`
  so cefi renders venue-only. Confirm the fix in both the backend breakdown and the UI grid.
- _"instruments breakdown" button:_ this overlaps the P5 redundancy — resolve it with the same decision (remove/merge)
  so its meaning is unambiguous.
- **Acceptance:** the CeFi breakdown shows venues only (no `solana`/`zksync` chain sub-rows); DeFi still shows chains;
  shard-level CSV (`download-shard-csv`) present + consistent across AGs; the "instruments breakdown" button is
  removed/merged. pw:L2.

- [x] [BACKEND] P1. ✅ Gate the venue→chain derivation on `asset_group == 'defi'` (cefi = venue-only) —
      `_build_v4_sub_dimensions` chains breakdown now fires only for `cat == 'defi'` (`breakdowns_domain.py`).
      Trace-first confirmed the leak: the live cefi manifest holds residual split rows (`venue=PACIFICA chain=SOLANA` /
      `venue=LIGHTER chain=ZKSYNC` — 4617 chain-nonempty rows, only distinct cefi chains `SOLANA`/`ZKSYNC`);
      `_build_breakdowns` already uses the UAC axis matrix (cefi = instrument_type/data_type, no chain) so only the
      ungated `extras["chains"]` sub-dimension leaked. UI grid needs no change — it renders the backend
      `extras["chains"]` verbatim, so gating the backend suppresses cefi chain sub-rows. — deployment-api@47a7f67 +
      Evidence: `test_v4_sub_dimensions_chain_gated_on_defi.py` (cefi→no chains, defi→chains) + quality-gates.sh green
      (117s) + **real-data browser validation 2026-07-16** (local deployment-api on real GCS + deployment-ui +
      Playwright): the LIVE build (`/data-status/turbo?pipeline_mode=…` cache-bypass, and
      `/data-status/coverage-summary`) returns `CEFI chains: None`. _(Read-side display gate only; manifest query key
      unchanged. NOTE — the writer-side split rows `venue=PACIFICA chain=SOLANA` are a separate manifest drift, out of
      P7's read-side scope; see Progress Log.)_
- [x] [BACKEND] P2. ✅ _(P7 follow-up — stale rollup cache)_ FIXED at the read layer. The TURBO "Data Coverage" grid is
      served from a pre-built GCS rollup blob (`data_status_rollup_worker.py`); a blob written BEFORE the P7 fix still
      carried `cefi.chains=['SOLANA','ZKSYNC']` (found via Playwright against real data — the worker DOES use the gated
      `_build_v4_sub_dimensions`, so it self-heals on its next 5-min run post-deploy, but that leaves a stale-blob
      window). Added `strip_non_defi_chains()` applied in `slice_rollup_to_window` beside `strip_defi_ghost_venues`, so
      any non-defi category's `chains` breakdown is dropped at the rollup-CONSUMPTION layer — the TURBO grid is
      cefi-venue-only regardless of blob staleness (a no-op on a correctly-rebuilt blob). — deployment-api@e27ba4b +
      Evidence: `test_data_status_beta_rollup_and_cli_config.py::test_strip_non_defi_chains_drops_cefi_keeps_defi` +
      `::test_slice_rollup_strips_stale_cefi_chains_keeps_defi` green (ruff/basedpyright clean; 10/10 in the file).
      _(Committed via collision carve-out — foreign live P6 WIP was mid-edit in the shared checkout; scoped-verified my
      2 files.)_
- [x] [UI] P2. ✅ Resolved by the P5 gate. There were two overlapping "Instrument breakdown" affordances: (a) the nested
      link inside the hierarchical drilldown (`DataStatusTab.tsx:4092`), suppressed for IS cefi/tradfi/defi by the P5
      predicate; and (b) the Data Coverage grid's venue-detail "Instrument breakdown" link (`DataStatusTab.tsx:5582` →
      `handleVenueClick` → `VenueDetailPanel`). Removing (a) leaves (b) as THE single, unambiguous instrument-breakdown
      path. Shard-level CSV stays consistent across AGs — the grid retains its
      `shard-csv-date-found`/`shard-csv-date-missing` per-date CSV download buttons (`DataStatusTab.tsx:5514,5553`)
      unchanged. — deployment-ui@953fa81 (same P5 change; no separate button removal needed).

## P8 — Sports league-drilldown consistency + TEAMS data-correctness

**Design guide.** Drillability is set per data_type by the `axis` in `SPORTS_DATA_TYPE_META`
(`deployment-api/deployment_api/services/data_status/sports_helpers.py:77-219`): `per_league_*` → the response carries a
`leagues` map → the UI's `hasLeagues` gate (`DataStatusTab.tsx:4288,5279`) renders a league drilldown; `global_*` →
`per_league: None` → no league section at all. So some sources drill by league and some don't. Separately, the deeper
per-fixture drill + downloads are hardcoded to `name === "FIXTURES"`
(`DataStatusTab.tsx:5285,5385,5393,5433,5440,5462`).

- _TEAMS data-correctness drift (decided → direction A):_ TEAMS is classed `global_trigger_date` in
  `sports_helpers.py:139` + codex, but the IS writer emits **per-league** TEAMS rows (`sports_reference_core.py:293,335`
  — `row_key={date, data_type:'TEAMS', league_id}`) AND both the UAC `SHARD_AXIS_MATRIX`
  (`data_status_axis_matrix.py:70`) and `gcs_paths.py:127` classify TEAMS per-league — a 4-way drift. Fix: flip the
  TEAMS axis to `per_league_trigger_date` (the branch at `sports_helpers.py:582-625` already works for PLAYER_VALUES,
  which shares TEAMS' trigger-date cadence), a read-side change that RESTORES shard-atom identity.
- _Seasonal TEAMS is handled by the DATE axis:_ TEAMS is captured on trigger dates (season-start + transfer windows)
  keyed by `(date, league_id)`, so each season's roster is a distinct snapshot under the same league — the drilldown
  `TEAMS → league_id → date` surfaces per-season change as the date axis; no extra dimension.
- **Acceptance:** TEAMS is league-drillable and consistent with STANDINGS; genuinely-global data_types (LEAGUES, VENUES)
  show an explicit "global reference entity" affordance instead of a silent gap; off-season dates read as legitimately
  empty. Unit test asserts the TEAMS response carries `leagues`. pw:L2 for the UI affordance.

- [x] **DECIDED (operator 2026-07-16): direction A — reclassify TEAMS → per-league.** Read-side; matches the IS writer +
      UAC shard-atom SSOT.
- [x] [BACKEND] P1. ✅ `sports_helpers.py` TEAMS axis `global_trigger_date` → `per_league_trigger_date` (routes TEAMS
      through the per-league branch → `dt_entry["leagues"]` populated → UI league drilldown); updated codex
      `sports-data-source-coverage-matrix.md` TEAMS row to per-league × trigger-date; updated the 3 tests that pinned
      the old global axis + added `test_teams_per_league_axis.py` asserting the TEAMS response carries a populated
      `per_league` map. — deployment-api@fb0eec8 + Evidence: `quality-gates.sh --no-fix` green (4539 passed);
      `test_teams_per_league_axis.py` + `TestTriggerDateDenominator::test_teams_*` green.
- [x] [BACKEND] P1. ✅ Verified: the `per_league_trigger_date` branch uses `sports_trigger_dates_for_league` (season
      boundaries = season-start + transfer windows) per league — one TEAMS snapshot per season boundary. Off-season /
      non-trigger dates read as legitimately empty (honest-absence): the P8 test asserts a league with expected trigger
      dates but no captured rows (LA_LIGA) returns `found_shards=0` (not a gap), and EPL with both boundary dates
      captured returns 2/2. — deployment-api@fb0eec8.
- [x] [UI] P1. ✅ Honest-absence affordance — for genuinely-global sports data_types (LEAGUES=`global_periodic`,
      VENUES=`global_season`) with no per-league map, `DataStatusTab.tsx` now renders an explicit "Global reference
      entity — no per-league breakdown (axis: {axis})" row instead of silently omitting the Leagues section (uses
      `subData.axis`). Extracted the pure predicate `showsGlobalReferenceAffordance(category, hasLeagues,     axis)`
      into `data-status-helpers.ts`. TEAMS (now per-league, P8) renders the real drilldown + never hits this. —
      deployment-ui@43818c9 + Evidence: `data-status-helpers.test.ts` "showsGlobalReferenceAffordance" 3 specs green +
      full UI QG green (tsc/eslint/vitest 90/build). `[UI]` + pw:L2 (Vitest regression spec).
- [x] [UI] P2. ✅ Chose the simpler option (b): a one-line honest UI note. New pure predicate
      `showsFixturesOnlyDrillNote(category, dataTypeName)` (`data-status-helpers.ts`) renders "Per-fixture drill-down
      and downloads are available for FIXTURES only." for every non-FIXTURES sports data_type (STANDINGS, TEAMS,
      LEAGUES, PLAYER_VALUES, …), placed right after the existing per-league/global-reference-affordance rendering in
      `DataStatusTab.tsx` so it doesn't clutter FIXTURES' own view. — deployment-ui@b0525e5 + Evidence:
      `data-status-helpers.test.ts` "showsFixturesOnlyDrillNote" 3 specs green (non-FIXTURES sports → true, FIXTURES →
      false, non-sports categories → false) + full UI QG green (tsc/eslint/vitest 89 tests/build). `[UI]` + pw:L2
      (Vitest regression spec, per this plan's stated acceptance). _(Incident + corrective fix: deployment-ui@12c94be —
      a CONCURRENT agent in this same slot/working-directory had live uncommitted work
      (`FixturesBrowser.tsx`/`.test.tsx` + a `client.ts`/`DataStatusTab.tsx` wiring + a `mock-api.ts` addition) mixed
      into the same files. `git add -p` correctly isolated this commit's staged diff to only the 2 intended hunks, but
      quickmerge's `--files` step does a full-file `git add`, which re-swept the other agent's unstaged
      `FixturesBrowser` import/mount + an unrelated label-wording hunk into the b0525e5 commit — `FixturesBrowser.tsx`
      itself was never committed, so `live-defi-rollout` briefly carried a dangling import. Caught immediately via
      `git ls-tree` + reverted in a same-session forward-fix commit (12c94be, tsc/eslint/full-QG re-verified green); the
      other agent's WIP files are untouched/intact in the working tree — only their 2-line `DataStatusTab.tsx` wiring +
      the label-wording tweak will need re-applying on their end. Flagged to the operator; see also the pre-existing
      `plans/active/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md` for this slot's
      recurring two-agent-collision pattern.)_

---

## P9 — Operator review round 2 (2026-07-16 pm) — data-status deep-dive + reconciliation

> Operator re-reviewed the live (prod-deployed, PRE the P1–P8 fixes) data-status page. Findings validated against REAL
> GCS via a local full-stack run (deployment-api on real GCS + deployment-ui + Playwright). Each tagged
> **fixed-not-shipped** (fixed in LDR, awaiting promote/deploy), **fixed-now** (shipped this round), or **not-fixed**
> (new finding → todo below).

**Reconciliation — instrument_type + data_type per AG (REAL data, coverage-summary breakdowns):**

| AG         | instrument_type (unique-id counts)                                                                                                       | data_type                                                             | Verdict                                                                                                                                                                             |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI       | SPOT_PAIR, PERPETUAL, COMBO, FUTURE, OPTION (canonical) **+ `perpetual` 1.15M, `spot` 502k (LEGACY dupes)** + `__legacy__` 4.85M (blank) | `instruments` (+ `__legacy__` 284)                                    | P4-A canonicalises the DISPLAY (fixed-not-shipped); DATA dupes need the migration (P4 DATA P2).                                                                                     |
| TRADFI     | (pre-fix) `__legacy__` 46.5M (blank — 98% of rows!) + OPTION/COMBO/SPOT_PAIR/EQUITY/FUTURE/ETF/INDEX                                     | `instruments`                                                         | **✅ fixed 2026-07-16**: instruments-service@66258618 — writer was already fixed pre-mission; migration backfilled the 15,017 blank manifest rows (0 `captured` rows remain blank). |
| DEFI       | POOL, LENDING, STAKING, YIELD_BEARING, A_TOKEN, DEBT_TOKEN, PERPETUAL, SPOT_PAIR, LST (canonical) + `__legacy__` 3.85M                   | **TWO: `instrument-catalog` 8.45M + `instruments` 3.03M**             | **not-fixed**: two data_types — root-cause (a `backfill_defi_catalog_data_type_2026_06_21` migration left churn).                                                                   |
| SPORTS     | (source axis) — see below                                                                                                                | —                                                                     | **not-fixed**: invalid `source` values.                                                                                                                                             |
| PREDICTION | PREDICTION_MARKET                                                                                                                        | `prediction_canonical_question_group` + `prediction_market_lifecycle` | Two prediction GRAINS (cqg bundle + per-market lifecycle) — likely legit; confirm.                                                                                                  |

- [x] **Q1 — Symbol search returned nothing (500).** ✅ **fixed-now.** `_load_corpus_from_per_venue_parquets`
      (`data_query_service.py`) resolved the corpus bucket via `build_bucket("instruments", …)` which DROPS the
      `-{env}-` segment → non-existent `instruments-store-{ag}-{project}` (no `-prd-`) → GCS 404 → 500 → blank UI.
      Switched to `resolve_bucket_name(kind="instruments-store", …)` (+ prediction's own kind). —
      deployment-api@2cda602 + Evidence: real-GCS `query='BTC-USDT'` → 10 matches (`BINANCE-FUTURES:PERPETUAL:BTC-USDT`
      …); 2 regression tests.
- [x] [PERF] P1. ✅ _(Q1 follow-up — symbol search now works but takes ~44s per query)_ **Root cause**: the 5-min
      in-process TTL corpus cache (already present, house convention matching `upcoming_fixtures._FIXTURES_CACHE`) only
      protects against re-walking on a WARM cache — every cold miss / TTL-expiry still walked
      `_load_corpus_from_per_venue_parquets` SEQUENTIALLY, one blocking transpacific GCS parquet read per venue
      (`instrument_availability/by_date/day=.../venue=.../instruments.parquet`); DeFi alone registers 63 venues in
      `VENUE_TO_ASSET_GROUP`, so a cold cross-category search (walking cefi/defi/prediction/tradfi/sports) paid tens of
      serial ~1-3s round-trips. **Fix**: parallelised the per-venue reads with a `ThreadPoolExecutor`
      (`_read_all_venue_parquets` + `_read_venue_parquet_rows`, `_VENUE_READ_MAX_WORKERS=16`) — same pattern already
      shipped in `upcoming_fixtures._read_frames_for_window` for per-day fixture reads — collapsing N sequential
      round-trips to ~one round-trip's wall time per batch. 5-min TTL cache left unchanged (already matches house
      convention; the fix targets the cold-miss cost, not cache freshness). Single-walk discipline preserved — no new
      whole-corpus GCS walk, only concurrency on the existing one. — deployment-api@8e1221b + Evidence: 2 new test
      classes in `test_data_query_service.py` — `TestCorpusCacheTTL` (cold miss populates cache / within-TTL call does
      NOT re-read / post-TTL-expiry re-reads, via a fake monotonic clock) and `TestReadAllVenueParquetsConcurrency`
      (wall-clock proof: 6 venues × 0.2s mocked read complete in well under the 1.2s sequential cost, plus merge/dedup +
      empty-input-short-circuits-without-reading coverage); full `quality-gates.sh` green (4576 passed, 0 failed, 16
      skipped; 2 unrelated `test_route_deployments_inventory*` socket-timeout failures on a prior run confirmed as a
      host-load flake — cleared on retry, unrelated to this diff). Real-GCS before/after latency not measured
      (time-boxed under operator urgency) — the concurrency-proof unit test is the verification evidence instead.
- [x] [DATA] P1. ✅ _(Q2 — TRADFI blank instrument_type)_ — instruments-service@66258618 + Evidence below. **Root
      cause**: the shared cefi/tradfi/defi manifest writer
      (`instruments_service/engine/orchestrator/writers.py::_write_venue`) hardcoded `instrument_type=""` on every
      `manifest.record_captured(...)` call regardless of the underlying DataFrame's own (always-populated since this
      repo's initial commit) `instrument_type` column — a pure manifest-STAMPING bug, never a data-capture bug (the
      per-day-per-venue `instruments.parquet` objects always carried the real per-record type). **Writer already fixed
      pre-mission** by two prior commits already live on `live-defi-rollout`/`main`: `b475ae8e` (2026-06-17, single-type
      stamping) superseded by `91fc7bd2` (2026-07-07, `_split_by_instrument_type` — one manifest row per distinct type
      for mixed-type venue-days) — verified by reading `writers.py` at HEAD; no further writer code change was needed.
      **Real scope** (live GCS read 2026-07-16): the manifest index (`_index/availability_index.parquet`,
      `instruments-store-tradfi-prd-central-element-323112`) is 17,083 ROWS — the "46.5M of ~47.1M" figure is the SUM of
      each row's `instrument_count` grouped by blank-vs-typed `instrument_type`, not a manifest row count (15,017/17,083
      rows blank; those rows' `instrument_count` summed to 46,552,151 of 47,189,618 total — 98.6%, matching the plan
      figure almost exactly). Of the 15,017 blank rows, 10,542 were `capture_status=captured` with a real backing GCS
      object; the remaining ~4,475 (82 attempted_failed + 3,883 empty_confirmed + 510 expected_unattempted) captured
      zero instruments and stayed honestly blank. **Migration**:
      `scripts/canonicalize_tradfi_instrument_type_2026_07_16.py` — for each blank captured row, targeted single-object
      read of that exact shard's own `instrument_availability/by_date/day=…/     venue=…/instruments.parquet` (no
      whole-corpus walk), re-deriving `instrument_type` from the object's own column (mirrors the current writer's
      `_split_by_instrument_type` — one manifest row per distinct real type found, splitting mixed-type shards). Dry-run
      → `--apply` → re-verify, on real prod GCS. Evidence: before=15,017/17,083 blank rows (46,552,151/47,189,618
      instrument-count-weighted); after=4,475/28,028 blank rows (28,028 = 17,083 + 10,945 net new rows from multi-type
      shard splits); **0 of the 22,870 `captured` rows remain blank** (capture_status×blank crosstab confirmed
      post-apply); sample CME 2026-07-07 split into FUTURE=347/COMBO=4437/OPTION=69704 rows. Rollback snapshot:
      `gs://instruments-store-tradfi-prd-central-element-323112/_index/snapshots/pre_tradfi_instrument_type_canon_2026_07_16_20260716T143452Z.parquet`.
      `prod/catalog.parquet` checked separately — already 0 blank (1,171,776 rows, built from the same always-typed
      per-record data), no regen needed. MTDS/MDPS/features-service coordination checked (sub-agent investigation): none
      read this manifest's `instrument_type` for their own shard keys — each stamps its own independently — so this was
      safely IS-only. **Adjacent finding (flagged, not fixed — separate from instrument_type)**: 931 of the 10,542
      resolved shards carry a manifest `row_count`/`instrument_count` that is STALE relative to the object's CURRENT
      content (e.g. CME 2026-06-28: manifest said 74,005, the object now holds 2,826 rows — legitimately overwritten by
      a later, narrower capture without a manifest update); this migration re-stamps from the real object (honest)
      rather than preserving the stale count, logged per-shard as `shard count DRIFT` (net magnitude 391,939) — a
      separate, pre-existing manifest-vs-object staleness bug likely not tradfi-specific, worth its own follow-up
      investigation.
- [x] [DATA] P2. ✅ _(Q2 — CeFi legacy lowercase dupes)_ Collapsed `perpetual`→`PERPETUAL` + `spot`→`SPOT_PAIR` in the
      cefi availability index. Root cause: historical writer path predating UAC's strict `InstrumentType` enum field
      (tightened UAC@6f0e0c2e, 2026-04-02) let raw lowercase strings through for the 6 `*-FUTURES` + 7 `*-SPOT`
      Tardis-blend venues; live-verified CLOSED — fresh captures (2026-07-10 → today) are 100% clean/canonical-cased,
      and `prod/catalog.parquet` never carried the lowercase values (424,633 rows, all-uppercase types). Added a
      defensive `_LEGACY_INSTRUMENT_TYPE_ALIASES` normalization guard at the manifest row_key emission site
      (`_split_by_instrument_type`, `writers.py`) as belt-and-suspenders. Cross-service coordination checked:
      MTDS/MDPS/features do NOT read `instrument_type` from this IS manifest (each derives it independently from its own
      captures) — no coordination needed; MTDS separately had its OWN parallel occurrence of this bug class, already
      independently fixed (`market-tick-data-service/scripts/normalize_instrument_type_casing.py` +
      `relabel_bybit_spot_perpetual_itype_2026_07_07.py`) — flagged to operator as informational, not actioned here.
      Migration deduped on the manifest's real composite row-identity
      (`unified_trading_library.manifest_writer._ROW_KEY_COLUMNS`), last-write-wins by `attempted_at` — 3,377
      `(date,venue)` PERPETUAL collisions + 10,003 SPOT_PAIR collisions verified and dropped correctly (math
      cross-checked: 11,582+15,802−3,377=24,007 PERPETUAL; 16,238+14,418−10,003=20,653 SPOT_PAIR). —
      instruments-service@6f87a251 + Evidence: real-GCS `_index/availability_index.parquet` before=93,958 rows
      (perpetual=15,802 [`sum(row_count)`=1,152,860, matching the "~1.15M" figure], spot=14,418
      [`sum(row_count)`=502,714, matching "~502k"]) → after=80,578 rows (perpetual=0, spot=0, PERPETUAL=24,007,
      SPOT_PAIR=20,653); backup
      `gs://instruments-store-cefi-prd-central-element-323112/_index/     availability_index.legacyinstrumenttypefix.20260717-005002.bak.parquet`;
      post-apply re-download verification PASSED (0 residual lowercase rows, row count matches); independently
      re-verified live via the coverage-summary endpoint post-apply (COMBO/FUTURE/OPTION/`__legacy__` counts
      byte-identical pre/post, confirming no out-of-scope rows were touched).
- [x] [DATA] P2. ✅ _(Q2 — DeFi two data_types)_ **DECIDED (operator round-2 2026-07-16): `instruments` is canonical for
      DeFi.** Root cause: the LEGACY `_write_catalogue_record` path
      (`instruments_service/engine/orchestrator/     catalogue.py`) used to stamp `data_type='instrument-catalog'` for
      DeFi rows — that path is DEAD CODE in the current orchestrator (`_write_all_venues` always constructs a live
      `ManifestWriter`, so `_write_venue`'s batched branch is always taken, which ALREADY stamps the canonical
      `data_type='instruments'`, confirmed by reading `writers.py`). Fixed the dead legacy stamp anyway (correctness if
      ever revived) + `scripts/defi_cumulative_drawdown_guard_2026_06_25.py`'s own filter —
      instruments-service@4d63822d. **Cross-repo finding**: `data_type='instrument-catalog'` is a load-bearing UAC
      crosscutting preflight-DAG value (`instruments_preflight_dag.py`'s DeFi `defi_market_data` entry, consumed by
      MTDS's `assert_defi_catalog_fresh` to gate live DeFi collects) — updated `upstream_entity_type` to
      `'instruments'` + the 3 DeFi-scoped test assertions (CeFi/TradFi DAG entries left untouched, out of
      scope/unverified) — unified-api-contracts@90b8b986. Migrated the historical rows on real infra:
      `instruments-service/scripts/     canonicalize_defi_data_type_instrument_catalog_2026_07_16.py` — dry-run found a
      safety-gate bug in my own first draft (naive `captured_before - dropped_count` formula assumed every dropped
      duplicate was a captured row; fixed to track `captured_dropped` explicitly + prioritize captured status over
      recency when picking a collision-group winner) before applying. Applied: 215,501 → 175,080 rows; 126,443 legacy
      rows migrated, 40,421 duplicate collisions resolved (39,286 were genuine duplicate captures, 1,135 non-captured),
      captured-row-count invariant held exactly (171,492 → 132,206, delta = captured_dropped). Post-run verify: 0
      residual `instrument-catalog` rows. `catalog.parquet` doesn't reference this data_type value (verified — no regen
      needed). No MTDS/MDPS shard-atom coordination needed beyond the preflight-DAG constant (neither reads `data_type`
      as their own shard key from this IS manifest column).
- [x] [DATA] P1. ✅ _(Q3 — SPORTS "invalid" `source` values)_ **NOT a bug — root-caused, no fix needed.**
      `mdps_odds_horizon_bucket` and `instruments_service` are both REGISTERED non-vendor `source` identifiers in UAC's
      crosscutting `SOURCE_PRIORITY`/`PipelineMode` registries (`_source_priority_data.py:77` +
      `("reference","instruments"):["instruments_service"]`), used identically across every asset group — deliberate
      2026-06-07 sports-manifest routing exception (MDPS's own odds-horizon-bucket product is intentionally written into
      IS's canonical sports bucket) + the already-shipped 2026-07-13 orphan backfill (`instruments-service` migration
      script, `market-data-processing-service@6907257`). Live GCS read of the canonical `instruments-store-sports-prd`
      index (2026-07-16) shows `mdps_odds_horizon_bucket`=356,131 rows (350,809 of them the real `odds_horizon_bucket`
      data_type — its actual purpose) and `instruments_service`=100,472 rows (100% genuinely self-referential/global
      reference data_types: LEAGUES/VENUES/TRANSFERMARKT_LEAGUES/ SFI_LEAGUES/SFI_STANDINGS — the same "global reference
      entity" pattern P8 already fixed). **The operator's cited counts (8.1M/3.7M) do not match any real bucket**
      (canonical=356K/100K, orphan=124K/0) — off by ~23-37x, almost certainly the same stale-cached-rollup-blob class of
      bug this plan's P7 already root-caused. Only real (small, optional, P3) finding: venue-casing dupes
      (`MDPS_ODDS_HORIZON_BUCKET` vs `mdps_odds_horizon_bucket`, `ODDS_API` vs `odds_api`, etc.) — not a correctness
      issue, just breakdown-UI cardinality noise. Full writeup + evidence: issue doc
      `plans/active/issues/sports_source_mdps_instruments_service_not_leakage_2026_07_16.md`. — no code shipped,
      root-cause-only per operator's explicit "root-cause BEFORE any correction" instruction.
- [x] [UI] P3. ✅ _(Q4 — "unique instruments" label)_ The
      `2,970,327 unique instruments (catalogue-deduplicated, all asset     groups)` count is CORRECT (verified: Σ per-AG
      = total exactly; dominated by expired OPTION/COMBO strikes — cefi 263k+138k, tradfi 1.17M — and resolved
      prediction markets 1.34M). Relabeled to "unique instruments — all-time incl. expired/delisted/resolved
      (catalogue-deduplicated, all asset groups)"; the latest-day figure was already rendered beside it (a prior P9
      backend fix), relabeled to "N active on latest day" (bold + tooltip) so the two numbers read as
      all-time-vs-live-universe rather than one being mistaken for the other. — deployment-ui@33a37af + Evidence: full
      UI QG green (`tsc`/`eslint`/`vitest` 90 tests/build, 74.91% coverage). `[UI]` — pw:L2 deferred to the plan's final
      local full-stack Playwright validation pass (no dedicated component test scaffold exists for this card — text-only
      JSX change, verified live instead of via a new Vitest spec).
- [x] [UI] P2. _(operator request — fixtures browser)_ Added a fixtures browser to the IS data-status summary: renders
      catalogue fixtures grouped by **league → day** with collapsible `<details>` dropdowns (same accordion primitive
      `UpcomingFixtures`/`HierarchicalShardDrilldown` already use). Backend:
      `deployment_api/services/fixtures_browser.py` (`list_fixtures_by_league_and_day`) reuses `upcoming_fixtures.py`'s
      day-window threaded reader (`_read_frames_for_window`/`_row_to_fixture`/`_sports_bucket`) — same
      legacy-singleton/`fixtures_schedule`-split fallback + shard-level failure isolation — over a BOUNDED window
      (`days_back`/`days_forward`, default 7/30, capped 60 each; single-walk discipline: no `list_blobs` over the whole
      `sports_reference/` prefix). Considered the sports instrument catalogue
      (`build_sports_fixture_team_player_catalogue`) as a full-history alternative but rejected it — that catalogue is
      itself windowed (`SPORTS_FTP_WINDOW_DAYS`) AND drops `kickoff_utc`/`status`, which the UI needs. New route
      `GET /api/fixtures/browse` (`deployment_api/routes/fixtures_browse.py`, mock-mode-aware, mirrors
      `routes/fixtures.py`); registered in `main.py` beside the existing fixtures router; `fixtures_browser` real-module
      registered in `tests/unit/conftest.py`'s `_ensure_services_mocked()` allowlist (same pattern
      `catalogue_lifecycle`/`prediction_catalogue` use). Frontend: `FixturesBrowser.tsx` (nested league→day `<details>`
      accordion) mounted IS-only in `DataStatusTab.tsx` beside `<UpcomingFixtures/>`; `fetchFixturesBrowse` +
      `FixtureRow`/`FixturesByLeagueAndDay` types in `client.ts`; mock handler in `mock-api.ts`. —
      deployment-api@d77c1264fe00d143e1d65995b0b5a0b45c27890b + Evidence: `quality-gates.sh --no-fix` full green (0
      failed, 4576 passed, 16 skipped, coverage 79.83%; `tests/unit/test_fixtures_browser.py` — grouping shape,
      empty-day handling, league filter, shard-isolated-failure, window-clamping, all pass).
      deployment-ui@966a69e224e69d47cf88a675d24d7d42be0e69ab + Evidence: full UI QG green (`tsc`/`eslint`/`vitest` 91
      test files, build passed); `FixturesBrowser.test.tsx` (5 tests: league/day grouping render, expand/collapse
      interaction, empty state, refresh refetch, league-filter refetch) all pass. `[UI]` + pw:L2 deferred to the plan's
      final local full-stack Playwright validation pass (mirrors the P9 Q4 precedent above — no dedicated Playwright
      spec added this tick, Vitest is the cited evidence).

### P9 — cross-agent verification (2026-07-16 pm, other agents' P3/P6 work)

P3 (prediction browser: deployment-api@9238983 + deployment-ui@3bdb4e4 + uac@72fd959) and P6 phase-1 (catalogue
explorer: deployment-api@abcce0b + @1e3c7b4) are **committed, on LDR, CI-green (`quality-gates-v2` success), plan todos
flipped with evidence, and code is real** (not stubs) — the shipping process was followed correctly. TWO gaps found on a
local real-GCS run (worth confirming — same "CI-green-with-mocks but slow/empty on real data" class as the Q1 symbol
search):

- [x] ~~[PERF] P2. (P3/P6 endpoints — real-data verification)~~ ✅ **RE-VERIFIED 2026-07-17** — the hang I flagged was
      root-caused + fixed by the overnight side-discovered fixes (UAC `OTHER_BUCKET_MEMBER_ADDED` INFO-log flood →
      `uac@d4523602`; `coverage.py` `pd.NA` crash → `deployment-api@e754a60`; symbol-search parallelized → `@8e1221b`).
      Fresh local run (deployment-api@d786743): `/prediction-catalogue?category=crypto` returns **correct data**
      (total=214,532 crypto + full category_counts, real KALSHI/POLYMARKET rows) — but ~39s (reads the ~1.3M-row pred
      catalog; a caching/pagination perf follow-up remains, tracked as the new PERF todo below).
- [x] ✅ **[BACKEND] P1 — FIXED 2026-07-17.** `GET /data-status/catalogue` returned `total_count=0` for cefi/defi/tradfi
      on real data (prediction/sports worked). Root cause: `_load_catalogue_frame` (`routes/data_status/_catalogue.py`)
      read `_index/availability_index.parquet` and keyed on `instrument_id`, but the cefi/defi/tradfi availability index
      is VENUE-level (shard atom = venue; NO per-instrument rows — real-GCS confirmed: cefi `_index`=80,615 rows, ZERO
      non-blank `instrument_id`). Fix: for cefi/defi/tradfi read the per-AG identity catalogue `prod/catalog.parquet`
      (the SAME file `catalogue_lifecycle`/`read_unique_instrument_count` already read) via `_read_identity_catalogue` —
      ONE bounded GCS GET (single-walk preserved); `is_mvp` from the catalogue's own precomputed `mvp` column;
      `capture_status`/`error_reason`/`attempted_at` honestly default (identity catalogue carries no manifest-only
      per-shard fields). prediction/sports keep the per-entity `_index` path unchanged. — deployment-api@62cc10f +
      Evidence: real-GCS `_build_catalogue_rows` → cefi=424,465 (e.g. `ASTER:PERP:IPUSDT`), defi=11,770 (Uniswap-V3
      pools), tradfi=1,173,803 (CBOE COMBO); QG green (106s); +8 `TestIdentityCatalogueSource` tests (parametrized
      cefi/defi/tradfi regression, asset-group-scoped bucket resolution, mvp-column-not-`is_mvp`, search, venue-narrow,
      degrade-to-empty-not-500, CSV parity, raw-parquet schema-aware projection). Shipped via dirty-deps carve-out
      (deployment-service `terraform.tfvars` foreign-live-dirty; strict-quickmerge WARN-only).
- [x] [PERF] P3. ✅ `/data-status/prediction-catalogue` — **profiled on real GCS BEFORE optimising, which corrected this
      todo's premise.** Measured cold cost is **~173s, not ~39s**, and it splits ~50/50 into two stages that are BOTH
      **filter- and page-independent**: the GCS GET of the 184.5 MB pred `catalog.parquet` (**84.5s**) + the ~2.7M-row
      classification pass in `_build_rows` (**86.0s**); parquet parse is a rounding error (1.8s) and facets 0.35s. So
      the todo's suggested "pagination/projected read" **would have fixed nothing** — you cannot skip an 84s
      whole-object download by asking for 50 rows, and the facet counts need the whole corpus by construction. **The
      actual bug was the cache key**: it included `limit`/`offset`, so every "Next page" click re-paid the entire ~173s.
      Fixed by re-keying `_CATALOGUE_CACHE` on the FILTER SET only and retaining a **bounded 5,000-row window** (+ the
      true `total` + facets) per set. **Why bounded and not a corpus/frame cache** (the tempting "obvious" fix): an
      unfiltered result is ~2.7M rows and the identity frames measure **122–312 MB deep** — caching those would
      re-create exactly the OOM class this plan's own P1 root-caused on the honest-coverage writer. 5,000 rows = 100
      pages at the default 50/page; a request past the window logs and falls back to a correct full rebuild rather than
      silently serving a truncated list. Also pushed the `venue` narrow into the FRAME before classification (pure
      optimisation — `venue` is a raw column needing no classification, and the caller applied the identical narrow to
      the built rows immediately after). — deployment-api@0e39a53 + Evidence (**real GCS, shipped code**):
      `category=crypto` page 1 = 157.18s (total=214,532) → **page 2 = 0.00s**, page 21 = 0.00s, and page1 rows ≠ page2
      rows (not the cache echoing page 1); `venue=KALSHI` cold **27.88s vs 157.18s unfiltered (5.6x)**, all rows
      `venues={'KALSHI'}`; `category=sports` correctly rebuilds (157.48s) returning `categories={'sports'}` — proving a
      different filter set is NOT served from the crypto entry. Unit: `test_prediction_catalogue.py` 9 passed incl. new
      `TestPagingDoesNotRePayTheCorpusCost` ×5 (second page issues NO second read; paged rows == unpaged ordering; **a
      different filter set is not served from another set's cache** — the load-bearing risk of dropping limit/offset
      from the key; `total` is the full count not the window length; venue-pushdown results identical to filtering after
      build). **Known residual (honest, not deferred silently):** the FIRST request for a new filter set still costs
      ~157s. That is inherent to reading a 184MB / 2.7M-row corpus per filter set; removing it needs a server-side
      projection/index rather than a cache — which is precisely the P6 phase-2 "true-catalogue source" item below, where
      it belongs.
- [x] [PERF] P3. ✅ _(P6-catalogue follow-up, found 2026-07-17)_ `/data-status/catalogue` — the todo's diagnosis was
      **confirmed** by profiling here (unlike the prediction one above): download+parse for tradfi is only ~3.3s, so the
      cost really was building **every** row-dict via `df.iterrows()` before slicing the page. Fixed by splitting the
      build into `_prepare_catalogue_frame` (vectorised narrow + `is_mvp` tag + order — no dicts) and `_rows_from_frame`
      (materialises dicts from whatever slice it is handed), so the JSON route (`_build_catalogue_page`) builds only the
      requested page while `total_count` stays exact via a frame `len()`. The CSV twin keeps the full-list path, and
      both now share one prepare step so they are **structurally** unable to disagree on rows/order. `is_mvp` is
      vectorised for the identity catalogues (reads their precomputed `mvp` column — this is what takes tradfi's 1.17M
      rows off the per-row path); manifest-backed AGs (prediction/sports) keep the per-row predicate, i.e. no regression
      there. **Operation order preserved exactly** (mvp_only → search-in-frame-order → cap at
      `MAX_CATALOGUE_SEARCH_RESULTS` → sort): the cap lands BEFORE the sort, so reordering would silently change which
      rows a capped search returns. Deliberately did **not** add the suggested TTL cache: measured the frames at 311.8
      MB (tradfi) / 121.7 MB (cefi) deep, and the residual cold time is the transpacific GET (variable), not compute —
      caching those frames buys little and risks the P1 OOM class. — deployment-api@0e39a53 + Evidence (**real GCS**):
      tradfi **61.32s → 14.88s (4.1x)** with `total_count=1,173,803`; cefi **18.85s → 2.90s (6.5x)**; **page
      byte-identical to the old full-build `full[:50]`** for both, plus verified equivalence for `offset=100 limit=20`
      under `mvp_only=True` (`page == full[100:120]`) and `search=BTC` (`page == full[:10]`, total 500 == 500). All **16
      pre-existing `test_route_data_status_catalogue.py` specs pass UNCHANGED** (they pin CSV/JSON parity — the
      refactor's real guard); 25 passed across both perf files. basedpyright A/B'd vs HEAD: I introduced 1 new error (an
      untyped `.apply` lambda) and **fixed it properly with a typed inner function rather than suppressing it** — back
      to 4 = HEAD's count; ruff RUF046 likewise fixed, not ignored.
- [x] ~~[UI] P2. (P6 phase-1 UI — NOT done)~~ ✅ RESOLVED — the P6 phase-1 UI (InstrumentsModalStandard "MVP only"
      toggle + per-row badge + CSV threading + Catalogue Explorer panel) DID land after this note was written — see the
      flipped P6 `[UI] P2 _(phase 1)_` checkbox above (`DataStatusDrilldown.tsx`). This note was stale.

---

## P10 — Sports fixtures browser: filter by date / league / team (operator round 3, 2026-07-17)

> Operator: _"for catalogue sports should have all the fixtures broken down by searching by date, league and/or team for
> filtering"_. The P9 fixtures browser shipped league→day grouping with a `league_id` filter over a **today-relative**
> window only — so team search did not exist and no historical date was addressable (`days_back` caps at 60).

- [x] ✅ **[BACKEND] P2 — DONE 2026-07-17.** `list_fixtures_by_league_and_day` / `GET /fixtures/browse` gained the two
      missing axes. **`team=`** — case-insensitive substring across home/away team **name AND id**, matching whichever
      side the team played; applied POST-parse so it keys on `_row_to_fixture`'s normalized fields rather than the raw
      split-shard variants (`af_home_name` etc.). **`start_date`/`end_date=`** — an ABSOLUTE `YYYY-MM-DD` window that
      can address **any** range in history (the relative window could only ever reach 60 days from today); a missing
      side is filled from the relative default, a reversed range is swapped, and the span is capped at
      `_MAX_WINDOW_SPAN_DAYS` (120) so the bounded per-day read — and **single-walk discipline** — is unchanged (no new
      whole-corpus walk, only which days are read). An unparseable date degrades to the relative window rather than
      500ing. **Cache-key fix**: `_BROWSE_CACHE` now keys on the RESOLVED window + every filter — previously a team
      narrow would have been served the cached UNFILTERED rows. — deployment-api@5815582 + Evidence: QG green (120s);
      **real-GCS** — baseline ±3d = 14 leagues/123 fixtures, `team='atlanta'` → 3/3 genuinely match, `league_id='129'` →
      only 129 returned, absolute `2026-05-01..03` → 354 fixtures across exactly those 3 days (a window the old UI could
      not reach); +11 tests (`TestTeamFilter` home/away/id/blank-noop/cache-isolation/combined, `TestAbsoluteDateWindow`
      jump/fill-either-side/reversed/span-cap/unparseable-fallback/cache-isolation).
- [x] ✅ **[UI] P2 — DONE 2026-07-17.** `FixturesBrowser.tsx` filter bar reworked: the `Days back`/`Days forward` number
      inputs are REPLACED by real **From date / To date** pickers (prefilled today-7 → today+30, so the default view is
      unchanged but any range is now selectable), plus a new **Team** input beside **League id**. Text filters run
      through the house `useDebounce` (300ms) — each distinct value is a fresh windowed GCS read server-side, so a
      per-keystroke refetch would be genuinely expensive. The window note now states the actual date range + active
      narrows, and warns when a chosen range exceeds the server's 120-day span cap (rather than silently
      under-reporting). `mock-api.ts`'s `/fixtures/browse` handler now HONOURS the date/league/team narrows — an
      unfiltered mock made the new filter bar look broken in local mock mode. — deployment-ui@8cdae0b + Evidence: full
      UI QG green (tsc/eslint/vitest/build); `FixturesBrowser.test.tsx` 10 tests pass (absolute-default-window shape,
      league refetch, team refetch, historical-range refetch, combined date+league+team query, span-cap warning). `[UI]`
      — pw:L2 deferred to the plan's final local full-stack Playwright pass (mirrors the P9 Q4 / fixtures-browser
      precedent; Vitest + the real-GCS backend proof above are the cited evidence).

> **Scope note (honest bound):** "all the fixtures" is served within a **bounded window** — the reader walks explicit
> per-day paths, so an unwindowed all-history listing would be a whole-corpus GCS walk (review-blocking, single-walk
> discipline). The absolute date range makes **any** date reachable (which is what the ask needs); it just reads ≤120
> days at a time rather than all of history at once.

---

## Operator decisions — RESOLVED (2026-07-16)

1. **P8 — TEAMS axis**: ✅ direction A (reclassify per-league). Seasonal change is the trigger-date axis under each
   league.
2. **P4 — SPOT_ASSET**: ✅ populate for every base+quote token leg across DeFi + spot-CeFi (catalogue address columns →
   backfill → live discovery-time emission → CeFi symbol→chain→address mapping). Summary labels = canonical with raw on
   hover.
3. **P3 — prediction label**: ✅ slug for v1 (category from `canonical_question_group`), real title column as a
   follow-up.
4. **P6 — catalogue explorer**: ✅ both, phased (availability-derived now, true-catalogue projection follow-up).

### P9 round-2 decisions (operator 2026-07-16 pm)

5. **DeFi data_type**: ✅ `instruments` is canonical → migrate `instrument-catalog` → `instruments`.
6. **CeFi instrument_type**: ✅ migrate the non-canonical lowercase `perpetual`→`PERPETUAL`, `spot`→`SPOT_PAIR`.
7. **TradFi instrument_type**: ✅ migrate/stamp the 46.5M blank (`__legacy__`) rows to their canonical InstrumentType.
8. **Prediction data_types**: ✅ KEEP both grains (`prediction_canonical_question_group` +
   `prediction_market_lifecycle`) — no change.
9. **Sports invalid sources**: ✅ root-cause WHY `mdps_odds_horizon_bucket` + `instruments_service` appear as IS sports
   `source` values (operator: "is it a sign of deeper issues?") BEFORE any correction — diagnose the cross-service
   leakage path first, then fix at the writer/consolidator.

> **Migration HARD RULES (all three data migrations 5–7):** `instrument_type` + `data_type` are SHARD axes for
> MTDS/MDPS/features (NOT for instruments-service, where they are DISPLAY axes) — a naive IS-only rewrite of these
> values breaks cross-service shard-atom identity. Each migration must: (a) fix the WRITER first so new rows are
> canonical; (b) an IDEMPOTENT one-off migration script (pattern: `instruments-service/scripts/canonicalize_*_2026_*.py`
>
> - `backfill_defi_catalog_data_type_2026_06_21.py`) run on REAL infra with manifest-verified row counts; (c) preserve /
>   co-migrate shard-atom identity across MTDS/MDPS/features (confirm those services' shards for the same instruments,
>   or coordinate); (d) regen the affected catalogue + availability index. Run behind a pre-migration drain if any live
>   writer touches the same index. These are heavy real-infra ops — a fresh-context agent owns them (handoff prompt in
>   the operator's hands).

## Full audit artefacts

Findings digest + per-agent verdicts: workflow `wf_872e8051-00a` (findings all `CONFIRMED-WITH-CORRECTIONS`; P7 agent
failed the structured-output cap, so P7's exact chain-derivation line is TRACE-FIRST above). This plan is the durable
worklist; the transcript is ephemeral.
