---
doc_type: plan
title:
  uv binary drifted off the pinned 0.10.8 on the running VM fleet — per-repo setup.sh fails, lockfile-determinism at
  risk
created: 2026-06-22
source:
  - human-planning-vm workspace bootstrap (2026-06-22) — Phase 5 per-repo setup failed for all 25 repos
  - plans/archive/2026_06/uv_lockfile_determinism_2026_06_02.md (the pin SSOT, ARCHIVED)
  - scripts/setup.sh:387-401 (the broken bootstrap-uv fallback)
  - scripts/quality-gates-base/base-service.sh:297 + base-library.sh:167
locked_by: live-defi-rollout
priority: P2
status: active
summary: "The canonical workspace **uv pin is `0.10.8`** (set by `uv_lockfile_determinism_2026_06_02.md`, archived ✅; committed `uv.lock` files are `revision = 3`, the serialization 0.10.8 produces). But the..."
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

## What I found

The canonical workspace **uv pin is `0.10.8`** (set by `uv_lockfile_determinism_2026_06_02.md`, archived ✅; committed
`uv.lock` files are `revision = 3`, the serialization 0.10.8 produces). But the running VM fleet had **drifted to uv
0.11.x**:

| Host                                                    | uv before                       | uv after (this fix)      |
| ------------------------------------------------------- | ------------------------------- | ------------------------ |
| laptop (slot host)                                      | 0.10.8 ✅                       | 0.10.8                   |
| human-planning-vm (`i-0dd9812a96cdda5dc`)               | **0.11.21**                     | 0.10.8 ✅                |
| agent-orchestrator-vm / central (`i-0c9b283b31d6b5ca7`) | **0.11.15**                     | 0.10.8 ✅                |
| e2e-test-vm (`i-086e8787dddda52d6`)                     | **0.11.21**                     | 0.10.8 ✅                |
| Harsh laptop                                            | unknown (unreachable from here) | — TODO                   |
| stopped epic VMs (vm-defi/cefi/…)                       | unknown — re-drift on relaunch  | — covered by durable fix |

**Two concrete consequences of the drift:**

1. **Per-repo `scripts/setup.sh` fails on any drifted-uv box.** Its bootstrap-uv step (`scripts/setup.sh:395-401`) is:

   ```bash
   elif command -v uv && uv --version | grep -q '0\.10\.8'; then
       log_skip "uv 0.10.8 already installed (pinned)"
   else
       "$PYTHON_CMD" -m pip install "uv==0.10.8" --quiet 2>/dev/null   # <-- FAILS
   fi
   ```

   When uv is present-but-wrong-version, it falls to `$PYTHON_CMD -m pip install`, where `$PYTHON_CMD` is the
   **uv-managed CPython 3.13 which has no pip** → non-zero → `set -e` exits 1. This is exactly why human-planning-vm's
   bootstrap reported **"Failed: 25"** for per-repo setup. Even if pip existed, a pip-installed uv would not replace the
   active `~/.local/bin/uv` binary, so it would not actually realign.

2. **Lockfile-determinism risk.** `base-service.sh` does NOT enforce the uv version (just
   `command -v uv || pip install`), so QG runs against whatever uv is present. QG itself uses `uv sync --frozen` (no
   rewrite), but a `uv lock` run under 0.11.x can re-serialize the lock to a different `revision` than the committed
   `revision = 3` → silent churn + the FF-pull-cron dirtiness the pin plan exists to prevent.

`agent-orchestrator-vm`'s per-repo venvs "work" only because they were built **before** that box's uv drifted — not
because the drift is harmless.

## Why it matters

- A fresh workspace bootstrap or a `--force` re-setup is broken on every drifted box (medium-high: blocks bringing up a
  new human/worker box, as hit live on human-planning-vm 2026-06-22).
- Determinism: the whole reason for the pin is byte-identical `uv.lock` serialization. A fleet running mixed uv versions
  silently undermines it.
- Re-drift: whatever provisioned the VMs installed 0.11.x (not the pin). Binary realignment (below) fixes the running
  boxes but will recur on the next VM relaunch unless the **durable fix** lands.

## Recommended decision

**Keep the pin at 0.10.8** (do NOT bump to 0.11.x — that would force re-locking every repo `revision = 3 → N`, exactly
the churn the pin prevents). Align the fleet TO the pin.

### Already done (operational — by this issue's author, 2026-06-22)

- [x] [INFRA] P1. Realign uv → 0.10.8 on all reachable running boxes via the astral standalone installer
      (`curl -LsSf https://astral.sh/uv/0.10.8/install.sh | env UV_UNMANAGED_INSTALL=$HOME/.local/bin sh`):
      human-planning-vm, agent-orchestrator-vm (central), e2e-test-vm. Binary-swap only — running processes + existing
      venvs untouched. Laptop already 0.10.8. — verified `uv --version` == 0.10.8 on all four.

### Durable fix — needs a tracked rollout unit (coupled: template edit + fleet rollout + per-repo commit)

- [ ] [INFRA] P1. Fix the `scripts/setup.sh` bootstrap-uv fallback in the PM template
      (`unified-trading-pm/scripts/setup.sh`, the SSOT copied to all repos by
      `scripts/propagation/rollout-quality-gates-unified.py`). Replace the pip fallback with the astral installer so a
      drifted box self-realigns pip-free:
  ```bash
  elif command -v uv &>/dev/null && uv --version 2>&1 | grep -q '0\.10\.8'; then
      log_skip "uv 0.10.8 already installed (pinned)"
  elif command -v curl &>/dev/null; then
      # uv-managed CPython has no pip; a pip-installed uv wouldn't replace the active binary either.
      curl -LsSf "https://astral.sh/uv/0.10.8/install.sh" | env UV_UNMANAGED_INSTALL="$HOME/.local/bin" sh >/dev/null 2>&1
      hash -r
      log_ok "Installed/realigned uv 0.10.8 (pinned, astral installer)"
  else
      "$PYTHON_CMD" -m pip install "uv==0.10.8" --quiet 2>/dev/null || pip install "uv==0.10.8" --quiet 2>/dev/null
      log_ok "Installed uv 0.10.8 (pinned, pip fallback)"
  fi
  ```
- [ ] [INFRA] P2. Roll the fixed `setup.sh` out fleet-wide
      (`python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py`) and commit the updated
      `scripts/setup.sh` to **every repo's** `live-defi-rollout` in the same unit (the rollout is NOT done until all
      per-repo copies are committed + pushed — leaving them dirty jams the `slot-cron-ff-pull` cron). Target repos: all
      25 in `workspace-manifest.json`.
- [ ] [INFRA] P3. Move the `0.10.8` constant out of the 3 hardcoded sites (`setup.sh`, `base-service.sh:297`,
      `base-library.sh:167`) into `scripts/workspace/resolve-canonical-versions.py` so it is read, not duplicated (the
      deferred "Phase 1" from `uv_lockfile_determinism_2026_06_02.md`).
- [ ] [INFRA] P3. Add a uv-version drift-guard (warn) to `base-service.sh`/`base-library.sh` or
      `verify-slot-host-symmetry.sh` so a future drift surfaces loudly. Composes with the existing low-priority
      drift-guard note in `plans/epics/infrastructure_master.md`.
- [ ] [INFRA] P2. Realign uv → 0.10.8 on Harsh's laptop (run the astral one-liner above) + on every epic VM at next
      relaunch (until the durable P1+P2 setup.sh fix lands, a relaunched VM re-drifts).

### Separate finding surfaced during the same bootstrap (not uv-related)

- [ ] [INFRA] P2. human-planning-vm per-repo setup: 19/23 OK, 6 failures — `strategy-service` +
      `fund-administration-service` (+1 Tier-4) "Project editable install failed — check pyproject.toml/uv.lock";
      `unified-trading-system-ui` needs `pnpm` (`npm i -g pnpm`); `e2e-testing` + `system-integration-tests` cascade
      from strategy-service. Diagnose the editable-install failures (likely stale lock — `uv lock` — or a real dep
      conflict); these block local `quality-gates.sh` in those 6 repos only. `.venv-workspace` + the other 19 repos are
      fine.

---

## Update 2026-06-22 (session cont.) — human-planning-vm bring-up + root causes

### Operational fixes COMPLETED (human-planning-vm `i-0dd9812a96cdda5dc`)

- [x] [INFRA] P1. Full workspace bootstrap: 25 repos on `live-defi-rollout` + clean; `.venv-workspace` built; pnpm
      installed; UI setup green; FF-pull cron healthy (fixed: 21 root repos were cloned on `main`, + bootstrap
      `--rollout-first` churn left every repo dirty → cron skipped them; + a root-owned stale lock).
- [x] [INFRA] P1. Workspace git-detection bug: the bootstrap created the root `.code-workspace` as a SYMLINK →
      `.cursor/workspace-configs/...` whose folder paths are `../../<repo>`. Opened via the root symlink, VS Code/Cursor
      resolved `../../` above the workspace root → Source Control showed "no folders containing Git repositories".
      Replaced with a REGULAR root-relative file. (Durable fix below.)

### BIG FINDING — starlette cross-repo dep conflict (real fleet bug, NOT VM-specific) → operator decision

`unified-trading-library` pins **`starlette>=1.3.1,<2.0.0`** (on BOTH `main` and `live-defi-rollout`), but
`strategy-service` / `trading-agent-service` / `fund-administration-service` + the **canonical manifest** pin
**`starlette>=1.1.0,<1.3.0`**. A fresh `uv pip install -e .` of any of those services (they install UTL as an editable
sibling) is **unsatisfiable** → editable install FAILS on any fresh setup fleet-wide; `e2e-testing` +
`system-integration-tests` cascade from strategy-service. agent-orch-vm's working venvs only predate UTL's bump.

- [ ] [DEPS] P1. **Operator decision**: either lower UTL's starlette to `>=1.1.0,<1.3.0` (align to the canonical cap —
      what the version-aligner already wants) OR raise the canonical cap + re-pin all consumers to allow `>=1.3.1`. Do
      NOT unilaterally change the T0 lib. Repos: `unified-trading-library` + the 3 consumers.
- [ ] [DEPS] P2. After the pin decision, re-lock affected repos (uv 0.10.8) + re-verify editable install.

### Durable boot-script hardening — WRITTEN + VALIDATED, BLOCKED from landing (see version divergence below)

Validated locally on slot-3 (`bash -n` + `shellcheck -S error` clean + sed-rewrite verified); stashed as `git stash` msg
`boot-script-hardening-uv-pin-pnpm-branch-symlink-2026-06-22` on the slot-3 PM clone.

- [ ] [INFRA] P1. `scripts/workspace/workspace-bootstrap.sh`: (a) Phase 1 — enforce pinned uv `0.10.8` via the astral
      installer when the present uv differs (was `[SKIP] uv already installed`, letting 0.11.x ride); (b) Phase 1 —
      install pnpm (corepack → npm → sudo npm fallback) so the UI repo's setup.sh works; (c) after the clone loop —
      `git checkout live-defi-rollout` for every repo (git clone leaves them on the default `main`, which the FF-pull
      cron skips + causes cross-branch dep conflicts).
- [ ] [INFRA] P1. `scripts/workspace/setup-workspace-config-symlink.sh`: emit the root `.code-workspace` as a REGULAR
      file with root-relative paths (sed-rewrite `"../../X"`→`"X"`, `"../../"`→`"."`) instead of the
      symlink-to-cursor-configs (the git-detection bug above).
- [ ] [INFRA] P2. `scripts/setup.sh` astral-uv fallback (the per-repo fix above) — couples to the fleet rollout.

### PM version-promotion divergence — the blocker (operator/machinery)

`origin/live-defi-rollout` PM = **1.2.324**, `origin/main` = **1.2.325**; `main-backmerge-to-ldr.yml` runs green but
does NOT sync the bump (a ~30-file content delta exists main↔LDR). The local `quality-gates.sh` version-alignment gate
**HARD-blocks any PM commit** while this split exists (`--skip-version-alignment` is human-only), so the boot-script
fixes above cannot quickmerge. NOTE: this is the LOCAL QG gate being stricter than `assert_version_coherence.py` (which
treats VERSION_SPLIT as warn-only promotion lag).

- [x] [CICD] P1. Reconcile PM `main`↔`live-defi-rollout` — DONE via **merge-down, NOT force-sync**: main was taking live
      `[skip ci]` semver bumps every few min (PM→1.2.326, AO→0.40.0), so force-pushing the SSOT would revert real active
      bumps + risk the semver bump-rate circuit breaker. Merged `origin/main`→LDR (max-version manifest resolution,
      preserving both sides' bumps); main is now **0 commits ahead of LDR** (fully contained). The standing drain PR
      #498 was stale-CONFLICTING → close+reopen cleared it → now **MERGEABLE** (auto-merge armed).

### UPDATE — starlette conflict was a STALE-CLONE ARTIFACT, now RESOLVED (supersedes the BIG FINDING above)

On the current LDR, UTL pins `starlette>=1.1.0,<1.3.0` (aligned). The `>=1.3.1` was a prior CVE-fix floor that was
deliberately lowered (constraints.toml: "starlette 1.3.1 wraps included routers as `_IncludedRouter` (no `.path`) →
breaks route-introspection"). The earlier conflict was a stale UTL clone (pre +240-commit FF-pull). Verified:
`strategy-service` editable install now EXIT=0; all 6 previously-failing repos set up OK (0 failed). NO T0 change.

### ROOT BLOCKER of the LDR→main drain — PRE-EXISTING PM v2 failure (a prior autonomous session's incomplete work)

PR #498's only required check `quality-gates-v2` is **RED** (since before this session): the `QG slice (tests)` fails
because a prior autonomous run shipped a **59th archetype `TSMOM_BTC_CTA`** (CTA; commits `1f1b20413`/`236176168` —
"autonomous run COMPLETE … CTA archetype") to the registry but did NOT update PM's archetype-count tests, which still
assert **58**:

- `tests/unit/test_capability_verdict_matrix.py:83` `assert len(archetypes) == 58` → got 59
- `tests/unit/test_prospectus_generators.py:226` `Expected 58 … got 59`
- `tests/unit/test_capability_verdict_matrix.py:123` `test_f48_engineless_archetypes_are_not_registered` → the CTA
  archetype is **engineless but isn't `VOL_*`/`MARKET_MAKING*`** → F48 invariant violated. main's tests also expect 58,
  so the 59th would red main's v2 too. **This blocks ALL PM LDR→main promotion** (not just the boot-scripts) and
  predates this session.
- [ ] [STRATEGY] P1. **Strategy-owner decision** on `TSMOM_BTC_CTA`: engine-backed (register its engine → F48 passes) or
      spec-only-for-now (F48 must explicitly allowlist the CTA archetype as known-pending)? Then bump the 3
      archetype-count asserts 58→59. Do NOT blind-bump — the F48 failure may signal a real "archetype shipped without an
      engine" gap. Once v2 is green, PR #498 auto-merges and drains the boot-scripts + all stuck LDR content to main.
- [ ] [CICD] P2. Durable fix for the chronic version-split: make `main-backmerge-to-ldr` actually sync the `[skip ci]`
      manifest/version bumps down to LDR (today it "runs green" but leaves the split), so the local-only
      version-alignment gate stops perpetually blocking PM commits.

### UPDATE — archetype tests-slice FIXED (operator chose engine-backed); residual blocker = a separate typecheck cascade

- [x] [STRATEGY] P1. `TSMOM_BTC_CTA` is **engine-backed** — `TsmomBtcCtaEngine` is already in the live
      `ARCHETYPE_ENGINE_REGISTRY` (`strategy_service/engine/strategies/v2/factory.py`), shipped at
      `strategy-service@f5f00109` / `UAC@61ac3ad2` (per `citadel_paper_batch_live_reconciliation_2026_06_19.md`). The PM
      tests were merely stale: added `TSMOM_BTC_CTA` to `_FIXTURE_ENGINE_BACKED` + bumped the 3 counts 58→59
      (PM@`235774d59`). Verified: the 3 affected tests pass locally. **No strategy-service change needed.** v2's
      `QG slice (tests)` is now GREEN.
- [ ] [CICD] P1. **RESIDUAL BLOCKER (separate, pre-existing CI-infra incident)** — PR #498's v2 still RED on
      `QG slice (typecheck)`: ~**3082 `reportAny`/`reportUnknown*` errors** cascaded across MANY _existing_ PM scripts
      (`generate-cicd-diagram.py`, `fix_frontmatter.py`, `audit-library-imports.py`, …). This is the env-cascade the QG
      base scripts themselves document ("~thousands of spurious reportUnknown\*/reportAny … isn't resolved in .venv (the
      cascade root)") — a sibling dep not resolving in the CI typecheck venv → Unknown propagates everywhere; NOT real
      type errors, NOT annotatable, NOT introduced by this session. PM v2 was GREEN at 12:47 UTC and surfaced this at
      15:48 only because the stuck drain PR had never let v2 run on the full accumulated LDR content. Needs the PM-CI
      owner to diagnose the typecheck-venv dep resolution (the `--python` sibling editable-install path in
      `base-service.sh`). Until green, PR #498 (carrying boot-scripts + reconcile + archetype fix) cannot auto-merge —
      everything is staged on LDR (`be9fe5785`..`235774d59`) ready to drain the moment typecheck is green.
