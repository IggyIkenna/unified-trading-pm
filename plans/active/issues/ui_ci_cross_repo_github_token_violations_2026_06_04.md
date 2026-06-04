---
title:
  unified-trading-system-ui registry-drift CI job — mechanics FIXED (tokens/UIC/generator-args/py3.13/UTL); registry
  CONTENT regen remains (env-matched UAC main + playwright)
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

## REMAINING — registry CONTENT is stale (separate from the now-fixed mechanics)

With mechanics fixed, the job now runs — and correctly surfaces that **`lib/registry/ui-reference-data.json` is itself
stale** vs current UAC (~15 keys differ: `strategy_registry`, `client_registry`, `venue_data_availability`,
`config_schemas`, …). It's been drifting since the job broke (2026-06-01). This must be regenerated + committed, but
**not from this laptop**:

- **Env-match**: CI checks out UAC's **default branch (`main`)**, which is **diverged from `live-defi-rollout`** (main 4
  ahead / 17 behind LDR as of 2026-06-04). A laptop slot is on LDR, so its regen would NOT match CI's `main`-based regen
  → committing it would still show drift. The regen must come from the same UAC ref CI uses (the GHA job, or a
  `main`-pinned checkout + UTL + py3.13).
- **Playwright gate (HARD RULE)**: `lib/registry/ui-reference-data.json` feeds UI dropdowns / catalogues, so a
  regen-commit is a UI-data change → needs `pw:L2 ✓` + a regression spec per CLAUDE.md § "UI changes — playwright gate".

Owner: a UI-capable slot that can (a) regenerate from the CI-matching UAC ref and (b) run playwright. Once committed,
the registry-drift GHA job (mechanics already fixed) goes green.

Also pre-existing + unrelated (noted, not fixed here): `codecov/codecov-action@v3` at ci.yml:40 is flagged by actionlint
as too old — bump to a current major.
