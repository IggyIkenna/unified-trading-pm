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

- [ ] [AUDIT] P2. Walk each repo's `scripts/` (start with the heavy/stale concentrations: instruments-service,
      market-tick-data-service, deployment-service, e2e-testing). **Stamp the Phase-0 lifecycle marker
      (`Epic:`/`Lifecycle:`/`Delete-when:`) on each script in the same touch as you classify it.** Classify each: (a)
      LIVE one-off still needed; (b) RAN-ONCE-DONE → delete (Script-Homes: delete after prod-run + a GCS orphan-sweep
      shows 0 stale targets); (c) OUT-OF-SHAPE / divergent from current code (hardcoded buckets / pre-env-short paths /
      direct `google.cloud`/`boto3` / dead imports / references to deleted modules) → mark deprecated or delete; (d)
      RECURRING → should be a CLI subcommand (file the promotion). Land a results doc under `plans/audit/results/`.
      Target: all service repos.
- [ ] [AUDIT] P2. From the audit, produce the concrete delete / deprecate / CLI-promotion lists; execute the deletes
      carefully (never delete a script that still has live GCS targets — verify first). Target: per-repo.

## Phase 2 — ruff-lint pass on scripts/ [P2]

- [ ] [SCRIPT] P2. Add `scripts/` to the **ruff lint** pass in `base-service.sh` (lint-only — NOT basedpyright, NOT
      coverage). Decide ruff rule scope + ratchet-vs-hard from the Phase-1 findings (a fleet of messy one-offs will
      light up → likely a baselined ratchet that only goes DOWN, like the existing 5.94/5.95 ratchets). Repo:
      **unified-trading-pm** (`base-*.sh`) → fleet-live via the PM-sourced base scripts (no per-repo rollout).
      **Sequencing:** run AFTER Phase-1 deletes so the ratchet baseline isn't inflated by soon-to-be-deleted scripts.

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
