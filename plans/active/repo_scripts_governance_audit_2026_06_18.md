---
title: "Repo scripts/ governance — ruff-lint pass + deprecate/delete audit + strict-quickmerge carve scope (D16)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
created: 2026-06-18
locked_by: live-defi-rollout
source:
  - operator decision 2026-06-18 (CI/CD drift audit D16 follow-up)
  - plans/audit/results/cicd_pipeline_vs_plans_drift_audit_2026_06_17.md § D16
---

# Repo scripts/ governance — lint + audit + the strict-quickmerge carve scope

## Decisions (operator-ratified 2026-06-18)

1. **`scripts/` stays OUT of typecheck (basedpyright) + coverage — by design.** Repo `scripts/` are one-off/throwaway
   (run a handful of times, then deleted). Gating them with the typechecker/coverage only manufactures **refactor
   tech-debt** for code meant to be removed (every refactor would have to keep soon-to-be-deleted scripts type-clean).
   Recurring/important logic must become a **CLI subcommand** (which IS gated as part of `$SOURCE_DIR`), never a
   permanent `scripts/` file. Confirms the existing Script-Homes contract (`codex/06-coding-standards/script-homes.md`).
2. **ADD a ruff-lint pass on `scripts/`** (cheap, autofixable rot-catch — syntax / imports / obvious bugs) — **no
   basedpyright** (too heavy + high-noise for throwaway code). Exact ruff scope (which rules, ratchet vs hard) is
   surfaced by the Phase-1 audit.
3. **`tests/` stays AS-IS** — essential; ruff-linted + pytest-run on every QG (local + CI + staging); deliberately
   **no** basedpyright (noise > help on test code); naturally no coverage. No change.
4. **D16 — the strict-quickmerge `scripts/` carve scope (PM-only vs all-repos) is PENDING this audit.** Verified: the
   carve only affects **provenance** (the `Quickmerge:` trailer + dep-gate pre-flight), NOT content-gating — `scripts/`
   is QG-unchecked either way. Decide after the audit shows what service-repo `scripts/` actually contain.
5. **Every script declares a lifecycle marker (operator 2026-06-18)** — a 3-line greppable comment header (works for
   `.sh` + `.py`): `Epic:` (owning epic), `Lifecycle:` (`permanent | campaign | oneoff`), `Delete-when:` (completion
   condition, required for `campaign`/`oneoff`). Not every script is throwaway — `setup.sh` is permanent lifecycle
   infra; a GCS-migration script is a weeks-long **campaign**. The marker lets the audit distinguish them mechanically
   instead of re-deriving each time, and makes "delete after use" self-enforcing. **`Epic:` (not a single plan)**
   because a script spans multiple plans (the GCS cutover touches MTDS / instruments / deployment plans at once); epics
   are stable
   - multi-plan + validate-able vs the registry like `assigned_vm`. **Epics are EVERLASTING**, so `Epic:` is OWNERSHIP,
     not the delete trigger — `Delete-when:` carries the actual completion signal. **`last_run` is DERIVED, never a
     manual header field** (a hand-updated field would rot — nobody updates a comment after every run): staleness =
     `git log -1 --format=%cs -- <script>`; a campaign script needing true run-frequency appends to a central
     auto-ledger (a `log_script_run.sh "$0"` one-liner, like `log-manifest-mutation.sh`). Full convention in Phase 0.

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

- [ ] [DESIGN] P2. Codify the 3-line script lifecycle marker (a comment header — works for `.sh` AND `.py`, so it's not
      Python-docstring-only):

  ```
  # Epic: <epic-slug>                       # owning epic — validated vs plans/epics/ registry (required, ALL scripts)
  # Lifecycle: permanent|campaign|oneoff    # required, ALL
  # Delete-when: <concrete completion condition>   # required for campaign/oneoff; permanent omits it
  ```

  Closed `Lifecycle` set mirrors the VM `lifecycle_class` spirit: **`permanent`** ≈ LONG_LIVED (`setup.sh`, dev tooling;
  template-managed scripts like `setup.sh`/`quality-gates.sh`/`quickmerge.sh` are auto-permanent — PM-sourced); whereas
  **`campaign`** ≈ a temporary-state-with-named-successor (the GCS bucket migration — lives weeks, deleted at
  completion); **`oneoff`** ≈ EPHEMERAL (run-once; `Delete-when:` = "after prod-run + orphan-sweep=0"). `Epic:` is
  OWNERSHIP (multi-plan; epics everlasting → NOT the delete trigger); `Delete-when:` carries the completion signal.
  Codify in `codex/06-coding-standards/script-homes.md`. Composes with: VM `lifecycle_class`, the Runbook
  Execution-Owner SSOT (`owner/cadence/verifier/last_executed`), and "Temporary states + their canonical follow-up
  plans" — same lifecycle-declaration idea, now for scripts.

- [ ] [SCRIPT] P2. Wire enforcement (ratcheted warn→block, like the 5.94/5.95 checks): a script-homes sweep / QG check
      that (a) every `scripts/` file declares `Epic:` + `Lifecycle:` (+ `Delete-when:` for campaign/oneoff); (b) `Epic:`
      ∈ the epic registry (reuse the `assigned_vm`-vs-registry `regen_vm_registry.py --check` pattern); (c) surfaces
      every `campaign`/`oneoff` whose `Delete-when` looks satisfied OR whose `git` last-modified is stale (>N months) →
      flagged for the **epic owner** to confirm + delete. Repo: unified-trading-pm.

- [ ] [DESIGN] P2. `last_run` / run-frequency is **derived, never a manual header field**: default staleness =
      `git log -1 --format=%cs -- <script>` (last-modified, zero maintenance); a campaign script that needs true
      run-frequency appends to a central auto-ledger via a `log_script_run.sh "$0"` one-liner (mirrors
      `log-manifest-mutation.sh`). No hand-updated field anywhere.

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
      immediately-safe ~40** (UI 2026-03 `.tsx.bak` splitters/codemods; done deployment-service bucket migrations; the 5
      dead checkers — UAC `check_schema_organization`, UTL `check-ruff-versions`, SIT `check-sit-readiness`, MTDS QG
      stale SSOT pointer, deployment-service `aggregate_instruments`). Target: per-repo.
- [ ] [AUDIT] P2. **DEPRECATE remediation** — fix the ~10 KEEP/PROMOTE scripts carrying the cloud-discipline gap (UCI
      `get_storage_client`/`gcs_*` + `resolve_bucket_name` + `GCP_PROJECT_ID` via `UnifiedCloudConfig`):
      strategy-service DeFi tracers, `seed_demo_client`, `run_client_reporting_cutover`, `run_amm/lending_validation`,
      `backfill_vix_yahoo`, `run_weekly_pipeline`. (DELETE-cohort scripts are moot — removal moots the flaw.) Target:
      per-repo.
- [ ] [AUDIT] P2. **PROMOTE-TO-CLI** — file the ~8 recurring-prod-logic scripts as their owning service's CLI subcommand
      (`daily_update.py`→client-reporting-api; `collect_lst_seasonal_rewards_daily.py`/`check_pipeline_completeness.py`→
      features-service; `measure_honest_coverage.py`/`verify_instrument_manifest_coverage.py`→instruments-service;
      `run_weekly_pipeline.py`/`backfill_vix_yahoo.py`→e2e→service CLI). One small plan item per repo. Target: per-repo.

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

- [ ] [SCRIPT] P2. Decide + implement the `scripts/` provenance-carve scope, informed by Phase 1 (how often service-repo
      scripts are legitimately direct-pushed during migrations): - **PM-only** → make `check_strict_quickmerge.py`
      repo-aware (carve `scripts/` for PM; treat a service repo's `scripts/*.py` as gated source needing the
      `Quickmerge:` trailer) + update CLAUDE.md carve #3 to match. - **all-repos** → update CLAUDE.md carve #3 to "any
      repo's `scripts/**`" so the doc matches the current code. Keep `tests/` exempt either way (it's caught in staging
      via pytest). Repo: unified-trading-pm.

## Codex SSOT updates

- `codex/06-coding-standards/script-homes.md` — add (a) the **lifecycle marker convention** (`Epic:`/`Lifecycle:`/
  `Delete-when:`, the closed `permanent|campaign|oneoff` set, `last_run` is derived-not-manual) and (b) the "scripts/:
  ruff-lint YES; basedpyright + coverage NO (by design, to avoid refactor tech-debt on throwaway code); recurring logic
  → CLI" clarification — when Phase 0/2 land.
- CLAUDE.md — one-liner pointing to the script lifecycle marker + the ruff-only rule (per the durable-facts-live-here
  rule), once shipped.

## Success criteria

- Every `scripts/` file declares a valid lifecycle marker (`Epic:`+`Lifecycle:`[+`Delete-when:`]); the sweep flags
  satisfied-`Delete-when` / stale scripts to their epic owner.
- Every service repo's `scripts/` audited; the delete/deprecate list executed (0 out-of-shape scripts left in-tree).
- `scripts/` is ruff-linted fleet-wide (ratcheted); basedpyright + coverage remain excluded by design.
- The D16 carve scope is decided + implemented; CLAUDE.md matches `check_strict_quickmerge.py`.
- `tests/` unchanged (confirmed intentional).

## Progress Log

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
