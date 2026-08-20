---
doc_type: plan
title: Repo scripts/ governance — ruff-lint pass + deprecate/delete audit + strict-quickmerge carve scope (D16)
summary:
  Govern the scripts/ directories across repos — add ruff-lint pass, audit for deprecation/deletion, and define the
  strict-quickmerge carve scope for D16.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-service,
    e2e-testing,
    features-service,
    instruments-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [scripts, governance, ruff, lint, audit, deprecation, quickmerge, ci-cd, D16]
related: []
created: 2026-06-18
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
last_updated: 2026-08-20
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    operator decision 2026-06-18 (CI/CD drift audit D16 follow-up),
    plans/audit/results/cicd_pipeline_vs_plans_drift_audit_2026_06_17.md § D16,
  ]
assigned_role: infra
drift_direction: correct-codex
context_scope:
  [
    /codex/06-coding-standards/script-homes.md,
    /codex/06-coding-standards/quality-gates.md,
    scripts/quality-gates-base/base-service.sh,
    /plans/audit/results/repo_scripts_characterization_2026_06_18.md,
  ]
---

# Repo scripts/ governance — lint + audit + the strict-quickmerge carve scope

## Decisions (operator-ratified 2026-06-18)

1. **`scripts/` stays OUT of typecheck (basedpyright) + coverage — by design.** Repo `scripts/` are one-off/throwaway
   (run a handful of times, then deleted). Gating them with the typechecker/coverage only manufactures **refactor
   tech-debt** for code meant to be removed (every refactor would have to keep soon-to-be-deleted scripts type-clean).
   Recurring/important logic must become a **CLI subcommand** (which IS gated as part of `$SOURCE_DIR`), never a
   permanent `scripts/` file. Confirms the existing Script-Homes contract
   (`/codex/06-coding-standards/script-homes.md`).
2. **ADD a ruff-lint pass on `scripts/`** (cheap, autofixable rot-catch — syntax / imports / obvious bugs) — **no
   basedpyright** (too heavy + high-noise for throwaway code). Exact ruff scope (which rules, ratchet vs hard) is
   surfaced by the Phase-1 audit.
3. **`tests/` stays AS-IS** — essential; ruff-linted + pytest-run on every QG (local + CI + staging); deliberately
   **no** basedpyright (noise > help on test code); naturally no coverage. No change.
4. **D16 — the strict-quickmerge `scripts/` carve scope (PM-only vs all-repos) is PENDING this audit.** Verified: the
   carve only affects **provenance** (the `Quickmerge:` trailer + dep-gate pre-flight), NOT content-gating — `scripts/`
   is QG-unchecked either way. Decide after the audit shows what service-repo `scripts/` actually contain.
5. **Every script declares a lifecycle marker (operator 2026-06-18)** — a 3-line greppable comment header (works for
   `.sh` + `.py`): `Epic:` (owning epic), `Lifecycle:` (`permanent | campaign | oneoff`), `Delete-when:` (required +
   present on ALL scripts, `NA` for `permanent` — was: "completion condition, required for `campaign`/`oneoff`",
   implying `permanent` scripts omit the field; corrected 2026-07-14, verify-rerun-2 finding 97: the operator correction
   2026-06-22 (see Phase 0 below) made `Delete-when` mandatory-and-present on every script so the fleet stays greppable
   via `grep -rL '^# Delete-when:'` — Decision 5 here was never updated to match). Not every script is throwaway —
   `setup.sh` is permanent lifecycle infra; a GCS-migration script is a weeks-long **campaign**. The marker lets the
   audit distinguish them mechanically instead of re-deriving each time, and makes "delete after use" self-enforcing.
   **`Epic:` (not a single plan)** because a script spans multiple plans (the GCS cutover touches MTDS / instruments /
   deployment plans at once); epics are stable
   - multi-plan + validate-able vs the registry like `assigned_vm`. **Epics are EVERLASTING**, so `Epic:` is OWNERSHIP,
     not the delete trigger — `Delete-when:` carries the actual completion signal. **NO runtime last-run tracking
     (operator 2026-06-18): no `log_script_run`, no run-ledger, no auto-updated header field** — an auto usage timestamp
     is commit-noise (unnecessary commits/PRs just to _run_ a script) and redundant, since the delete decision is gated
     on the **`Delete-when` condition**, never a run-count. Only manual staleness _hint_ if ever in doubt:
     `git log -1 --format=%cs -- <script>` (last-EDITED). Full convention in Phase 0.
6. **Rollout sequence + deletes-DEFERRED (operator 2026-06-18).** Immediate priority is the **frontmatter ROLLOUT, NOT
   deletion** — stamp the lifecycle marker on every script, then prune later by `Delete-when`. Sequence: \*\*(1) PM docs
   - frontmatter** (the convention in `script-homes.md`/CLAUDE.md ✅ + PM's own scripts), **(2) every other repo's
     frontmatter** (orchestrator-dispatched per `scripts_lifecycle_marker_rollout_2026_06_18.md`), **(3) prune by
     `Delete-when`** (epic-owner-confirmed, orphan-sweep = 0). **NO run-logger / NO runtime last-run tracking**
     (operator 2026-06-18: dropped — an auto usage ledger is commit-noise for ~zero decision value; the `Delete-when`
     condition is the trigger, not a run-count). **No deletions until each `Delete-when` is met\*\* — Phase-1's
     DELETE/DEPRECATE/PROMOTE execution todos stay PARKED. Collision is a non-issue: a top-of-file marker doesn't
     conflict with body edits.

## Verified facts (`base-service.sh` — the same script CI + staging run)

| Path           | ruff | basedpyright | pytest | coverage |
| -------------- | ---- | ------------ | ------ | -------- |
| `$SOURCE_DIR/` | ✅   | ✅ (L746)    | —      | ✅       |
| `tests/`       | ✅   | ❌           | ✅     | —        |
| `scripts/`     | ❌   | ❌           | ❌     | ❌       |

A `scripts/*.py` is checked **nowhere** (local or staging — same script both places). Accepted as intentional (decision
1); partially closed by the ruff-lint pass (decision 2). `tests/` ARE caught in staging (ruff + pytest), so a carved-out
`tests/*.py` is genuinely gated — the carve is safe for tests.

## Inventory (2026-06-18, `find scripts/ -name '*.py'` fleet-wide)

**~647 `.py` across 22 repos; ~131 match a stale-name heuristic**
(`migrat|backfill|one_off|reconcile|dedup|cleanup|fix_| repair|rename|move_|delete_|purge|sweep` — a starting list, NOT
a verdict). Heaviest:

| Repo                     | .py | stale-named                          |
| ------------------------ | --- | ------------------------------------ |
| instruments-service      | 111 | **65** ← biggest cleanup target      |
| unified-trading-pm       | 248 | 18 (mostly LEGIT tooling — see note) |
| market-tick-data-service | 62  | 29                                   |
| deployment-service       | 53  | 5                                    |
| e2e-testing              | 48  | 2                                    |
| features-service         | 31  | 2                                    |
| unified-api-contracts    | 28  | 0                                    |
| (others ≤16 each)        | …   | …                                    |

> **PM is special — do NOT lump it with service repos.** Its 248 scripts are the workspace **tooling host** (the CICD
> machinery, propagation templates, plan-hygiene, agents) — genuine, recurring, chicken-and-egg infrastructure, NOT
> one-off throwaway. This is exactly why the strict-quickmerge `scripts/` carve exists for PM. The throwaway-one-off
> model applies to **service-repo** scripts (instruments-service / MTDS are the big targets).

## Phase 0 — define + roll out the lifecycle marker convention [P2] (precedes the audit)

- [x] ✅ [DESIGN] P2. **DONE 2026-06-18** — codified the 3-line lifecycle marker convention in
      `/codex/06-coding-standards/script-homes.md` § "Lifecycle marker" + a CLAUDE.md § "Script Homes" one-liner (marker
      format, the `permanent|campaign|oneoff` taxonomy, `Epic`-is-ownership / `Delete-when`-is-trigger, the
      `Delete-when`-driven pruning model (no runtime tracking), ruff-yes/basedpyright-no gating). Codify the 3-line
      script lifecycle marker (a comment header — works for `.sh` AND `.py`, so it's not Python-docstring-only):

  ```
  # Epic: <epic-slug>                       # owning epic — validated vs plans/epics/ registry (required, ALL scripts)
  # Lifecycle: permanent|campaign|oneoff    # required, ALL
  # Delete-when: <concrete completion condition> | NA   # REQUIRED + PRESENT on ALL scripts; NA for permanent
  ```

  (was: "`# Delete-when: <concrete completion condition> # required for campaign/oneoff; permanent omits it`" —
  corrected 2026-07-12, doc-reconciliation finding 71, §A2 B-queue ruling: operator correction 2026-06-22 made
  `Delete-when` mandatory-and-present on every script, `NA` for `permanent`, so the fleet stays greppable via
  `grep -rL '^# Delete-when:'`; see `/codex/06-coding-standards/script-homes.md` § "Lifecycle marker" (the enforced
  SSOT) and `plans/archive/2026_07/scripts_lifecycle_marker_rollout_2026_06_18.md`.)

  Closed `Lifecycle` set mirrors the VM `lifecycle_class` spirit: **`permanent`** ≈ LONG_LIVED (`setup.sh`, dev tooling;
  template-managed scripts like `setup.sh`/`quality-gates.sh`/`quickmerge.sh` are auto-permanent — PM-sourced); whereas
  **`campaign`** ≈ a temporary-state-with-named-successor (the GCS bucket migration — lives weeks, deleted at
  completion); **`oneoff`** ≈ EPHEMERAL (run-once; `Delete-when:` = "after prod-run + orphan-sweep=0"). `Epic:` is
  OWNERSHIP (multi-plan; epics everlasting → NOT the delete trigger); `Delete-when:` carries the completion signal.
  Codify in `/codex/06-coding-standards/script-homes.md`. Composes with: VM `lifecycle_class`, the Runbook
  Execution-Owner SSOT (`owner/cadence/verifier/last_executed`), and "Temporary states + their canonical follow-up
  plans" — same lifecycle-declaration idea, now for scripts.

- [ ] [SCRIPT] P2. Wire enforcement (ratcheted warn→block, like the 5.94/5.95 checks): a script-homes sweep / QG check
      that (a) every `scripts/` file declares `Epic:` + `Lifecycle:` + `Delete-when:` — **all three REQUIRED and PRESENT
      on ALL scripts, `NA` for `permanent`** (was: "+ `Delete-when:` for campaign/oneoff", which implied `permanent`
      omits it — corrected 2026-07-26, `/plan-reconcile` infra shard: this line was left behind by the 2026-07-14
      verify-rerun-2 finding-97 correction that fixed Decision 5 and the Phase-0 code block above but not this todo; the
      codex SSOT `/codex/06-coding-standards/script-homes.md:97` reads
      "`# Delete-when: <condition> | NA # REQUIRED + PRESENT on ALL scripts`" and `:100` "**All 3 fields are MANDATORY
      and PRESENT on every script** (operator 2026-06-22)", and `:154-155` defines the enforced check as failing on a
      missing `# Delete-when:` OR a non-`permanent` using `Delete-when: NA`); (b) `Epic:` ∈ the epic registry (reuse the
      `assigned_vm`-vs-registry `regen_vm_registry.py --check` pattern); (c) surfaces every `campaign`/`oneoff` whose
      `Delete-when` looks satisfied OR whose `git` last-modified is stale (>N months) → flagged for the **epic owner**
      to confirm + delete. Repo: unified-trading-pm.

- [x] ✅ [DESIGN] P2. **DECIDED 2026-06-18 — NO runtime last-run tracking.** Dropped the run-ledger / `log_script_run`
      idea entirely (operator): an auto-updated usage timestamp is commit-noise (unnecessary commits/PRs just to _run_ a
      script) and redundant — the delete decision is gated on the **`Delete-when` condition**, never a run-count, so a
      `permanent` script's run-count is irrelevant and a `campaign`/`oneoff` deletes when its condition holds. Only
      manual staleness _hint_ if ever in doubt: `git log -1 --format=%cs -- <script>` (last-EDITED). No ledger, no
      header field, nothing to maintain.

## Phase 1 — audit each repo's scripts/ (characterize + STAMP the marker) [P2]

- [x] ✅ [AUDIT] P2. **DONE 2026-06-18 — read-only characterization of all 21 service repos' `scripts/` (~820 scripts,
      `.py`+`.sh`; PM excluded).** 6 Opus sub-agents, one per repo-cluster; every script classified
      (KEEP-PERMANENT/KEEP-ONEOFF/DELETE/DEPRECATE/PROMOTE-TO-CLI) + lifecycle + git-date + red-flag grep. Results:
      **`plans/audit/results/repo_scripts_characterization_2026_06_18.md`**. Tally: ~620 keep-permanent, ~65 keep-oneoff
      (active campaign), ~127 DELETE-candidates (heavily campaign-gated), ~75 DEPRECATE (cloud-discipline rot), ~8
      PROMOTE-TO-CLI. (Stamping the lifecycle marker on each script is deferred to the delete/Phase-0 pass — the
      characterization already assigns each one, so stamping is mechanical, but it pairs with the delete touch to avoid
      churning ~820 files read-only.)
- [ ] [AUDIT] P2. **Delete EXECUTION — GATED + REVIEWED (do NOT mass-`git rm`).** Per the results doc Finding 1: the big
      DELETE cohort (instruments-service 64 / MTDS 22) is **campaign-gated** — the 2026-06 manifest-canonicalisation
      campaign is ACTIVE, so delete a repo's dated one-offs for an asset_group **only after that AG's
      `*_manifest_canonicalisation_2026_06_01.md` plan archives** + GCS-orphan-sweep=0. **Start with the
      immediately-safe ~40** (UI 2026-03 `.tsx.bak` splitters/codemods; done deployment-service bucket migrations; the 3
      dead checkers — UAC `check_schema_organization`, MTDS QG stale SSOT pointer, deployment-service
      `aggregate_instruments`. **Struck 2026-08-14 — live CI tooling, NOT dead**: UTL `check-ruff-versions.sh` (CI Step
      0 in `cloudbuild.yaml`, self-declares `Lifecycle: permanent`) and SIT `check-sit-readiness.py` (invoked from
      `.github/workflows/smoke-test-gate.yml`, self-declares `Lifecycle: permanent`) — see
      `/plans/archive/2026_08/issues/immediately_safe_40_delete_cohort_stale_reclassification_2026_08_14.md`). Target:
      per-repo.
      **Immediately-safe subset EXECUTED 2026-08-15 (slot 15, `infra_satellite_ao_dispatch_batch16_2026_08_13.md`)**: 4
      UI `.tsx.bak` splitters deleted (`unified-trading-system-ui@181ae65d8f`); a stale-pointer fix (not a deletion) in
      a live QG script's SSOT citation (`market-tick-data-service@eda08816ef`); UAC `check_schema_organization.py`
      already deleted upstream, no action needed. Checkbox stays OPEN — the campaign-gated DELETE cohort
      (instruments-service 64 / MTDS 22) is still blocked on the manifest-canonicalisation campaigns per this item's own
      gating rule; only the immediately-safe sub-list is done.
- [ ] [AUDIT] P2. **DEPRECATE remediation** — fix the ~10 KEEP/PROMOTE scripts carrying the cloud-discipline gap (UCI
      `get_storage_client`/`gcs_*` + `resolve_bucket_name` + `GCP_PROJECT_ID` via `UnifiedCloudConfig`):
      strategy-service DeFi tracers, `seed_demo_client`, `run_client_reporting_cutover`, `run_amm/lending_validation`,
      `backfill_vix_yahoo`, `run_weekly_pipeline`. (DELETE-cohort scripts are moot — removal moots the flaw.) Target:
      per-repo.
- [x] ✅ **EXTRACTED 2026-08-17 (na-eligibility-audit, infra tranche) → `infra_satellite_ao_dispatch_batch18_2026_08_17.md`
      items 9-12 (one per repo).** ~~PROMOTE-TO-CLI — file the ~8 recurring-prod-logic scripts as their owning
      service's CLI subcommand (`daily_update.py`→client-reporting-api;
      `collect_lst_seasonal_rewards_daily.py`/`check_pipeline_completeness.py`→features-service;
      `measure_honest_coverage.py`/`verify_instrument_manifest_coverage.py`→instruments-service;
      `run_weekly_pipeline.py`/`backfill_vix_yahoo.py`→e2e→service CLI).~~ Not yet executed — tracked there.

## Phase 2 — ruff-lint pass on scripts/ [P2]

- [ ] [SCRIPT] P2. Add `scripts/` to the **ruff lint** pass in `base-service.sh` (lint-only — NOT basedpyright, NOT
      coverage). Decide ruff rule scope + ratchet-vs-hard from the Phase-1 findings (a fleet of messy one-offs will
      light up → likely a baselined ratchet that only goes DOWN, like the existing 5.94/5.95 ratchets). Repo:
      **unified-trading-pm** (`base-*.sh`) → fleet-live via the PM-sourced base scripts (no per-repo rollout).
      **Sequencing:** run AFTER Phase-1 deletes so the ratchet baseline isn't inflated by soon-to-be-deleted scripts.
- [ ] [SCRIPT] P2. **(from Phase-1 Finding 2)** ruff alone won't catch the systemic `scripts/` rot (~75 scripts:
      `from google.cloud import storage` vs UCI; hardcoded `central-element-323112` vs `GCP_PROJECT_ID`; inline `gs://`
      vs `resolve_bucket_name`; `os.environ.setdefault("GOOGLE_CLOUD_PROJECT")`) — that's a TID251/import-surface
      concern, not a style rule. **Extend the existing cloud-SDK-direct (TID251) + `os.getenv`/banned-env ratchets to
      cover `scripts/`** (baselined, counts-only-down), so the rot can't silently grow. AFTER the DELETE pass (baseline
      not inflated by soon-deleted scripts). Repo: unified-trading-pm.

## Phase 3 — D16 strict-quickmerge carve scope [P2]

- [x] ✅ [SCRIPT] P2. **DECIDED + DONE 2026-08-08 — operator ruling: all-repos.** Recorded as D16 in the workspace
      `CLAUDE.md` § "Git discipline + shipping pipeline"; SSOT `/codex/08-workflows/ci-cd-flow.md`. Extend the carve to
      all-repos formally, matching what `check_strict_quickmerge.py`'s `CARVE_PREFIX` already does in practice.
      Confirmed by reading the actual current code:
      `CARVE_PREFIX = (".github/", "scripts/", "plans/", "codex/", "docs/")`
      (`scripts/cicd/check_strict_quickmerge.py:52`) is a bare path-prefix match with zero repo-awareness — each repo's
      own pre-push hook/CI run of this script operates on ITS OWN relative commit paths, so `scripts/` is already carved
      out uniformly for every repo's own commit range, not scoped to PM. No code change needed (the decision matches
      existing behavior); updated the prose that mis-stated it as "PM `scripts/**`" to match reality:
      `/codex/08-workflows/ci-cd-flow.md` § "Strict quickmerge" carve-out item 3, `cursor-configs/CLAUDE.md`'s Git
      discipline carve #3, and `check_strict_quickmerge.py`'s own module docstring (which had the same "PM scripts"
      framing). Keep `tests/` exempt either way (it's caught in staging via pytest) — unchanged, no code touched
      `tests/`. Repo: unified-trading-pm.

## Codex SSOT updates

- `/codex/06-coding-standards/script-homes.md` — add (a) the **lifecycle marker convention** (`Epic:`/`Lifecycle:`/
  `Delete-when:`, the closed `permanent|campaign|oneoff` set, `Delete-when`-driven pruning with no runtime tracking) and
  (b) the "scripts/: ruff-lint YES; basedpyright + coverage NO (by design, to avoid refactor tech-debt on throwaway
  code); recurring logic → CLI" clarification — when Phase 0/2 land.
- CLAUDE.md — one-liner pointing to the script lifecycle marker + the ruff-only rule (per the durable-facts-live-here
  rule), once shipped.

## Success criteria

- Every `scripts/` file declares a valid lifecycle marker (`Epic:` + `Lifecycle:` + `Delete-when:` — all three, `NA` for
  `permanent`; was `[+Delete-when:]`, same 2026-07-26 correction as the Phase-0 enforcement todo above); the sweep flags
  satisfied-`Delete-when` / stale scripts to their epic owner.
- Every service repo's `scripts/` audited; the delete/deprecate list executed (0 out-of-shape scripts left in-tree).
- `scripts/` is ruff-linted fleet-wide (ratcheted); basedpyright + coverage remain excluded by design.
- The D16 carve scope is decided + implemented; CLAUDE.md matches `check_strict_quickmerge.py`.
- `tests/` unchanged (confirmed intentional).

## Progress Log

- **2026-08-11 (slot 3, interactive) — D16's `scripts/**` carve SCOPE is SUPERSEDED (operator ruling 2026-08-10).** The
  Phase-3 D16 todo above records the carve as all-repos blanket `scripts/**`, ratified 2026-08-08. That scope is now
  NARROWED: the exempt set is exactly `scripts/quality_gates/`, `scripts/quality-gates-base/`, `scripts/hooks/`,
  `scripts/cicd/` and `scripts/quality-gates*.sh` (`GATE_INFRA_PREFIX` / `GATE_INFRA_FILE_PREFIX` in
  `check_strict_quickmerge.py`); every other `scripts/**` `.py`/`.ts`/`.tsx` is normal gated source requiring a
  `Quickmerge:` trailer. Shipped unified-trading-pm@3895be718f (3 new boundary tests; 18/18 green). **The D16 todo
  itself is NOT reopened** — its all-repos-not-PM-only finding was correct and survives; only the breadth of the path
  set changed. **Why**: the blanket carve created a live asymmetry — the push guard waved `scripts/**` through while QG
  STEP 5.105 SCANS `scripts/**`. On 2026-08-10 that let
  `market-tick-data-service/scripts/restamp_tradfi_cme_future_blank_instrument_id_2026_08_10.py` reach live-defi-rollout
  ungated carrying a banned subprocess GCS call, reddening LDR and promote PR #939 for the whole fleet. D16's
  chicken-and-egg rationale ("a corrected gate can't pass through the gate it is fixing") justifies exempting the gate
  machinery; it never justified exempting production backfill/migration/restamp scripts, which run against PROD data and
  are production code by consequence. Doc surfaces updated in the same commit: `/codex/08-workflows/ci-cd-flow.md` §
  "Strict quickmerge" carve-out item 3, `cursor-configs/CLAUDE.md` § "Git discipline" carve #3, and the checker's own
  module docstring.

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — unchanged mixed shape. Re-read
  end-to-end; `grep -cE '^- \[ \]'` = 7, down from 8 (today's item-79 operator ruling closed the D16 carve-scope todo,
  already reflected above). Checked the remaining 7 against today's operator-Q&A cheat sheet: none matches. The
  enforcement-wiring item (line ~160) duplicates the folded-in `[SCRIPT] P1` item (line ~385) in substance — both
  BLOCKED on the same unmet fleet-wide precondition (the 2026-08-02 measurement found 96 invalid-`Epic:` + 136
  invalid-`Lifecycle:` + 2 `Delete-when:NA`-misuse files, "gate-clearable: NO"). The DEPRECATE-remediation item (line
  ~197) is CONFLICT-GATED — re-confirmed still claimed by `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`
  item (k) ("cloud-agnostic sweep of ~60 scripts... Same fix class, wider scope, already claimed"), matching this doc's
  own prior audits' citation. The ruff-lint + TID251 items (lines ~209/~214) are explicitly sequenced AFTER the
  DELETE-execution item, which is itself campaign-gated. The Delete-EXECUTION item (line ~190) bundles a genuinely
  bounded sub-list (the "immediately-safe ~40") with a campaign-gated cohort in one checkbox — same
  bundling-blocks-whole-doc-flip pattern seen elsewhere this sweep. No clean whole-doc RECLASSIFY; `assigned_vm: NA`
  correct, consistent with every prior audit of this doc since 2026-07-30.
- **2026-08-08 (operator Q&A round5, infra tranche, item 79)**: Operator ruled the D16 carve scope: all-repos, matching
  what `check_strict_quickmerge.py`'s `CARVE_PREFIX` already does in practice. Read the actual current `CARVE_PREFIX`
  logic (`scripts/cicd/check_strict_quickmerge.py:52`) before closing — confirmed it's a bare path-prefix match with no
  repo-awareness, so the code already behaved all-repos; only the codex/CLAUDE.md prose (mis-stated as "PM scripts/**")
  needed correcting, not the code. Flipped the Phase-3 todo to done; updated `/codex/08-workflows/ci-cd-flow.md`,
  `cursor-configs/CLAUDE.md`, and the script's own module docstring to match. This was one of the 2 items this doc's
  Progress Log previously cited as operator-gated (per `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s
  BLOCKED-OPERATOR-DECISION section) — that citation is now stale for this item specifically; the doc's other
  operator-gated item + the folded-in `[SCRIPT] P1` condition-block are untouched by this session.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since 2026-08-02. Re-read end-to-end;
  `grep -cE '^- \[ \]'` = 8, matching. Mixed shape unchanged: 2 items operator-gated (cited in
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s BLOCKED-OPERATOR-DECISION section), the folded-in `[SCRIPT] P1`
  still condition-blocked on an unmet fleet-wide precondition. Note: `ag_closeout_audit_infra_parked_2026_08_03.md`
  finding 13 previously flagged the two ruff-lint items (add `scripts/` to the ruff pass; extend TID251/`os.getenv`
  ratchets to `scripts/`) as "potentially bounded/mechanical" batch7 candidates but explicitly un-conflict-checked —
  still un-scoped as of this run, re-flagging as RECLASSIFY-candidates worth a dedicated look, not actioned here.
- **2026-06-18 — Phase 1 characterization DONE (read-only).** Fanned out 6 Opus sub-agents (one per repo-cluster) over
  all 21 service repos' `scripts/` (~820 `.py`+`.sh`; PM excluded). Results doc:
  `plans/audit/results/repo_scripts_characterization_2026_06_18.md`. Three headline findings: **(1)** the big DELETE
  cohort (instruments-service 64 / MTDS 22) is **campaign-gated** — the 2026-06 manifest-canonicalisation campaign is
  ACTIVE, so the `*_2026_06_01.py` set is in-flight (KEEP) and dated 2026-05 reconcilers may be re-run; delete per-AG
  only after that AG's canonicalisation plan archives → **no fleet `git rm`**. **(2)** systemic `scripts/`
  cloud-discipline rot (~75: `google.cloud`-direct / hardcoded `central-element-323112` / inline `gs://`), invisible
  because `scripts/` is outside the QG gate — validates the ruff decision AND motivates extending the TID251/banned-env
  ratchets to `scripts/` (new Phase-2 todo). **(3)** ~8 PROMOTE-TO-CLI (recurring prod logic as scripts;
  `daily_update.py` the clearest). Plus 5 dead-checker tooling scripts (pointed at deleted/archived paths). Phase 1
  flipped; delete + deprecate + promote execution todos scoped with the gating rule. **Next:** Phase 0 marker
  codification, then the immediately-safe ~40 deletes (UI splitters + done bucket migrations + dead checkers), then the
  campaign-gated cohort as each plan archives.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **2026-08-02 — fleet-wide lifecycle-marker coverage measured (`infra_satellite_ao_dispatch_batch1-014`).** Ran the
  measurement the Folded-in-scope `[SCRIPT] P1` item below is gated on. See "## Fleet-wide lifecycle-marker coverage
  measurement (2026-08-02)" for the per-repo table + verdict. **Verdict: gate-clearable: NO** — down from 11+ repos with
  unstamped scripts (2026-07-15 baseline) to 2 files in 2 repos missing a field, but the checker-as-specified (`Epic:` ∈
  registry, closed `Lifecycle` enum, non-`permanent` ≠ `Delete-when: NA`) would still fail CI immediately fleet-wide on
  96 invalid-`Epic:` + 136 invalid-`Lifecycle`-value + 2 `Delete-when: NA`-misuse files. Did **not** build or wire
  `check_script_lifecycle_markers.py` — that stays operator-gated per the source todo. The Folded-in-scope `[SCRIPT] P1`
  item stays BLOCKED; its unblock condition is now precisely measured, not just "not empty" from a prior year-old grep.

## Fleet-wide lifecycle-marker coverage measurement (2026-08-02)

**Purpose**: measure — never enforce — whether the fleet is clean enough for the operator to unblock the Folded-in-scope
`[SCRIPT] P1` item below (build + wire `check_script_lifecycle_markers.py`). Per
`/codex/06-coding-standards/script-homes.md:97,100,154-155`, all three of `# Epic:` / `# Lifecycle:` / `# Delete-when:`
are MANDATORY and PRESENT on every `scripts/` file (`Delete-when: NA` only for `permanent`); `Epic:` must resolve to a
slug in the epic registry.

**Method**: per repo, over every `scripts/*.py` + `scripts/*.sh` file: (1) missing `# Epic:` / missing `# Lifecycle:` /
missing `# Delete-when:` — a file with no line anywhere matching the pattern (mirrors the precondition's own
`grep -rL '^# Delete-when:' */scripts/` check, not a stricter "immediately after shebang" placement check); (2)
`# Epic:` value not in the **epic registry** — taken as `plans/epics/*.md` basenames (minus `.md`), excluding
`README.md` and the 3 `*_SUPERSEDED_*` variants (23 valid slugs; mirrors `regen_vm_registry.py`'s own glob), first
whitespace-delimited token of the value compared verbatim; (3) non-`permanent` files whose `Delete-when:` value is `NA`
(case-insensitive). **Scope**: the 25 repos cloned in this worker's slot topology (the standard fleet per CLAUDE.md's
System map) — does not include ad-hoc worktree variants (`-sports-wt`, `-cid-migration`, etc.) if any exist outside this
slot's clone set.

| Repo                              | scripts files | missing Epic | missing Lifecycle | missing Delete-when | invalid Epic (not in registry) | non-permanent w/ Delete-when:NA |
| --------------------------------- | ------------: | -----------: | ----------------: | ------------------: | -----------------------------: | ------------------------------: |
| agent-orchestrator                |            49 |            0 |                 0 |                   0 |                              1 |                               2 |
| alerting-service                  |             5 |            0 |                 0 |                   0 |                              0 |                               0 |
| batch-live-reconciliation-service |             4 |            0 |                 0 |                   0 |                              0 |                               0 |
| client-reporting-api              |             9 |            1 |                 1 |                   1 |                              0 |                               0 |
| deployment-api                    |             9 |            1 |                 0 |                   0 |                              0 |                               0 |
| deployment-service                |           320 |            0 |                 0 |                   0 |                             10 |                               0 |
| deployment-ui                     |             5 |            0 |                 0 |                   0 |                              0 |                               0 |
| e2e-testing                       |           213 |            0 |                 0 |                   0 |                             23 |                               0 |
| execution-service                 |            12 |            0 |                 0 |                   0 |                              0 |                               0 |
| features-service                  |            67 |            0 |                 0 |                   0 |                              3 |                               0 |
| fund-administration-service       |             2 |            0 |                 0 |                   0 |                              0 |                               0 |
| greeks-service                    |             2 |            0 |                 0 |                   0 |                              0 |                               0 |
| ibkr-gateway-infra                |            11 |            0 |                 0 |                   0 |                              0 |                               0 |
| instruments-service               |           305 |            0 |                 0 |                   0 |                             10 |                               0 |
| market-data-processing-service    |            20 |            0 |                 0 |                   0 |                              0 |                               0 |
| market-tick-data-service          |           210 |            0 |                 0 |                   0 |                             41 |                               0 |
| ml-service                        |            12 |            0 |                 0 |                   0 |                              0 |                               0 |
| strategy-service                  |            30 |            0 |                 0 |                   0 |                              1 |                               0 |
| system-integration-tests          |             7 |            0 |                 0 |                   0 |                              0 |                               0 |
| trading-agent-service             |             4 |            0 |                 0 |                   0 |                              0 |                               0 |
| unified-api-contracts             |            36 |            1 |                 1 |                   1 |                              1 |                               0 |
| unified-trading-api               |             5 |            0 |                 0 |                   0 |                              0 |                               0 |
| unified-trading-library           |            10 |            0 |                 0 |                   0 |                              1 |                               0 |
| unified-trading-pm                |           634 |            0 |                 0 |                   0 |                              5 |                               0 |
| unified-trading-system-ui         |            17 |            0 |                 0 |                   0 |                              0 |                               0 |
| **TOTAL (25 repos)**              |      **1998** |        **3** |             **2** |               **2** |                         **96** |                           **2** |

**Missing-field detail (3 files, 2 repos)**: `client-reporting-api/scripts/__init__.py` (0 bytes, empty package marker —
missing all 3 fields) and `unified-api-contracts/scripts/__init__.py` (0 bytes, same) each miss all 3 fields;
`deployment-api/scripts/census_manifest_data_type_2026_07_24.py` misses only `# Epic:` (it carries `Lifecycle`/
`Delete-when` text embedded in its module docstring, not a standalone comment header — non-conformant placement, but the
grep-based precondition still finds those two lines since they happen to start the line).

**`na_misuse` detail (2 files, 1 repo)**: `agent-orchestrator/scripts/orchestrator/audit_cron_notify.py` and
`.../check_null_brief_hash_growth.py` — both carry `Lifecycle: periodic` (itself not a valid enum value — see
supplementary finding below) with `Delete-when: NA`.

**Supplementary finding (beyond the 3 requested counts, but directly load-bearing for gate-clearability — the checker
also fails CI on an unknown `Lifecycle` value per `script-homes.md`'s own enforcement description): invalid `Lifecycle:`
value (not `permanent`/`campaign`/`oneoff`)** — **136 files fleet-wide**, heavily concentrated in
market-tick-data-service (45) and instruments-service (38), driven almost entirely by one systemic near-miss:
**`one-off` (hyphenated) instead of the closed `oneoff` token** (the large majority of both repos' count). Other
observed values: `periodic` (agent-orchestrator, 5), `campaign:<sub-label>` embedding a colon-suffixed sub-campaign name
instead of the bare `campaign` token (client-reporting-api 4, execution-service 8), `reusable`/`reusable-tooling`/
`reusable-investigation`/`reusable-narrow`/`re-runnable`/`temporary`/`one-shot`/`recurring`/`bridge` (scattered
one-offs). Per-repo counts: agent-orchestrator 5, client-reporting-api 4, deployment-api 2, deployment-service 3,
e2e-testing 11, execution-service 8, features-service 6, instruments-service 38, market-data-processing-service 4,
market-tick-data-service 45, unified-api-contracts 1, unified-trading-library 1, unified-trading-pm 8 (total 136 across
13 repos). Not one of the 3 requested counts, but worth surfacing now rather than as a second surprise after the
missing-field precondition clears — the `one-off`→`oneoff` fix alone would close the bulk of this at low cost (a
fleet-wide rename, not per-file judgment).

**Verdict: gate-clearable — NO.** The plan's own stated precondition (`grep -rL '^# Delete-when:' */scripts/` empty
fleet-wide) is **not yet met** (2 files), though very close — down from 11+ repos at the 2026-07-15 baseline to 2
trivial `__init__.py` files in 2 repos. Even once that clears, the checker as specified in the Folded-in-scope item
below would **still fail CI fleet-wide** on day one: 96 files carry an `Epic:` value outside the epic registry (mostly
dated one-off/campaign plan-slugs used in place of the owning everlasting epic — e.g. `sports_manifest_canonicalisation`
instead of `sports_master`), 2 files misuse `Delete-when: NA` on a non-`permanent` lifecycle, and (supplementary) 136
files carry a `Lifecycle:` value outside the closed `permanent|campaign|oneoff` enum. **Recommended sequencing for the
operator**: (1) stamp the 3 missing-field files (trivial — 2 are empty `__init__.py`, add
`# Epic: <owning-epic> / # Lifecycle: permanent / # Delete-when: NA`; the deployment-api file needs a proper `# Epic:`
header line, not just docstring text), (2) fleet-wide `one-off`→`oneoff` rename (closes most of the 136), (3) epic-owner
pass on the 96 invalid `Epic:` values (retarget to the correct everlasting epic slug — or decide some belong in the
registry, e.g. `on-chain-alpha-track` in e2e-testing, 23 files), (4) fix the 2 `na_misuse` files' `Lifecycle` value
first (they're `periodic`, itself invalid) then their `Delete-when`. Only after all four clear does
`grep -rL '^# Delete-when:' */scripts/` being empty actually mean the checker will land green, not just that the
narrowest literal precondition passed.

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [ ] [SCRIPT] P1. **BLOCKED — condition-gated, do NOT start until every Phase-0 + Phase-1 repo above is ✅** (else it
      reds the whole fleet on still-unstamped repos). Downgraded from `[OPERATOR]` 2026-07-27 (category B/6 — the
      unblock condition is a plain read-only grep, not a human value-judgment, so it does not need operator authority;
      it stays BLOCKED right now purely because the condition itself is unmet): a fresh fleet-wide check today
      (`grep -rL '^# Delete-when:' */scripts/ --include='*.py' --include='*.sh'` across all 28 repo checkouts) is
      **NOT** empty — 11+ repos still have unstamped scripts (unified-trading-pm 11, deployment-service /
      deployment-service-sports-wt 5 each, deployment-ui 4, e2e-testing 2, instruments-service 2,
      market-tick-data-service (+ its `-cid-migration`/`-sports-wt` worktrees) 2 each, plus one each in
      client-reporting-api / features-service / fund-administration-service / greeks-service / unified-api-contracts).
      Build + wire the lifecycle-marker QG checker so the 3-field marker is enforced like other frontmatter'd filetypes:
      a checker (`scripts/quality_gates/check_script_lifecycle_markers.py`) that FAILS when a `scripts/` file is missing
      any of `# Epic:` / `# Lifecycle:` / `# Delete-when:`, or has an invalid `Lifecycle` value, or an `Epic:` not in
      `orchestrator_vm_registry.yaml`'s epic set, or a non-`permanent` carrying `Delete-when: NA`. Wire it into the
      PM-sourced `base-service.sh` + `base-library.sh` so it rides fleet-wide with NO per-repo rollout (mirror STEP
      5.94/5.95). This unblocks (any agent may confirm — no operator sign-off needed for the check itself) once a re-run
      of the same grep above comes back empty fleet-wide. Update `/codex/06-coding-standards/quality-gates.md` +
      `script-homes.md` § "What gates a scripts/ file" in the same unit. Target: **unified-trading-pm** (checker + base
      wiring) → fleet. (FOLDED IN from scripts_lifecycle_marker_rollout_2026_06_18, 2026-07-15, plan-reconcile §6
      operator ruling)
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Mixed doc: 5 of 8 items
  look bounded/deterministic, but 2 are explicitly operator-gated per a dated citation in
  infra_satellite_ao_dispatch_batch1_2026_07_26.md's own BLOCKED-OPERATOR-DECISION section, and 1 is genuinely blocked
  on an unmet fleet-wide precondition (11+ repos still missing a marker). Flipping the whole doc would improperly expose
  the gated items to blind dispatch — stays NA as a whole pending a targeted split of just the 5 bounded items into a
  future batch, not actioned this run.
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid — unchanged from the 2026-07-30
  verdict.** In scope only because a context-scout backfill touched the file; no content change since. Read end-to-end;
  `grep -cE '^- \[ \]'` = **8**, matching this verdict's item count. The mixed shape is unchanged and still blocks a
  whole-doc flip: 2 items are operator-gated per a dated citation in
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s BLOCKED-OPERATOR-DECISION section, and the folded-in
  `[SCRIPT] P1` is genuinely condition-blocked on an unmet fleet-wide precondition (11+ repos still carry unstamped
  `scripts/` files, so wiring the lifecycle-marker checker today reds the whole fleet). Flipping the doc would expose
  the gated items to blind dispatch. The standing recommendation is unchanged and still un-actioned: a targeted split of
  just the bounded items into a future infra batch — `/ag-closeout-audit`'s Phase-3 job, not an `assigned_vm` flip.
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** (infra tranche): RECLASSIFY_SPLIT — extracted the PROMOTE-TO-CLI item (8
  scripts, split per-repo per this doc's own "one small plan item per repo" instruction) to
  `infra_satellite_ao_dispatch_batch18_2026_08_17.md` items 9-12 (not yet executed). Verified ungated on its own
  merits — its own todo text carries no "GATED + REVIEWED" language unlike its DELETE/DEPRECATE siblings, and the
  broader "human-judgment work" framing found elsewhere in the corpus
  (`features_service_coverage_and_script_canon_2026_06_10.md`) was about the ORIGINAL, now-superseded whole-sweep
  checkbox, not this already-scoped, already-classified promote list. The other 6 open items remain
  gated/condition-blocked (campaign gates, an unmet fleet-wide precondition, sequencing after the delete pass) — doc
  stays `assigned_vm: NA`.
- **context-scout 2026-08-17**: re-verified context_scope (4 entries), unchanged — corrected one entry's path to the
  corpus's leading-slash repo-root-relative convention (`plans/audit/...` → `/plans/audit/...`), content unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
