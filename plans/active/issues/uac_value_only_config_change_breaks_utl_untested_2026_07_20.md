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
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [cross-repo, ci-cd, sit, breaking-detection, data-correctness, quality-gates]
related:
  [betfair_instrument_id_delimiter_cross_repo_2026_07_08.md, tradfi_canonical_path_migration_design_2026_07_19.md]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-07-20 while root-causing the overnight T0 FAILURE + CI REGRESSION alerts on unified-trading-library",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-21
resolved_by:
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
- [ ] [DEVOPS] P0. **[A] Make the v2 content-sentinel dependency-content-aware** — key it on
      `own-tree-hash + resolved-UAC/UTL-content` in `.github/workflows/python-quality-gates-v2.yml` so a dependency
      change busts the skip. Highest-leverage + highest-blast-radius (core gate cache) → **operator sign-off required**,
      not an autonomous ship. This ALONE fixes the class for every existing re-run path.
- [ ] [DEVOPS] P1. **[B] DECOUPLED registry-value signal in `detect_breaking_change.py`** — narrow allowlist +
      order-normalizing AST canonicalizer, emit a **separate `registry_value_changed`** field (NOT `is_breaking` — that
      false-breaks the fleet on benign recalibrations, verified) that drives a targeted re-dispatch once [A] lands.
      Config YAMLs get the same path-scoped treatment. Code is ready + verified 6/6; blocked on [A] so a re-dispatch is
      not a no-op.
- [ ] [DEVOPS] P2. ~~Add a `quality-gate-run` listener + fix `poll_level`~~ **SUPERSEDED** — verified a no-op while the
      content-sentinel keys on own-tree-hash (blocker 3). Reconsider only after [A]; and reconcile the v2-template drift
      first (second loaded gun).
- [ ] [DEVOPS] P2. ~~Make the differ set `is_breaking` on value change~~ **DO NOT** — verified to false-break the fleet
      on benign recalibrations (e.g. `EMISSION_LATENCY_MS_BY_SOURCE`). Use the decoupled signal in [B] instead.
- [ ] [DEVOPS] P2. Fix the invalid `sit_retry_cap` wall_type in `sit-debounce-trigger.yml` (it can never succeed) and
      decide whether a red SIT should escalate to a background worker rather than Issue + Slack only.
- [ ] [DEVOPS] P2. Correct the `full-workspace-sit` messaging/naming so `SIT_VALIDATED` cannot be read as "the resolved
      cross-repo combination was executed" — it is a surface check.

## Progress Log

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
