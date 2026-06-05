---
title:
  unified-trading-system-ui registry-drift CI job — RESOLVED (tokens/UIC/generator-args/py3.13/UTL/PM-checkout +
  registry refreshed from UAC main, pw:L2 ✓); GHA-green is the final confirmation
created: 2026-06-04
author: ikennaigboaka [slot-1·laptop]
source:
  - tab-mirror fleet rollout 2026-06-04 (the only repo that failed STEP 5.18 token-check during rollout)
  - unified-trading-system-ui/.github/workflows/ci.yml (registry-drift job)
  - unified-trading-pm/scripts/openapi/generate_ui_reference_data.py (current interface)
locked_by: live-defi-rollout
---

## What I found

The `registry-drift` job in `unified-trading-system-ui/.github/workflows/ci.yml` is stale relative to the current
`generate_ui_reference_data.py` interface. Three issues, two now fixed:

1. **[FIXED — UI@7a15b6b0, 2026-06-04]** Both cross-repo sibling checkouts used `token: ${{ secrets.GITHUB_TOKEN }}`
   (repo-scoped, can't read other repos) → flagged by QG STEP 5.18 (`check-workflow-tokens.py`). The UAC checkout now
   uses `secrets.GH_PAT`.
2. **[FIXED — UI@7a15b6b0]** The `Checkout UIC sibling repo` step (`IggyIkenna/unified-config-interface`) was
   **vestigial** — `generate_ui_reference_data.py` reads UIC enums from `unified_api_contracts.internal` (an import),
   not from a `../unified-config-interface` checkout. Removed the step + the `--uic-root` flag. (The repo still exists
   on GitHub but this job never reads it.)
3. **[FIXED — UI@4cc69d85, 2026-06-04]** The generator invocation was stale: the job called it with `--uac-root` /
   `--out`, but `generate_ui_reference_data.py` (PM, current) uses `parser.parse_args()` and accepts **only
   `--output-dir`** (derives `workspace_root` from its own path; writes `<output-dir>/ui-reference-data.json`). It also
   only `pip install pydantic` (never UAC) on py3.12, but the generator imports `unified_api_contracts` AND
   `unified_trading_library` (for `config_schemas`), both `requires-python >=3.13`. Reworked the job: **py3.13**,
   **checkout + `pip install -e` both UAC and UTL**, call with **`--output-dir /tmp/freshreg`**, diff
   `/tmp/freshreg/ui-reference-data.json`. Verified locally: the generator runs clean with `--output-dir` and emits the
   455 KB `ui-reference-data.json`.

4. **[FIXED — UI@c1793688, 2026-06-04]** The job never checked out **PM** (where the generator lives), so
   `../unified-trading-pm/...` was file-not-found in CI — the job couldn't even invoke the generator. Added a PM sibling
   checkout (GH_PAT). PM's generator is byte-identical main↔LDR, so the `main` checkout is correct.

## RESOLVED — registry CONTENT refreshed (UI@c1793688)

The committed `lib/registry/ui-reference-data.json` was substantially stale vs UAC (15 keys: `strategy_registry`,
`client_registry`, `venue_data_availability`, `config_schemas`, …) — drifting since the job broke 2026-06-01.
Regenerated **CI-faithfully** and committed (8907+/2116-):

- Built an isolated py3.13 env with **UAC main + UTL main** (the exact refs CI checks out), via detached worktrees at
  those refs. Verified the generator's aux-source files (`openapi/config-registry.json`, `system-topology.json`) and
  PM's generator are **identical main↔LDR**, so the main-regen == what CI produces (the only main-vs-LDR delta was
  `uac_enums`/`registries`, both import-driven and correctly taken from main).
- **Playwright gate satisfied**: `npx playwright test --project=chromium tests/smoke/` → **1 passed (43.1s)**.
  regression: `tests/smoke/data-status-pending-backfill.smoke.spec.ts` + the registry-drift CI job itself.

**Final confirmation pending = the GHA run**: this is the one thing that can only be proven in CI. Generated
CI-faithfully, so the registry-drift job should now go green on the next UI PR; if any residual diff appears it'll be a
minor env nuance to iterate on the GHA run. Issue is otherwise fully resolved — archive once the GHA run is green.

Pre-existing + unrelated (still open, not fixed here): `codecov/codecov-action@v3` at ci.yml:40 is flagged by actionlint
as too old — bump to a current major.
