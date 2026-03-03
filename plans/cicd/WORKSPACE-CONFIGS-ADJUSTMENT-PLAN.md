# Workspace Configs Adjustment Plan

**Goal:** Align workspace names and repo blocks with the canonical dependency matrix and current repo set. Fix wrong repo names, add new repos from the matrix, and make the setup script the single source of truth.

**References:**

- `.cursor/workspace-configs/` — setup scripts and `*.code-workspace` files
- `.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json` — canonical repo list and DAG
- `.cursor/rules/parallel-agent-execution.mdc` — workspace shortcuts and epic mapping

---

## 1. Current vs canonical

### 1.1 Repo name fix (blocking)

| Current in some workspaces | Canonical (matrix + codebase)       | Action             |
| -------------------------- | ----------------------------------- | ------------------ |
| `unified-order-interface`  | `unified-trade-execution-interface` | Replace everywhere |

**Affected assets:**

- `workspace-complete.code-workspace` (folders + extraPaths)
- `workspace-trading.code-workspace` (folders + extraPaths)
- `workspace-libraries.code-workspace` (folders + extraPaths)

**Script:** `create-workspace-files.sh` already uses `unified-trade-execution-interface` in heredocs. The generated `.code-workspace` files on disk were likely edited manually and still reference `unified-order-interface`. Regenerating from the script will fix this for script-generated content; any hand-edited JSON must be updated too.

### 1.2 Repos in dependency matrix not in workspace script

From `DEPENDENCY-MATRIX-CANONICAL.json`:

| Repo                               | In create-workspace-files.sh? | In which workspace(s)?                                                  |
| ---------------------------------- | ----------------------------- | ----------------------------------------------------------------------- |
| `api-contracts`                    | No                            | Add to **complete**; consider **libraries** (instruments-service dep)   |
| `matching-engine-library`          | No                            | Add to **libraries**, **trading**, **complete** (execution-service dep) |
| `unified-defi-execution-interface` | No                            | Add to **libraries**, **trading**, **complete** (execution-service dep) |
| `unified-ml-interface`             | No                            | Add to **libraries**, **ml**, **complete** (strategy, ml-training deps) |

### 1.3 Repos in script/matrix that are “extra” (no matrix entry)

These are valid repos to keep in workspaces but are not in the matrix (or are referenced only as deps):

- `market-tick-data-handler` — referenced by execution-service in matrix; keep in data-pipeline, trading, full-pipeline, complete.
- `market-data-processing-service` — referenced by risk-and-exposure-service; keep in data-pipeline, features, ml, trading, full-pipeline, complete.
- `features-delta-one-service` — in script only; keep if repo exists.
- `ml-inference-service` — in script only; keep if repo exists.
- `alerting-service` — in infrastructure workspace only; keep.
- UI repos, codex, deployment-v2/v3 — keep as today.

No renames needed for these; only ensure names are consistent and blocks match the intended use (see section 3).

---

## 2. Dependency-matrix summary (for workspace grouping)

**Topological order (simplified):**

- **Level 0:** unified-config-interface, unified-events-interface, api-contracts
- **Level 1:** unified-trading-services
- **Level 2:** unified-domain-client, matching-engine-library, execution-algo-library
- **Level 3:** unified-market-interface, unified-ml-interface
- **Level 4:** unified-trade-execution-interface, unified-defi-execution-interface
- **Level 5:** instruments-service, strategy-service, position-balance-monitor-service, risk-and-exposure-service, pnl-attribution-service, features-calendar, features-onchain, features-volatility, ml-training-service, execution-service

**Referenced but not top-level in matrix:** market-tick-data-handler, market-data-processing-service (treat as existing repos in workspace groups).

Use this to assign repos to **data**, **features**, **ml**, **trading**, **libraries**, **full-pipeline**, **complete**, and **infrastructure** so each workspace has the right deps for its theme.

---

## 3. Workspace-by-workspace changes

### 3.1 workspace-complete

- Replace `unified-order-interface` with `unified-trade-execution-interface` in folders and `cursorpyright.analysis.extraPaths`.
- Add from matrix (if not present): `api-contracts`, `matching-engine-library`, `unified-defi-execution-interface`, `unified-ml-interface`, `unified-domain-client` (already in script).
- Ensure extraPaths include every folder that has Python packages (same list as folders, minus .cursor and UIs if not needed for Python).
- Keep: all UIs, features-delta-one-service, ml-inference-service, deployment, codex, market-tick-data-handler, market-data-processing-service.

### 3.2 workspace-data-pipeline

- Ensure: unified-domain-client is included (instruments-service depends on it per matrix). Script already has unified-market-interface.
- Repos: .cursor, codex, deployment v2/v3, unified-trading-services, unified-events-interface, unified-config-interface, unified-domain-client, unified-market-interface, instruments-service, market-tick-data-handler, market-data-processing-service.
- No `unified-order-interface`; if any reference exists, use `unified-trade-execution-interface`.

### 3.3 workspace-features

- Add unified-domain-client (features-\* depend on it). Script already has market-tick, market-data-processing, unified-market-interface.
- Repos: foundation + unified-domain-client, unified-market-interface, instruments-service, market-tick-data-handler, market-data-processing-service, features-calendar, features-delta-one, features-volatility, features-onchain.
- No order/execution interface needed.

### 3.4 workspace-ml

- Add unified-domain-client, unified-ml-interface (ml-training-service depends on them per matrix).
- Repos: foundation + unified-domain-client, unified-ml-interface, market-tick-data-handler, market-data-processing-service, features-calendar, features-delta-one, features-volatility, features-onchain, ml-training-service, ml-inference-service.
- Update extraPaths to match.

### 3.5 workspace-trading

- Replace `unified-order-interface` with `unified-trade-execution-interface` in folders and extraPaths.
- Add from matrix: unified-domain-client, unified-market-interface (script already has trade-execution-interface and execution-algo-library), matching-engine-library, unified-defi-execution-interface (execution-service deps).
- Repos: foundation + unified-trade-execution-interface, execution-algo-library, matching-engine-library, unified-defi-execution-interface, unified-domain-client, unified-market-interface, instruments-service, market-tick-data-handler, market-data-processing-service, features-calendar, features-delta-one, strategy-service, execution-service, position-balance-monitor-service, risk-and-exposure-service, pnl-attribution-service.

### 3.6 workspace-libraries

- Replace `unified-order-interface` with `unified-trade-execution-interface`.
- Add: unified-ml-interface, matching-engine-library, unified-defi-execution-interface, api-contracts.
- Repos: .cursor, codex, deployment v2/v3, unified-trading-services, unified-events-interface, unified-config-interface, unified-trade-execution-interface, unified-market-interface, unified-ml-interface, unified-domain-client, execution-algo-library, matching-engine-library, unified-defi-execution-interface, api-contracts.
- extraPaths: same list (for Python packages).

### 3.7 workspace-full-pipeline

- Add unified-domain-client so strategy and downstream have UDS.
- No `unified-order-interface`; ensure naming is unified-trade-execution-interface if any reference is added later.
- Repos: foundation + instruments, market-tick-data-handler, market-data-processing-service, features-\*, ml-training, ml-inference, strategy-service, risk-and-exposure-service, position-balance-monitor-service (no execution-service in this workspace is acceptable; pipeline is data → features → ML → strategy/risk/position).

### 3.8 workspace-uis

- No change to repo names (no unified-order-interface).
- Keep: codex, deployment v2/v3, unified-trading-services, unified-config-interface, and all UI repos. Optional: unified-events-interface if UIs need it.

### 3.9 workspace-infrastructure

- No dependency-matrix repos; keep: .cursor, unified-trading-codex, unified-trading-deployment-v3, unified-trading-deployment-v3, alerting-service.
- No changes to repo names.

---

## 4. Implementation tasks

1. **Fix script `create-workspace-files.sh`**
   - Use only canonical names: `unified-trade-execution-interface` (never `unified-order-interface`).
   - Add to **workspace-complete** (and elsewhere as above): `api-contracts`, `matching-engine-library`, `unified-defi-execution-interface`, `unified-ml-interface`.
   - Add **unified-domain-client** to: data-pipeline, features, ml, full-pipeline (and trading/libraries/complete as already or newly specified).
   - For each workspace block, add the same entries to `cursorpyright.analysis.extraPaths` (and any other settings that list repo paths) so they stay in sync with `folders`.

2. **Regenerate all `.code-workspace` files**
   - Run: `bash .cursor/workspace-configs/create-workspace-files.sh` from the workspace root (script uses `WORKSPACE_ROOT` and writes into `CONFIG_DIR`).
   - Confirm path convention: script uses `../../repo-name` (two levels up from script dir). Ensure script is run from the repo root that contains all repos as siblings (e.g. `unified-trading-system-repos`).

3. **Fix any hand-edited JSON**
   - If any `.code-workspace` file is not fully generated by the script (e.g. workspace-complete was edited on disk), apply the same renames and additions there: `unified-order-interface` → `unified-trade-execution-interface`, and add missing repos/extraPaths as in section 3.

4. **Align docs and rules**
   - **`.cursor/rules/parallel-agent-execution.mdc`**
     - Update “Foundation repos” and any list that still says “unified-order-interface” or “order-interface” to `unified-trade-execution-interface`.
     - Optionally add a one-line note that workspace membership is defined by `create-workspace-files.sh` and aligned with `DEPENDENCY-MATRIX-CANONICAL.json`.
   - **`.cursor/workspace-configs/README.md`**
     - Replace “order-interface” with “trade-execution-interface” and mention that repo set is aligned with the dependency matrix.
   - **`.cursorrules` (workspace root)**
     - If it references workspace groups or “order interface”, use “unified-trade-execution-interface” and point to the dependency matrix for the canonical list.

5. **Optional: derive workspace blocks from matrix**
   - Add a small script or section in the plan that maps matrix repo names → workspace groups (data, features, ml, trading, libraries, full-pipeline, complete, infrastructure) so future matrix changes require updating only that mapping and re-running the generator. This can be a follow-up task.

---

## 5. Verification

- Grep for `unified-order-interface` under `.cursor/workspace-configs` and `.cursor/rules`: expect zero matches after changes.
- Grep for `unified-trade-execution-interface`: present in all workspaces that need execution/order interface (trading, libraries, complete).
- Open each `*.code-workspace` and confirm:
  - folders list has no typos and matches the intended repo set for that theme.
  - extraPaths includes every Python package root that is in folders.
- Run `create-workspace-files.sh` and diff output vs committed `.code-workspace` files (after implementing script changes) to avoid drift.

---

## 6. Summary table (target state)

| Workspace      | Repo count (approx) | Key additions / renames                                                                                                                      |
| -------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| complete       | 35+                 | unified-trade-execution-interface; + api-contracts, matching-engine-library, unified-defi-execution-interface, unified-ml-interface          |
| data-pipeline  | 11                  | unified-domain-client (if missing)                                                                                                           |
| features       | 15                  | unified-domain-client (if missing)                                                                                                           |
| ml             | 14                  | unified-domain-client, unified-ml-interface                                                                                                  |
| trading        | 20                  | unified-trade-execution-interface (rename); + unified-domain-client, matching-engine-library, unified-defi-execution-interface               |
| libraries      | 14                  | unified-trade-execution-interface (rename); + unified-ml-interface, matching-engine-library, unified-defi-execution-interface, api-contracts |
| full-pipeline  | 19                  | unified-domain-client (if missing)                                                                                                           |
| uis            | 14                  | No repo renames                                                                                                                              |
| infrastructure | 5                   | No changes                                                                                                                                   |

After implementation, workspace names and repo blocks will match the dependency matrix and the new repo set; `create-workspace-files.sh` will be the single source of truth for generated workspace definitions.
