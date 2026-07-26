# UI alignment — generators and docs (SSOT)

**Purpose:** One place that lists how **unified-trading-system-ui** stays aligned with contracts, manifests, and
strategy documentation. Use this before adding any new “generator” or sync path so we do not end up with two sources of
truth.

**This file is the index.** Individual scripts keep their own docstrings; they point here for the full picture.

**Consolidated surface (2026-03):** Active workspace SSOT targets **one primary trading UI**
(`unified-trading-system-ui`) plus **deployment-ui** for deployment-focused flows, with APIs centered on
**unified-trading-api**, **deployment-api**, and **auth-api** (see `scripts/dev/ui-api-mapping.json`). Legacy UIs and
APIs that were removed from `workspace-manifest.json` — including **logs-dashboard-ui**, **live-health-monitor-ui**,
**odum-research-website**, and **batch-audit-api** — live under the workspace-root **`archive/`** directory for
reference only.

---

## When to re-run (not a one-off)

These generators are **repeatable**: run them again whenever their **inputs** change. There is no separate “migration”
mode.

| Trigger (examples)                                                                           | Regenerate                                                                                                           |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| UAC registry or enum changes, new venues, `VALID_*` constants                                | §1 `generate_ui_reference_data.py`                                                                                   |
| `unified_api_contracts.internal` enums / presets used by the script                          | §1                                                                                                                   |
| `UnifiedCloudConfig` or config schema extraction in the script                               | §1                                                                                                                   |
| `unified-trading-pm/scripts/dev/ui-api-mapping.json` stacks                                  | §1                                                                                                                   |
| `workspace-manifest.json`, `strategy-manifest.json`, data-flow manifest, deployment topology | §2 `generate_system_topology.py`                                                                                     |
| UIC OpenAPI or HTTP contract surface for the UI                                              | §3 OpenAPI / `uic-openapi-sync.yml`                                                                                  |
| `ARCHETYPE_CAPABILITY_REGISTRY`, venue/gap registries, capability graph nodes/edges          | §1a `generate_capability_manifest.py` + `generate_capability_verdict_matrix.py` — **MANUAL sync, no CI auto-PR yet** |

**CI automation (2026-03-23):** The `uac-registry-sync.yml` and `uic-openapi-sync.yml` workflow templates auto-create
PRs when UAC/UIC merge to main/staging. File paths corrected from `src/generated/` to `lib/registry/` and `lib/types/`.
A `registry-drift` CI job in the UI repo's `ci.yml` should be added to fail PRs if the checked-in JSON/TS drifts from
what the generators produce — this is the next automation step.

### §1 — `ui-reference-data.json` (full loop)

1. **Workspace:** Sibling repos `unified-api-contracts` and `unified-trading-library` checked out next to
   `unified-trading-pm` (standard workspace layout). Note: `unified-internal-contracts` is now
   `unified_api_contracts.internal` (sub-module of `unified-api-contracts`), `unified-config-interface` is now
   `unified_trading_library.config_interface`.
2. **Python path:** Imports need those packages on `PYTHONPATH` (repo roots that contain `unified_api_contracts`,
   `unified_trading_library`), **or** a venv where both are installed editable (e.g. after `setup-workspace` + `uv sync`
   in a consumer that lists them as path deps).
3. **Run** (from workspace root, adjust `PYTHONPATH` if needed):

   ```bash
   PYTHONPATH="unified-api-contracts:unified-trading-library" \
     python3 unified-trading-pm/scripts/openapi/generate_ui_reference_data.py
   ```

   Optional: `--output-dir PATH` (default writes `unified-api-contracts/openapi/ui-reference-data.json`).

4. **Commit in `unified-api-contracts`:** The canonical generated file lives under that repo’s `openapi/` directory.
5. **Copy into the UI repo** (checked-in duplicate the bundler reads):

   ```bash
   cp unified-api-contracts/openapi/ui-reference-data.json \
      unified-trading-system-ui/lib/registry/ui-reference-data.json
   ```

6. **`lib/registry/generated.ts`:** It **imports** the JSON. You do **not** need to edit it when only **values** inside
   existing keys change. If you add **new top-level sections** or new keys the UI must re-export, extend `generated.ts`
   (or add a consumer that reads `referenceData` directly).

7. **Quality gates:** `cd unified-trading-system-ui && bash scripts/quality-gates.sh` (and UAC QG if you changed that
   repo).

### §2 — `system-topology.json`

Same workspace root assumption. Run:

```bash
python3 unified-trading-pm/scripts/openapi/generate_system_topology.py
```

Default output: `unified-api-contracts/openapi/system-topology.json`. Re-run after manifest edits; consume from tooling
or future UI features (not the main `ui-reference-data.json` path).

---

## 1. Machine-generated JSON for UI registries (extend, do not duplicate)

| Output                   | Generator                                                                  | Default path                                           | UI consumption                                                                                                           |
| ------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `ui-reference-data.json` | `python3 unified-trading-pm/scripts/openapi/generate_ui_reference_data.py` | `unified-api-contracts/openapi/ui-reference-data.json` | Copy into `unified-trading-system-ui/lib/registry/ui-reference-data.json`. Typed accessors: `lib/registry/generated.ts`. |

**What it extracts:** UAC venue/instrument registries and enums (explicit list), UIC enums (dynamic `dir()` scan),
`UnifiedCloudConfig` field metadata, UAC validation constants (`VALID_*`), operational-mode / testing-stage presets,
`scripts/dev/ui-api-mapping.json` stacks.

**Rule:** If the UI needs new dropdowns or labels from **UAC/UIC/UCI**, add extraction to
**`generate_ui_reference_data.py`** and regenerate the JSON. Do **not** introduce a second Python script that repeats
the same registry/enum extraction for the UI.

**Requires:** Workspace checkout with `unified-api-contracts` and `unified-trading-library` importable (typically
workspace venv). Internal contracts are at `unified_api_contracts.internal`, config interface is at
`unified_trading_library.config_interface`.

### 1a — `capability-manifest.json` / `capability-verdict-matrix.json` — MANUAL sync, gap identified 2026-07-26

Unlike `ui-reference-data.json` (§1, automated via `uac-registry-sync.yml`) and `archetype_capability_manifest.json` →
`coverage.ts` (automated via `scripts/propagation/sync-archetype-capability-to-ui.sh`, wired into the UI's own
`quality-gates.sh`), these two files have **no automated propagation path**:

| Output                           | Generator (UAC-side canonical copy)                                                                                                         | UI bundled copy                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `capability-manifest.json`       | `unified-trading-pm/scripts/openapi/generate_capability_manifest.py` → `unified-api-contracts/openapi/capability-manifest.json`             | `unified-trading-system-ui/lib/registry/capability-manifest.json` |
| `capability-verdict-matrix.json` | `unified-trading-pm/scripts/openapi/generate_capability_verdict_matrix.py` → `unified-api-contracts/openapi/capability-verdict-matrix.json` | `unified-trading-system-ui/public/capability-verdict-matrix.json` |

**Current mechanism (manual only):** after regenerating in UAC, someone hand-copies both files into the UI repo and
commits (`chore(registry): sync capability-manifest + verdict-matrix — ...`). There is no `repository_dispatch` workflow
like `uac-registry-sync.yml` that opens this PR automatically.

**Drift detection exists but is weaker than it looks:**
`unified-trading-system-ui/tests/unit/wizard/parity-gates.test.ts` sha256-compares the bundled copies against
`../unified-api-contracts/openapi/...` — but it only fires when that sibling repo is actually checked out next to the UI
repo. That's true for an agent's `.tabs/<slot>/` workspace (so `quality-gates.sh` catches drift there) and would be true
of a future fleet-wide CI that checks out both repos, but is **NOT true of `unified-trading-system-ui`'s own standalone
GitHub Actions CI** (`.github/workflows/ci.yml`'s `test` job does a single-repo `actions/checkout` — no UAC sibling) —
so a stale bundled manifest can merge to `main` via ordinary UI CI undetected. The `registry-drift` job in that same
`ci.yml` only regenerates + diffs `ui-reference-data.json`; it does not cover `capability-manifest.json` /
`capability-verdict-matrix.json`.

**Confirmed live** (found while investigating
`plans/active/issues/defi_wizard_batch2_018_residual_findings_2026_07_26.md` finding 2): at the time of that
investigation the UI's bundled `capability-manifest.json` was stale by a full UAC regen
(`unified-api-contracts@13266bf8` vs the UI's last sync `a0105d9f`, six minutes older — 574/2428 vs the fresh 582/2762
nodes/edges) — i.e. the exact "a fix landing in UAC does not automatically reach the wizard UI" scenario. Manually
re-synced via `unified-trading-system-ui@bd527d83`.

**Why "just extend `registry-drift` like `ui-reference-data.json`" is NOT the smaller lift it looks like (found
2026-07-26 scoping the follow-up todo):** both generators reach past UAC — they live-probe OTHER services' own `.venv`s
via `_run_service_probe(workspace_root, repo, ...)` (`workspace_root / repo / ".venv" / "bin" / "python"`, a real built
venv, not just a pip-installed package):

- `generate_capability_manifest.py`'s `extract_service_registries()` probes **execution-service** (`execution_algo`
  nodes) and **features-service** (`feature_group` nodes). It fails SOFT — an unreachable `.venv` degrades that registry
  to a `gap_registry` node rather than raising — so it would still "run" in a UAC-only CI job. But the current committed
  manifest has REAL nodes from a full-workspace regen (21 `execution_algo` + 1 `feature_group`, confirmed 2026-07-26),
  so a CI job checking out only UAC/UTL would regenerate a manifest that's structurally _different by design_ every
  single run (real nodes → gap nodes) — a **permanent false-positive drift signal that would red-flag every future PR**,
  not a real check.
- `generate_capability_verdict_matrix.py`'s `_probe_engine_backed_archetypes()` probes **strategy-service** for
  `ARCHETYPE_ENGINE_REGISTRY` and — unlike the manifest's soft-fail — **hard-fails** (`raise RuntimeError`, "F48: ...
  refusing to fall back to a transcribed set") if that `.venv` is unreachable. A UAC-only CI job wouldn't produce a
  false diff here — it would just always **crash**.

So a correct CI drift-check for either file needs execution-service **and** features-service **and** strategy-service
checked out with real, built `.venv`s (uv-managed — a full `uv sync` per service, not a light `pip install -e`)
alongside UAC/UTL — a materially heavier CI job than `ui-reference-data.json`'s, and one this determination round did
not attempt to build blind (no fast local iteration loop against real GitHub Actions execution; shipping an untested
version risks the exact permanent-false-positive failure mode described above, a worse outcome than today's manual-only
gap). Tracked as a properly-rescoped follow-up todo in the same issue doc — size it for real CI iteration cycles, not a
same-pattern-as-§1 copy-paste.

---

## 2. System topology JSON (tooling / future UI; not the same as §1)

| Output                 | Generator                                                                | Default path                                         |
| ---------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------- |
| `system-topology.json` | `python3 unified-trading-pm/scripts/openapi/generate_system_topology.py` | `unified-api-contracts/openapi/system-topology.json` |

Aggregates `workspace-manifest.json`, `data-flow-manifest.json`, **`strategy-manifest.json`**, UI/API flow tests, DAG,
`ui-api-mapping.json`. Useful for diagrams and automation; **not** automatically bundled as the main UI registry (that
is §1).

---

## 3. OpenAPI / HTTP contracts

| Concern                              | Location                                                                                                                                                                   |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unified OpenAPI generation           | `unified-trading-pm/scripts/openapi/generate_unified_spec.py`, `generate-unified-openapi.sh`                                                                               |
| UI TypeScript types from UIC OpenAPI | GHA template `unified-trading-pm/scripts/workflow-templates/uic-openapi-sync.yml` → targets `unified-trading-system-ui` (`src/generated/api-types.ts` or path in template) |

OpenAPI sync is **separate** from `ui-reference-data.json` (domain registries vs HTTP schemas).

**`generate_unified_spec.py` (merged OpenAPI):** The script prepends every `SERVICE_REGISTRY` repo root to `PYTHONPATH`
before each subprocess extract, so sibling imports like `auth_api` resolve without a hand-built export. You still need
**internal libraries** on `PYTHONPATH` (or installed in the active interpreter) because each service imports
`unified_trading_library`, `unified_api_contracts`, etc. Example from workspace root:

```bash
LIBS="unified-api-contracts:unified-trading-library"
export PYTHONPATH="${LIBS}:${PYTHONPATH:-}"
python3 unified-trading-pm/scripts/openapi/generate_unified_spec.py
```

Note: `unified-config-interface`, `unified-cloud-interface`, and `unified-trading-library` are now consolidated into
`unified-trading-library` as `config_interface`, `cloud_interface`, and `events_interface` sub-modules respectively.

Default outputs: `unified-api-contracts/openapi/unified-trading-system.openapi.{json,yaml}`. Copy the JSON/YAML into
`unified-trading-system-ui/context/api-contracts/openapi/` when the UI bundles the merged contract.

---

## 4. Strategy manifest validation (PM; no UI artifact)

Scripts such as `scripts/validation/validate-strategy-manifest.py`,
`scripts/manifest/generate-strategy-instrument-matrix.py`, `check-strategy-instruments.py` — **validate or derive** PM
manifests. They do **not** replace Codex prose or the browser handbook.

**Codex SSOT for strategy meaning:** `unified-trading-pm/codex/09-strategy/README.md`, per-asset-class markdown,
`STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md`.

---

## 5. Human-maintained UI docs (intentionally not generated)

| Artifact                                                           | Repo                      | Notes                                                                                                                                                                              |
| ------------------------------------------------------------------ | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/MOCK_STATIC_BROWSER_AGENT_HANDBOOK.md`                       | unified-trading-system-ui | Long-form **browser-agent evaluation** spec; consolidates Codex `09-strategy/` into one file. **No committed generator** — edit in place when strategy docs or mock labels change. |
| `docs/MOCK_STATIC_EVALUATION_SPEC.md`                              | unified-trading-system-ui | Short maintainer pointer to the handbook.                                                                                                                                          |
| Mock fixtures (`lib/*-mock-data.ts`, `strategy-registry.ts`, etc.) | unified-trading-system-ui | Hand-maintained; should stay **consistent** with handbook + Codex.                                                                                                                 |

**Rule:** Do **not** add an ad-hoc generator under the UI repo or `/tmp` flows without updating **this** document. If
automation becomes worthwhile later, add a **single** optional step under `unified-trading-pm/scripts/openapi/` (or one
subcommand of the existing generator) and document it in §1 or a new subsection here — still one SSOT index.

---

## 6. Related PM / codex links

- `unified-trading-pm/codex/09-strategy/STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md` — catalog vs `strategy-service`
  exports
- `unified-trading-pm/strategy-manifest.json` — machine strategy list
- `unified-trading-pm/scripts/dev/ui-api-mapping.json` — service stacks for reference data
