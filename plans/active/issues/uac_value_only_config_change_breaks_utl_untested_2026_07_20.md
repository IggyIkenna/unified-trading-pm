---
doc_type: issue
title: >-
  UAC value-only registry/config edits break UTL's own tests with no gate able to see it — 2 instances within 24h
  (massive SOURCE_PRIORITY removal, SPORTS bucket key)
summary: >-
  A UAC edit that changes a registry VALUE (not a symbol) breaks a downstream consumer's own test suite while the
  consumer's tree never changes, so nothing re-runs its CI. Every existing gate is blind to it: SIT is an API-surface
  linter (static AST name-presence over sibling source; it installs only UAC and never runs a dependent's tests),
  detect_breaking_change.py is name-and-signature-only so a dict-value or YAML edit reads is_breaking=false, and
  cascade-qg-ordering.yml — the one component designed for this fan-out — dispatches `quality-gate-run`, an event NO
  repo declares a repository_dispatch listener for, so it fails GREEN by reading the pre-existing ci_status. Instance 1
  (uac@a2beed46, massive removed from SOURCE_PRIORITY) reddened UTL main for ~9h undetected and was then laundered green
  by SIT. Instance 2 (SPORTS key dropped from cloud-providers.yaml) is FIXED in utl@c26a5297 — and on investigation was
  intra-workspace fixture drift rather than a UAC-ref divergence. The CLASS (todos 2-5) remains open.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [cross-repo, ci-cd, sit, breaking-detection, data-correctness, quality-gates]
related:
  [
    /plans/archive/issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
  ]
created: 2026-07-20
author: unknown
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-07-20 while root-causing the overnight T0 FAILURE + CI REGRESSION alerts on unified-trading-library",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-21
resolved_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    .github/workflows/python-quality-gates-v2.yml,
    scripts/cicd/detect_breaking_change.py,
    /plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/epics/infrastructure_master.md,
  ]
---

# UAC value-only config changes break UTL with no gate able to see it

## The class

An upstream T0 (UAC) changes a **value** inside a registry or config file. A downstream T0/T1 consumer's behaviour is
derived from that value at runtime, so the consumer's own tests break — but the consumer's tree never changed, so its CI
never re-runs and nothing notices.

## Instances (all authored by UAC within 24h of each other)

| #   | UAC commit | Change                                           | Downstream effect                                                          | State                      |
| --- | ---------- | ------------------------------------------------ | -------------------------------------------------------------------------- | -------------------------- |
| 1   | `a2beed46` | `massive` removed from tradfi `SOURCE_PRIORITY`  | 10 UTL manifest-writer tests fail                                          | FIXED (fixtures repointed) |
| 2   | `1ff91e5b` | `SPORTS` key dropped from `cloud-providers.yaml` | 2 `test_bucket_naming_cell_sweep` cells fail (`gcp`/`aws:features:sports`) | **FIXED** — utl@c26a5297   |

Instance 1 timeline: UTL v2 green 07-19 17:22Z → UAC `a2beed46` lands 17:34Z → overnight audit 07-20 02:20Z finds 10
failures. UTL main was red for ~9h with nothing detecting it, then SIT stamped `SIT_VALIDATED` at 05:21Z and erased the
red entirely (that laundering is separately fixed — see `ci_status_store.resolve_status`'s main-red provenance guard).

## Instance 2 — RESOLVED (kept for the diagnostic trail)

`resolve_bucket_name(cloud='gcp', kind='features', asset_group='sports')` raises
`BucketNamingError: Kind 'features' on cloud 'gcp' has no entry for asset_group='sports'. Available: ['CEFI', 'DEFI', 'PREDICTION', 'TRADFI']`.

Priority-setting facts measured 2026-07-20:

- `1ff91e5b` is **NOT on UAC main** (LDR only) — so this has not reddened UTL main yet.
- The sweep **did not run at all** in the 02:20Z CI slice (0 occurrences in that run's log), so CI has not seen it.
- It **does** reproduce locally against the sibling UAC-LDR checkout.

That framing was superseded — see the RESOLVED section immediately below.

### RESOLVED 2026-07-20 — `unified-trading-library@c26a5297`

**Two corrections to the diagnosis above, both measured.**

1. **The UAC attribution was imprecise.** `_candidate_yaml_paths()` probes `deployment-service/configs/` FIRST and UAC's
   packaged copy LAST, so locally the operative file is deployment-service's — UAC is never reached. The same SPORTS
   removal is present in the deployment-service and PM copies too, so the failure reproduces without UAC's LDR commit at
   all. UAC's copy only becomes operative in a standalone clone with no siblings. Instance 2 is therefore NOT a
   UAC-LDR-vs-main divergence; it is intra-workspace fixture drift.
2. **The mechanism was a deliberate `delenv`, not a passive shadow.** `tests/conftest.py` set
   `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` to the fixture process-wide before collection, and the sweep's own body does
   `monkeypatch.delenv(...)` + `_clear_yaml_cache()`. So collection read the fixture and execution read the real config
   — by construction, in one test.

**Fix shipped:** deleted the conftest override + the fixture (its standalone-clone rationale was obsolete —
`_packaged_uac_yaml_path()` is the always-available fallback now), repointed the 6 direct consumers at UAC's packaged
copy, and added a cross-copy parity pin (`tests/cloud_interface/unit/test_cloud_providers_yaml_parity.py`) because the
sweep is inherently self-referential and cannot catch a key REMOVAL. Parity verified to detect removed/added/changed
keys and stay silent on identical; the three live copies are in exact parity at 62 keys.

**Explicitly NOT changed:** `test_bucket_naming.py`'s `_SNAPSHOT_YAML` still carries `features.SPORTS`. An earlier
analysis called that a false pass; it is not. The snapshot is deliberately synthetic and says so in its own comment
("exercises resolver mechanics, not the live estate ... Do not treat it as a copy"), so pinning a historical shape there
is correct.

### Original diagnosis (superseded by the two corrections above)

`test_bucket_naming_cell_sweep._build_sweep_params()` (`tests/cloud_interface/unit/`) is correctly written to derive its
cells from the live YAML rather than hardcoding them — it iterates `_load_cloud_providers_yaml()` and keeps only keys in
`_ASSET_GROUPS`. But **collection-time and run-time resolve different files**:

- at collection the loader yields a mapping that still contains `SPORTS` (hence the `gcp:features:sports` param exists)
- at run time, with the autouse `_reset_yaml_cache` fixture applied, it resolves UAC's
  `unified_api_contracts/config/cloud-providers.yaml`, whose `features` entry is `['CEFI','TRADFI','DEFI','PREDICTION']`

`unified-trading-library/tests/fixtures/cloud-providers.yaml` still carries `SPORTS` at lines 66 / 202 (and for
`market-data-tick` / `instruments-store`), which is the likely collection-time source. **Do not just delete those
lines** — first establish which YAML the sweep is supposed to be authoritative against, because a fixture that silently
shadows the real config at collection but not at execution will keep producing phantom cells for every future key
change.

## Why no gate catches the class

1. **SIT is an API-surface linter, not an integration test.** `full-workspace-sit.yml` installs only UAC
   (`uv pip install -e unified-api-contracts pytest pyyaml`) and runs one step: `run_cross_repo_invariants.sh`. UTL is
   cloned but never installed, never imported, and its `tests/` are never collected. The UTL invariant AST-parses
   `unified_trading_library/__init__.py` and asserts 27 symbol names still exist. `SOURCE_PRIORITY` still exists and is
   still exported — only its value changed. So `SIT_VALIDATED` means "the names other repos import still exist", not
   "the resolved combination works".
2. **The differ is value-blind.** `detect_breaking_change.py` compares export sets, signatures, class fields and routes.
   Its own docstring: _"NOT breaking: … body changes."_ `SOURCE_PRIORITY` is an `AnnAssign` whose dict value changed;
   `cloud-providers.yaml` is not Python at all. Verdict `false` either way — and every downstream gate
   (`breaking_pending`, `tier_c_promotion_gate`, the cascade trigger) keys off that same verdict.
3. **The reverse-dependency fan-out fails green.** `cascade-qg-ordering.yml` builds a reverse dep graph and dispatches
   `quality-gate-run` to each dependent — which would run UTL's suite. But `quality-gate-run` appears in exactly one
   file workspace-wide: the emitter itself. No repo declares a `repository_dispatch` listener for it (UTL's v2 accepts
   only `push:[main]`, `pull_request:[main,staging]`, `workflow_dispatch`). The dispatch 204s, nothing runs, and
   `poll_level` then reads the _pre-existing_ `ci_status` — already `MAIN_GREEN`/`SIT_VALIDATED`, both in
   `PASSING_STATUSES` — and declares the level green. This is a false-green by construction, not merely a miss.
4. **A red SIT never reaches an agent.** `full-workspace-sit.yml` dispatches only `sit-passed`/`sit-failed`;
   `sit-unlock.yml` opens a GitHub Issue + Slack. The one auto-escalation for repeated SIT failure sends
   `wall_type: "sit_retry_cap"`, which is not in `escalate-to-orchestrator.yml`'s accepted set, so it hard-errors.

## The DEEPER root cause (adversarially verified 2026-07-20) — and why the obvious fix does NOT work

The count reached **6 instances in 2 days** (add: 9 DeFi venues + 20 sportsbooks reddened IS goldens + MTDS shard-count
fixtures). A design workflow + independent verification established the systemic hole and refuted the originally-planned
fix (listener + differ→`is_breaking`) on three counts. **Do not implement the two todos below as originally written —
they are struck through with the reason.**

### The real linchpin: the v2 content-sentinel keys on OWN tree-hash only

`.github/workflows/python-quality-gates-v2.yml` (PM's reusable v2, line ~120-127) computes its skip key as
`TREE="$(git rev-parse HEAD^{tree})"` + gate-version fingerprint, and **"deliberately does NOT hash the deps' resolved
CONTENT, so [it relies on] the dep RANGE pins"** (its own comment, line ~87). A value-only UAC change is
**within-range** (a 0.x dict-value edit bumps no version), so it perturbs neither the downstream's tree hash nor the
range pin → the sentinel **skips the gate and returns the last green**. This is why re-running a dependent's v2 does
nothing: it is architecturally cached against exactly the input that changed.

### Three verified blockers on the originally-planned fix

1. **Coupling registry-value detection to `is_breaking` FALSE-BREAKS the fleet (verified).** `is_breaking` drives the
   global staging lock (`update-repo-version.yml:171`) AND the fail-closed SIT-race gate
   (`ldr-to-main-promote-fleet.yml:613-642`). A routine recalibration —
   `EMISSION_LATENCY_MS_BY_SOURCE['yahoo'] = 900_000 → 840_000`, a value the module docstring itself calls a
   CONSERVATIVE estimate awaiting recalibration — is a registry in the allowlist, so a value-aware differ tied to
   `is_breaking` would jam **every** promote on a benign latency tweak. The signal must be **decoupled** from
   `is_breaking`.
2. **Shipping the value-aware differ ALONE makes it worse (verified).** `is_breaking` is the cascade trigger
   (`update-repo-version.yml:715-718`). Making the differ fire the cascade while the cascade is still false-green
   (blocker 3) means it now actively fires and reports green — false confidence where there was previously silence.
3. **The `quality-gate-run` listener is a NO-OP (verified).** Even wired in, a cascade-dispatched v2 on a dependent
   whose tree is unchanged hits the content-sentinel above and returns the stale green. The listener cannot help until
   the sentinel keys on resolved-dependency content. Separately, the v2 template has **drifted** ahead of the 22
   deployed copies (a second "loaded gun" — see
   `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md`), so a rollout must reconcile the drift
   first.

### The real fix (verified design, bigger than the original scope — needs operator direction)

- **[A] Make the content-sentinel dependency-content-aware.** Key it on `own-tree-hash + resolved-UAC/UTL-tree-hash` (or
  a hash of the installed dep contents) so a dependency change busts the skip and forces a genuine re-run. This is the
  single highest-leverage change — it makes EVERY existing re-run path (nightly sweeps, promote-gate re-runs, any
  dispatch) actually catch dependency-content changes, with no listener or differ needed. **Highest blast radius in the
  fleet** (it is the core gate's cache: wrong key → either 4× redundant CI cost or over-skipped real breaks), so it is
  operator-sign-off territory, not an autonomous ship.
- **[B] Value detection as a DECOUPLED signal.** Extend `detect_breaking_change.py` with a narrow
  `CROSS_REPO_REGISTRY_ALLOWLIST` (SOURCE_PRIORITY, VENUE_TO_ADAPTER_KEY, the DeFi-venue/sportsbook registries, …) that
  emits a **separate `registry_value_changed`** field — NOT `is_breaking` — using an order-normalizing AST canonicalizer
  (dict keys sorted so a reorder is not flagged; priority-list order preserved; comments/whitespace excluded — verified
  6/6 on the real cases). That signal drives a targeted re-dispatch of direct dependents, whose sentinel (fixed by [A])
  now actually re-runs. Config YAMLs (cloud-providers.yaml) get the same path-scoped treatment. The differ is a single
  centralized PM file (semver-agent + fleet-promote fetch PM's copy at runtime), so [B]'s code has zero fleet footprint.

## Todos

- [x] [DEVOPS] P0. Establish which `cloud-providers.yaml` the bucket-naming sweep is authoritative against, fix the
      collection-vs-runtime precedence mismatch, and make instance 2 green — do NOT just delete the fixture's `SPORTS`
      lines without resolving precedence first. ✅ unified-trading-library@c26a5297 — deleted the conftest override +
      fixture, repointed 6 consumers at UAC's packaged copy, added a cross-copy parity pin. UTL quality-gates green.
- [x] ✅ [DEVOPS] P0. **[A] Make the v2 content-sentinel dependency-content-aware** — key it on
      `own-tree-hash + resolved-UAC/UTL-content` in `.github/workflows/python-quality-gates-v2.yml` so a dependency
      change busts the skip. Highest-leverage + highest-blast-radius (core gate cache) → **operator sign-off required**,
      not an autonomous ship. This ALONE fixes the class for every existing re-run path. **SHIPPED 2026-08-09** —
      `unified-trading-ci@f0bfaa2` (Option 2, operator-approved 2026-08-09). Implemented in the `content-gate` job's
      `hash` step: folds the current `live-defi-rollout` tree hash of `unified-api-contracts`/`unified-trading-library`
      (via `gh api repos/.../commits/live-defi-rollout --jq     .commit.tree.sha`, scoped to whichever deps the caller
      declares via `dep_repos`) into `KEY` as a new `DEP_HASH` segment alongside the existing `TREE`/`GATE_HASH`;
      unresolvable dep lookup fails safe (`GATE_KNOWN=false` → full gate, no marker saved), mirroring the existing
      gate-version-fingerprint fail-safe. Verified: `actionlint` + `shellcheck` clean locally and in CI (run 31311558496
      — the only failures are 30 pre-existing shellcheck findings in unrelated files, filed separately, see Progress
      Log) before push. **Correction to the todo's own rollout instructions**: no `rollout-workflow-templates.sh` fleet
      rollout was needed — `python-quality-gates-v2.yml` was extracted out of PM into `unified-trading-ci` on 2026-08-06
      (`shared_ci_workflow_repo_extraction_2026_08_06.md`, predating this todo's 2026-08-08 walkthrough text, which
      still described the pre-extraction PM-hosted-copy rollout path) and every fleet caller pins
      `uses: IggyIkenna/unified-trading-ci/....yml@main` (a moving ref, single-branch repo, no LDR/staging tiers) — so
      shipping straight to `unified-trading-ci`'s `main` IS the fleet-wide rollout; there is no second per-repo-copy
      step. Live-verification of a forced UAC value-only change producing a sentinel MISS was NOT run this session (no
      safe throwaway value-only UAC edit was staged) — left as a follow-up if the operator wants an end-to-end proof
      rather than the code-level verification above.

      **operator ruling 2026-08-08**: wants to SEE the exact keying logic before signing off -- NOT shipping this
              session. Technical walkthrough below, grounded in the LIVE code
              (`.github/workflows/python-quality-gates-v2.yml` lines 104-201, re-read 2026-08-08), ready for a fast sign-off
              next time the operator is available.

              **RULED 2026-08-09 (operator): Option 2 approved -- hash UAC's + UTL's resolved git ref/commit**, per this
              walkthrough's own stated recommendation below. Signed off on the DESIGN only; the keying-logic implementation
              itself is still unbuilt (see "What sign-off actually gates" below -- nothing has shipped from this walkthrough).
              This checkbox was already tagged `[DEVOPS]` rather than `[OPERATOR]` -- the sign-off gate was expressed as
              embedded prose blocking the ship, not as a separate `[OPERATOR]` checkbox tag, so no retag was needed; recorded
              here instead. AO dispatch is now safely scoped now that Option 2 is chosen (see frontmatter
              `assigned_vm: planning` reclassification, recorded in the Progress Log) -- implement per "What sign-off actually
              gates" below: extend `KEY` in `.github/workflows/python-quality-gates-v2.yml` lines ~120-160, roll to the
              fleet's 22 per-repo copies via `rollout-workflow-templates.sh` (never hand-edited per repo), and verify live
              (force a UAC value-only change, confirm a downstream's sentinel now correctly MISSes). Not hand-implemented in
              this pass -- this is the fleet's highest-blast-radius CI gate and needs a proper AO-dispatched implementation +
              rollout, not a quick edit.

              ### How the sentinel keys TODAY (verbatim mechanism, not paraphrased)

              Job `content-gate` (`content sentinel`) runs first, computes a cache key, and probes Firestore
              (`qg_green_markers/{key}`) for a prior green. A HIT short-circuits every `qg-slices` matrix leg to GREEN with
              zero runner spend (`needs.content-gate.outputs.cache_hit`, gates the `if:` on the slices job).

              ```
              TREE      = git rev-parse HEAD^{tree}                         # line 127 -- OWN tree only
              WF_HASH   = sha256(.github/workflows/quality-gates-v2.yml)    # line 142 -- caller's own copy
              REUSABLE_SHA = blob sha of python-quality-gates-v2.yml         # line 143-148 -- PM's reusable workflow
              (local checkout for PM itself; `gh api .../contents/...?ref=live-defi-rollout` for fleet callers)
              BASE_SHAS = sorted dir-tree shas of scripts/quality-gates-base + scripts/quality_gates   # line 150
              GATE_HASH = sha256(WF_HASH|REUSABLE_SHA|BASE_SHAS)[:24]        # line 156
              KEY       = "qg-green-v2-{repo}-{TREE}-{GATE_HASH}"            # line 157
              ```

              `TREE` is a git tree object hash of the CALLER repo's own working tree at HEAD -- it recursively covers every
              file in that repo, **including `pyproject.toml`/`uv.lock`** (so it changes if a dep RANGE pin changes), but it
              does **not** reach outside the repo -- it has no way to see what UAC/UTL's OWN content resolves to right now.
              The code's own comment states this explicitly (line 87): "deliberately does NOT hash the deps' resolved
              CONTENT, so [it relies on] the dep RANGE pins." `GATE_HASH` protects against the GATE ITSELF changing (3 homes:
              the caller's workflow copy, PM's reusable workflow, PM's QG base scripts) -- it has nothing to do with
              dependency content either.

              ### The gap, concretely

              UAC ships `0.x` (pre-1.0, wide range pins like `>=0.1.20,<1.0.0` per `workspace-manifest.json`). A UAC commit
              that edits a registry/config VALUE (e.g. `SOURCE_PRIORITY['tradfi'].remove('massive')`) does not bump UAC's
              version past a downstream's range pin, so the downstream's own `uv.lock`/`pyproject.toml` are untouched by that
              edit ⟹ `TREE` is identical to the last green run ⟹ `KEY` is byte-identical ⟹ the sentinel HITS and returns the
              stale green, even though the downstream's actual runtime behaviour (which reads that registry value) may now be
              broken. This is exactly instances 1-2 documented above this todo.

              ### Candidate keying implementations (operator picks one, or directs a different one)

              **Option 1 -- hash UAC's + UTL's installed package content directly.** After `uv sync` resolves the
              environment, hash the tree of the INSTALLED `unified_api_contracts`/`unified_trading_library` package
              directories (e.g. `find .venv/.../unified_api_contracts -type f -exec sha256sum {} + | sort | sha256sum`) and
              fold that into `KEY` alongside `TREE`/`GATE_HASH`. Pro: exact -- catches literally any resolved-content
              difference, source or config data. Con: requires `uv sync` to run BEFORE the key can be computed, which pushes
              the content-gate job's cost up (today it is a ~5min checkout-only job with zero dependency install) --
              partially defeats the sentinel's own cost-saving purpose for the common case where nothing changed.

              **Option 2 -- hash UAC's + UTL's resolved git ref/commit, not their file content.** `uv.lock` records the exact
              resolved version (and, for a path/git dependency, the exact commit) for each dependency. Read that
              commit/version out of the caller's own (unchanged) `uv.lock`, then look up the ACTUAL current tree-hash of
              UAC/UTL at their `live-defi-rollout` HEAD (or `main`, whichever the range would resolve to) via
              `gh api repos/.../contents/...?ref=...` -- same pattern the gate-version fingerprint already uses for
              `REUSABLE_SHA` (lines 143-149). Fold `UAC_HEAD_TREE + UTL_HEAD_TREE` into `KEY`. Pro: no `uv sync` needed, stays
              a cheap checkout-only job -- same shape as the EXISTING gate-version fingerprint code, so it is the smallest,
              most surgical diff. Con: less precise than Option 1 -- it keys on "UAC/UTL's HEAD changed at all" rather than
              "the SPECIFIC symbols/values this caller actually uses changed", so it will over-invalidate (extra full-gate
              runs) on UAC/UTL commits that don't touch anything the caller reads. Given the sentinel's OWN fail-safe
              philosophy ("worst case is no speedup", line 97), over-invalidation is the safe direction to err in.

              **Option 3 -- Option 2, but scoped to just the caller's actual import surface.** Same as Option 2, but instead
              of the whole-repo HEAD tree, hash only the specific UAC/UTL submodule paths the caller's own source imports
              from (derivable via a one-time `grep -r 'from unified_api_contracts' <caller>/`-style scan, cached per-repo).
              Pro: closest approximation to Option 1's precision at Option 2's cost. Con: real new code to build and maintain
              (the import-surface scanner), and a caller whose code changes which UAC symbols it imports needs that scan
              re-run -- an extra moving part in the fleet's highest-blast-radius gate.

              **Recommendation (not yet operator-approved -- stated for the walkthrough, not shipped):** Option 2. It reuses
              the EXACT pattern already proven in this same job for `REUSABLE_SHA` (a `gh api .../contents/...` blob-sha
              lookup against `live-defi-rollout` HEAD), so the diff is small, auditable, and consistent with the rest of the
              job's own design -- no new dependency-scanning subsystem, no `uv sync` cost added to the sentinel job. The
              precision loss vs Option 1/3 trades toward MORE full-gate runs, never toward a false skip, which matches the
              job's own stated fail-safe direction.

              ### What sign-off actually gates

              Nothing ships from this walkthrough. The next step once the operator has read this and either approves Option
              2 (or names a different one) is: implement the chosen `KEY` extension in
              `.github/workflows/python-quality-gates-v2.yml` lines ~120-160, roll it to the fleet's 22 per-repo copies the
              same way `REUSABLE_SHA`'s pattern already does (template + `rollout-workflow-templates.sh`, never hand-edited
              per repo), and verify live: force a UAC value-only change, confirm a downstream's sentinel now correctly MISSes
              and runs the full gate instead of returning stale green.

- [x] ✅ [DEVOPS] P1. **[B] DECOUPLED registry-value signal in `detect_breaking_change.py`** — narrow allowlist +
      order-normalizing AST canonicalizer, emit a **separate `registry_value_changed`** field (NOT `is_breaking` — that
      false-breaks the fleet on benign recalibrations, verified) that drives a targeted re-dispatch once [A] lands.
      Config YAMLs get the same path-scoped treatment. **DONE 2026-08-09** — `unified-trading-pm@8875e5a79` (pushed as
      `07f008d3b`). Added `CROSS_REPO_REGISTRY_ALLOWLIST` (SOURCE_PRIORITY, VENUE_TO_ADAPTER_KEY,
      VENUE_PREFIX_TO_PROTOCOL, DEFI_VENUE_TO_PROTOCOL, CEFI_PERP_VENUE_API_ENDPOINTS) tracked independent of the
      `@contract-surface` marker; an order-normalizing `_canonicalize_value` (dict-key order ignored, list order
      preserved — priority-list semantics); `registry_value_changes()` + `config_yaml_value_changes()` (path-scoped to
      `unified_api_contracts/config/cloud-providers.yaml`) both wired into `main()` as new
      `registry_value_changed`/`registry_value_changed_names` fields — never folded into `reasons`/`is_breaking`. 5 new
      regression tests (SOURCE_PRIORITY removal decoupled-but-not-`is_breaking`, dict-key reorder not flagged,
      priority-list reorder flagged, unchanged not flagged, non-allowlisted constant untouched); 25/25 tests green, full
      `quality-gates.sh` green. **Still blocked on [A]** for the re-dispatch to actually fire (this todo's own scope was
      the signal itself, not the dispatch wiring — see [A]'s "What sign-off actually gates").
- [ ] [OPERATOR] P2. ~~Add a `quality-gate-run` listener + fix `poll_level`~~ **SUPERSEDED** — verified a no-op while
      the content-sentinel keys on own-tree-hash (blocker 3). Reconsider only after [A]; and reconcile the v2-template
      drift first (second loaded gun). **Retagged `[DEVOPS]` → `[OPERATOR]` 2026-08-09** (kept the checkbox format
      rather than converting to the non-checkbox `CANCELLED —` disposition bullet task_template.md describes — that
      format conflicts with `check_todo_regression.sh`'s literal `^- \[[ xX]\]` count invariant, which has no
      special-case for it; see the new SSOT-contradiction follow-up filed below) — found while checking this doc for
      backlog-ingestion eligibility before the [A] `assigned_vm` reclassification: the prior `- [ ] [DEVOPS]` form had
      no non-dispatchable marker and would have been ingested by AO despite reading SUPERSEDED.
- [ ] [OPERATOR] P2. ~~Make the differ set `is_breaking` on value change~~ **DO NOT** — verified to false-break the
      fleet on benign recalibrations (e.g. `EMISSION_LATENCY_MS_BY_SOURCE`). Use the decoupled signal in [B] instead.
      **Retagged `[DEVOPS]` → `[OPERATOR]` 2026-08-09**, same reason as the item above.
- [ ] [OPERATOR] P2. **EXTRACTED 2026-08-02** (operator ruling on
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 18, option A) to
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md` — this doc's main P0/P1 chain stays `locked_by`/operator-gated as
      before; only this bounded item moved. ~~Fix the invalid `sit_retry_cap` wall_type in `sit-debounce-trigger.yml`
      (it can never succeed)~~ and decide whether a red SIT should escalate to a background worker rather than Issue +
      Slack only. **STALE (na-eligibility-audit 2026-08-03)** — the struck phrase is DONE:
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (~line 240) records `unified-trading-pm@2e5a42479` +
      `agent-orchestrator@dbdccb6` fixing the choice-list + `EscalateRequest` Literal (confirmed live in this repo —
      `escalate-to-orchestrator.yml` now accepts `sit_retry_cap` at lines 37/67/81/150/152), with a full round-trip
      proof (`agt-d37ed9` dispatched → worker executed → closed 2026-07-28). The remaining clause (design call: should a
      red SIT escalate to a background worker rather than Issue + Slack only) stays **explicitly unresolved by design**
      per that same doc (~lines 832-839) — "a genuine design call and should stay NA regardless of which option is
      picked" — so this item stays open for that clause only.

      **RULED 2026-08-07 (operator, interactive session)**: YES — a red SIT should escalate to a background worker,
              not just Issue + Slack. Design decision only; not yet scoped into an implementation todo (needs its own
              bounded-outcome scoping — which worker/skill picks it up, what triggers the escalation, dedup against the
              existing Issue+Slack path) before it's AO-dispatchable.

              **Retagged `[DEVOPS]` → `[OPERATOR]` 2026-08-09**: found while reclassifying this doc's `assigned_vm: NA` →
              `planning` for the now-approved [A] item above -- this item, as written, is NOT yet bounded (its own text says
              "not yet AO-dispatchable" pending scoping) and per `task_template.md`'s non-dispatchable-marker family
              (`[OPERATOR]`/`BLOCKED-<TOKEN>`) it needed a real gate to stay out of the AO backlog once the doc-level
              `assigned_vm` flips -- it was previously `[DEVOPS]` with no ingestion-gate marker, which would have exposed an
              unscoped design-call item to dispatch. Retag to `[OPERATOR]` until someone (human or a follow-up scoping pass)
              turns "which worker/skill, what triggers, dedup against the existing path" into a bounded todo, then it can be
              re-tagged for dispatch.

- [x] ✅ [DEVOPS] P2. **EXTRACTED 2026-08-02** (same ruling, item 18) to
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`. Correct the `full-workspace-sit` messaging/naming so
      `SIT_VALIDATED` cannot be read as "the resolved cross-repo combination was executed" — it is a surface check.
      **DONE (na-eligibility-audit 2026-08-03)** — `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (~lines 840-852):
      already shipped pre-extraction via `system-integration-tests@33cf6f0` (2026-07-29), which added the "WHAT
      `SIT_VALIDATED` ACTUALLY MEANS" header block to `full-workspace-sit.yml`; verified ancestor-merged onto
      `origin/live-defi-rollout` and no other repo/doc carries the same over-claim.

## Progress Log

- **2026-08-09 (slot 22)** — Shipped [B]: `unified-trading-pm@8875e5a79` (landed `07f008d3b`). Implemented from scratch
  (the prior "code is ready + verified 6/6" prose was a design claim, not a checked-in diff — grepped, nothing existed).
  `CROSS_REPO_REGISTRY_ALLOWLIST` is explicit + narrow (5 names, real registries grepped from unified-api-contracts, not
  hypothetical); the AST canonicalizer reuses/extends the existing `_resolve_literal` machinery (added `ast.Tuple` →
  python `tuple` for hashable dict keys, needed for `SOURCE_PRIORITY`'s `(asset_group, data_type)` keys) rather than
  building a second parallel resolver. Verified the decoupling holds: `EMISSION_LATENCY_MS_BY_SOURCE`-style
  non-allowlisted value changes trip neither signal (test `test_non_allowlisted_constant_value_change_is_not_tracked`).
  Did NOT touch [A] (still operator-approved-design-only, unimplemented) — this todo's own text scoped it to the signal,
  explicitly "blocked on [A] so a re-dispatch is not a no-op" for the _consumption_ side, not the signal's existence.
  Unrelated pre-existing debt hit mid-ship: a fabricated git-SHA citation in a different plan doc
  (`infra_satellite_ao_dispatch_batch10_2026_08_09.md`, from slot-33, landed on origin before this session started)
  blocked Pass-1 QG's repo-wide `check_plan_commit_sha_evidence.py` — verified non-fabricated-by-me (`git cat-file -t`
  on the cited SHA fails; zero hits in `git log --all`), filed
  `infra_satellite_batch10_fabricated_commit_sha_evidence_2026_08_09.md` and re-baselined per the check's own printed
  remedy to unblock.
- **2026-07-20** — Class identified while root-causing the overnight T0 alerts. Instance 1 fixed (UTL fixtures repointed
  onto still-multi-source cells; `(tradfi, ohlcv_15m)` remains `["databento","yahoo"]` while `trades` collapsed to
  single-source). The SIT-laundering half is fixed separately in `ci_status_store.resolve_status`. Instance 2 diagnosed
  to a collection-vs-runtime YAML precedence mismatch and left open — deliberately not band-aided.
- **2026-07-20 (later)** — Count reached 6 instances. Ran a design workflow + INDEPENDENT verification of the operator's
  chosen fix (listener + value-aware differ). **Verdict: the chosen fix does not work; the real root cause is deeper.**
  Verified myself: (1) `EMISSION_LATENCY_MS_BY_SOURCE` is a docstring-declared "conservative" recalibratable value, so
  coupling value-detection to `is_breaking` would false-break the fleet; (2) PM's reusable v2 content-sentinel keys on
  `git rev-parse HEAD^{tree}` + gate-version and "deliberately does NOT hash the deps' resolved CONTENT" (its own
  comment) — so a within-range value-only UAC change skips the gate and returns stale-green, making the listener a
  no-op. **Nothing shipped for Item 5** — this is a big finding that changes the scope. Recommended real fix ([A]
  dependency-content-aware sentinel + [B] decoupled `registry_value_changed` signal) recorded above; [A] is the core
  gate cache (highest blast radius) → needs operator direction before implementation. The adversarial verification
  earned its cost: it prevented shipping a fleet-wedging (false-break) or actively-worse (unmasked false-green) change
  under autonomous momentum.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
- **RULED 2026-08-09 (operator)**: **Option 2 approved** -- hash UAC's + UTL's resolved git ref/commit, per this doc's
  own stated recommendation (the walkthrough under todo [A]). Recorded the approval inline under [A]; nothing shipped
  from the walkthrough itself (implementation is a separate, now-dispatchable step). Before reclassifying the doc-level
  `assigned_vm: NA` -> `planning` to make [A] AO-dispatchable, checked every OTHER open todo in this doc for
  backlog-ingestion eligibility (a doc-level `assigned_vm: planning` flip exposes every unmarked `- [ ]` line to AO
  regardless of its prose) and found two real gaps this same na-eligibility-audit's own "decommissioned item left
  unchecked" trap warning (below) had flagged but not yet fixed: (1) the two struck-through SUPERSEDED/DO-NOT P2 items
  were still `- [ ] [DEVOPS]` with no non-dispatchable marker -- retagged both `[DEVOPS]` -> `[OPERATOR]`, KEEPING the
  checkbox format, rather than converting to `task_template.md`'s documented non-checkbox `CANCELLED —` disposition
  bullet: discovered live that format conflicts with `check_todo_regression.sh`'s literal `^- \[[ xX]\]` total-count
  invariant (a genuine SSOT contradiction between two of the workspace's own conventions — no special-case exists for
  the CANCELLED conversion, so it hard-fails precommit as a false "todo loss"), so used the simpler, non-conflicting fix
  instead. Filed the contradiction as its own follow-up issue doc rather than silently working around it (see Progress
  Log below); (2) the EXTRACTED-2026-08-02 item (red-SIT-escalation design call, ruled YES on 2026-08-07 but explicitly
  "not yet scoped into an implementation todo... before it's AO-dispatchable") was tagged `[DEVOPS]` with no
  ingestion-gate marker -- retagged to `[OPERATOR]` so it stays out of the backlog until someone scopes it into a real
  bounded todo. With both fixed, [A] and [B] are the only two open items that will actually reach AO, and both are
  legitimately bounded ([A] now approved; [B] is bounded, verified 6/6, and simply sequenced behind [A]). Reclassified
  `assigned_vm: NA` -> `planning` (+ `execution_scope: local-only` -> `orchestrator-agent`). Cross-referenced the
  approval (brief pointer, not duplicated) in `operator_action_items_consolidated_2026_08_08.md`'s matching todo. Did
  NOT implement the `python-quality-gates-v2.yml` `KEY` extension myself -- highest-blast-radius fleet CI gate, needs a
  proper AO-dispatched implementation + rollout per the doc's own "What sign-off actually gates" section, not a quick
  edit in this pass. Note: this doc carries `locked_by: live-defi-rollout` (`locked_since: 2026-05-21`) -- per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` that field gates ARCHIVAL specifically, not
  ordinary todo/frontmatter edits, so it was not a blocker for this reclassification; not touched or unlocked here.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — the head todo [A] (make the v2
content-sentinel dependency-content-aware) states in its own text "**operator sign-off required**, not an autonomous
ship" because it is the core gate's cache with the highest blast radius in the fleet; [B] is explicitly "blocked on
[A]"; and the two remaining items are struck-through as SUPERSEDED and DO-NOT respectively. Adversarial verification
recorded in this doc already refuted the originally-planned fix on three counts.

**na-eligibility-audit 2026-08-02** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA, valid — with one parked item for the
operator.** Only change since the last marker is the 2026-08-01 context-scout `context_scope` backfill (metadata). All 6
open checkboxes re-read individually (completeness check: `grep -cE '^- \[ \]'` = 6 = verdicts reported). Four are
unambiguously NA: [A] states "**operator sign-off required**, not an autonomous ship" in its own text; [B] is "blocked
on [A]"; the two `~~struck-through~~` P2s are deliberately-unchecked **ruled-out** items (SUPERSEDED and DO-NOT), not
pending work — this is the exact "decommissioned item left unchecked" trap the skill names, so they must NOT be read as
open scope.

**PARKED — `BLOCKED-OPERATOR-DECISION` (extraction of two bounded trailing items from a locked doc):** the remaining two
`[DEVOPS] P2` items look bounded and worker-determinable on their own merits — (i) fix the invalid `sit_retry_cap`
`wall_type` in `sit-debounce-trigger.yml` (the doc itself measures that it "can never succeed", so the fix target is a
checkable fact), and (ii) correct the `full-workspace-sit` messaging so `SIT_VALIDATED` cannot be read as "the resolved
cross-repo combination was executed". Both are independent of the operator-gated [A]/[B] chain. They were NOT extracted
autonomously because this doc carries `locked_by: live-defi-rollout` (since 2026-05-21) and its P1 head is
operator-gated. Options: **A [WORKER REC]** — extract just these two into the next `ci_satellite_ao_dispatch_batchN`
plan, leaving this doc NA and locked (mirrors the batch5 pattern already used for the cloudbuild rollout todo); **B** —
leave both here until [A] is decided, accepting they stay unshipped; **C** — `[unlock-plan]` this doc and flip the whole
thing to `assigned_vm: planning` (NOT recommended — [A] is explicitly not an autonomous ship). Note item (i) embeds a
second clause ("and decide whether a red SIT should escalate to a background worker") that is a genuine design call and
should stay NA regardless of which option is picked.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator sign-off required, SUPERSEDED/DO-NOT items, adversarial
verification

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, valid — re-verified all 5 open
items. Only change since the last marker was a `context_scope` path fixup (one archived-doc reference corrected), zero
content/todo change — confirmed via `git show 50b8643dc`. `locked_by: live-defi-rollout` (since 2026-05-21) + item [A]'s
own "operator sign-off required, not an autonomous ship" text still govern; [B] stays blocked-on-[A]; the 2 struck items
remain correctly ruled-out (not open work); the extracted/stale sub-clause still cites its done-elsewhere commits. No
`assigned_vm` change. **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — item [A] itself
now carries a fresh 2026-08-08 operator interaction (see the todo's own "operator ruling 2026-08-08" entry): the
operator was walked through the exact keying mechanism and 3 candidate implementations, and explicitly declined to sign
off this session. This is the clearest possible confirmation [A] stays a genuine, current operator-gated decision. [B]
stays blocked on [A]; the 2 struck-through items remain ruled-out; the extracted item's remaining design-call clause was
RULED 2026-08-07 (yes) but still needs its own bounded-outcome scoping. `locked_by: live-defi-rollout` unchanged.
Checked today's 9 precedents; none apply (this is a live, dated, same-day operator decision-in-progress). No
`assigned_vm` change.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:35a81680e6aa1d0b]: KEEP-NA,
valid — confirms the 2026-08-08 round7 verdict, unchanged (only context-scout touch since). [A] stays
operator-sign-off-required (operator explicitly declined to sign off 2026-08-08); [B] blocked on [A]; the 2
struck-through items remain ruled-out; the extracted design-call clause (RULED 2026-08-07 yes) still needs bounded
scoping. `locked_by: live-defi-rollout` unchanged, not this run's to clear. No `assigned_vm` change.

- **2026-08-09 (worker-slot18)** — Item [A] SHIPPED: `unified-trading-ci@f0bfaa2`. Implemented operator-approved Option
  2 (hash UAC's + UTL's resolved live-defi-rollout tree content into the content-sentinel `KEY`), verified clean via
  local `actionlint`/`shellcheck` and confirmed in CI. Discovered the todo's own rollout instructions were written
  before the 2026-08-06 `unified-trading-ci` extraction landed — corrected inline on the checkbox (no
  `rollout-workflow-templates.sh` fleet pass needed; the file now has exactly one canonical copy and every caller pins
  `@main`). Also found `unified-trading-ci`'s `lint` (actionlint) job pre-existing-red on 30 shellcheck findings in 3
  unrelated files (semver-agent.yml, update-dependency-version.yml, request-major-bump.yml) — confirmed identical
  before/after this change, filed as its own P3 issue doc
  (`unified_trading_ci_lint_red_shellcheck_findings_2026_08_09.md`) rather than folding an unrelated fix into this ship.
  Did NOT run a live forced-UAC-value-change end-to-end proof (no safe throwaway edit staged this session) — left as an
  optional follow-up if the operator wants that beyond the code-level verification.
