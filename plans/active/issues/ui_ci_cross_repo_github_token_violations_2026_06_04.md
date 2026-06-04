---
title:
  unified-trading-system-ui registry-drift CI job is stale vs the generator interface (token fixed; generator-args +
  UAC-install remain)
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
3. **[REMAINING — needs a UI slot]** The generator invocation is still stale: the job calls it with `--uac-root` and
   `--out`, but `generate_ui_reference_data.py` (last changed PM 2026-06-01) uses `parser.parse_args()` and accepts
   **only `--output-dir`** — it derives `workspace_root` from its own path and imports `unified_api_contracts`. So:
   - `--uac-root` / `--out` are unrecognized → `argparse` exits non-zero (the job fails at this step).
   - The job only runs `pip install pydantic`; it never installs UAC, so `import unified_api_contracts` would
     `ModuleNotFoundError` even if the args were right. The ci.yml registry-drift job was last touched 2026-05-03 — it
     predates the generator's current CLI.

## Why it matters

STEP 5.18 (the token check) is now green, which unblocks the UI repo's QG token gate (the thing that blocked the
tab-mirror rollout). But the registry-drift **GHA job itself** still fails at the generator step until issue 3 is fixed
— so the job has been red since the generator changed (2026-06-01), independent of tokens.

## Recommended decision

A **UI-capable slot** (can run the GHA job / has a dev environment) should rework the registry-drift job to match the
current generator interface:

- Install UAC (+ UTL) so `import unified_api_contracts` resolves (e.g. `uv pip install -e ../unified-api-contracts`).
- Call `generate_ui_reference_data.py` with its real flag (`--output-dir <tmp>`), or no args (defaults to
  `workspace_root/unified-api-contracts/openapi`), then diff against `lib/registry/ui-reference-data.json`.
- Verify the job goes green in GHA (cannot be verified locally — needs the GHA sibling-checkout context).

Also pre-existing + unrelated (noted, not fixed here): `codecov/codecov-action@v3` at ci.yml:40 is flagged by actionlint
as too old — bump to a current major.
