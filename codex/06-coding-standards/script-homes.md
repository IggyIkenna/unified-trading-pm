---
scope: [engineer]
---

# Script Homes — where executables live (repo `scripts/` vs deployment-service vs e2e-testing)

**Codified 2026-06-10.** Canonical placement rule for every script / executable / one-off in the workspace. The service
**CLI** is the production run surface and **deployment-service** is the deploy/runtime surface (see
[cli-convention.md](cli-convention.md)); `scripts/`, `deployment-service`, and `e2e-testing` are the three homes for
everything that is _not_ production runtime. This doc is the SSOT for which goes where + the per-repo cleanup sweep.

> One-line essence (mirrored in `cursor-configs/CLAUDE.md` + `SUB_AGENT_MANDATORY_RULES.md`): **production verb →
> service CLI subcommand; provision/launch/schedule → deployment-service; cross-repo/smoke/e2e harness → e2e-testing;
> one-off single-repo op or dev/CI seeder/codegen → repo `scripts/` (one-offs are TEMPORARY).** Repo `scripts/` MUST
> obey repo SSOTs (resolve_bucket_name / UCI / env-short / UTC) — they rot silently because `scripts/` is outside the
> main gate.

---

## Decision tree (apply top-down; first match wins)

1. **Is it production runtime — the service doing its job (compute / fetch / validate / serve)?** → It is a **service
   CLI subcommand** (`<svc>/cli`, `--operation` / `--mode` / `--asset-group`) or API route — **NOT a script.** Batch and
   live are the same path ([Live = batch]); never fork a script for it. SSOT: [cli-convention.md](cli-convention.md).

2. **Does it build / provision / launch / schedule cloud runtime (VM, Cloud Run job, scheduler, image, terraform)?** →
   **deployment-service.** VM launchers live at `deployment-service/scripts/vm/launch-*-vm.sh`; recurring backfills run
   as scheduled jobs / VM launches; infra is terraform. The **launcher** lives here; the **compute logic** it invokes
   stays a service CLI subcommand (or, transitionally, a repo script the launcher calls — with a named successor to fold
   it into the CLI).

3. **Is it cross-repo / end-to-end test orchestration, or a CLI verification harness (smoke matrix, pipeline driver, e2e
   backfill driver)?** → **e2e-testing** (`e2e-testing/scripts/<domain>/`). Wire it to the primary-consumer service's QG
   (the **Peripheral Script Directories Under Primary-Consumer QG** rule / STEP 5.65) so import-rot is caught at PR
   time.

4. **Is it a one-off, single-repo operation tied to that repo's internals (a migration, a manifest backfill, codegen
   from this repo's own SSOT, a dev/CI mock seeder)?** → repo-level **`scripts/`** — subject to the sub-rules below.

## The homes

| Home                                          | Purpose                                                   | Examples                                                                                 | Lifecycle                                                                             |
| --------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **service repo `<svc>/cli`** (NOT `scripts/`) | production runtime verbs                                  | `features-service --operation calculate --mode batch --asset-group sports`               | permanent — the run surface                                                           |
| **deployment-service**                        | provision / launch / schedule cloud runtime               | `scripts/vm/launch-*-vm.sh`, Cloud Run jobs + schedulers, terraform                      | permanent infra                                                                       |
| **e2e-testing**                               | cross-repo e2e orchestration + CLI verification harnesses | `e2e-testing/scripts/<domain>/{run_pipeline_e2e,run_backfill,smoke_matrix}.py`           | permanent test tooling; under primary-consumer QG                                     |
| **service repo `scripts/`**                   | one-off single-repo ops + dev/CI seeders + codegen        | one-off migrations / manifest backfills (TEMPORARY), `seed_mock_data.py`, `regenerate_*` | one-offs are TEMPORARY (delete post-prod + orphan-clear); seeders/codegen may persist |

## Repo `scripts/` sub-rules

- **One-off migrations / backfills are TEMPORARY.** Delete once the operation has run in prod **and** a GCS orphan-sweep
  confirms no stale data depends on the script (see [migration_verification_orphan_safety] § orphan sweep). If the
  script encodes a _recurring_ need, it has a **named successor** (a service CLI subcommand / deployment-service job)
  and is retired the moment that lands — never left as a parallel path ([Delete deprecated code] + [Temporary state must
  have a named successor]).
- **Codegen / regeneration from the repo's own SSOT** (e.g. regenerate a schema YAML from the feature registry) may
  persist, but MUST be **deterministic + idempotent** (`sorted()` any set before render).
- **Dev / CI mock-data seeders** may persist (local + CI mock-mode only).
- **Every repo script MUST obey repo SSOTs** — `resolve_bucket_name()` (never hardcode `gs://` / a bucket name / a
  `PROJECT_ID`; env-short buckets), UCI `get_storage_client` / `get_secret_client` (never `from google.cloud import …` /
  `import boto3`), UTC datetimes, UAC types. `scripts/` is **not typechecked or covered by the main gate**, so a bypass
  rots silently — the peripheral-script QG wiring is the only guard, and only where it is wired.

## Anti-patterns (banned)

1. **Recurring operations as loose repo scripts.** A backfill/compute that runs on a schedule or VM belongs as a
   deployment-service launcher + a service CLI subcommand. (Incident 2026-06-10: `compute_sfi_progressive_only.py` is a
   repo script with a deployment-service launcher — transitional; retire when the `--source` CLI filter lands.)
2. **Scripts that bypass repo SSOTs** — hardcoded buckets / `gs://` f-strings, `from google.cloud import` / `boto3`,
   hardcoded `PROJECT_ID` / no env-short suffix. (Incident 2026-06-10: deleted `migrate_dash_separator_paths.py` +
   `backfill_fixture_features_manifest.py` hardcoded **pre-env-short** bucket names → pointed at empty legacy buckets.)
3. **Dead one-off migrations left in the tree.** A migration whose target data no longer exists in GCS is dead code —
   delete it (verify via orphan-sweep first). Tracking it only drags coverage and invites a mis-run against the wrong
   bucket. (Incident 2026-06-10: both deleted scripts targeted `0`-object buckets.)
4. **Production logic in a script.** If it is _how the service does its job_, it is a CLI subcommand, not a script.
5. **Smoke / e2e harnesses duplicated per-repo** when they belong cross-repo in e2e-testing.

## Per-repo cleanup sweep (an agent can run this across every repo at once)

For each repo, for each file under `scripts/`:

1. **Classify** by the decision tree → target home.
2. **Production-runtime** → fold into `<svc>/cli` as a subcommand; delete the script.
3. **Launcher / recurring** → move the launcher to `deployment-service/scripts/vm/`; compute logic → CLI subcommand.
4. **Cross-repo / smoke / e2e** → move to `e2e-testing/scripts/<domain>/` and wire to the primary-consumer service's QG
   (STEP 5.65).
5. **One-off migration / backfill** → check GCS for orphans / old-schema data the script targets:
   - **0 orphans + operation already ran in prod** → **delete** (boosts coverage, kills tech debt).
   - **orphans exist** → run it to completion ([Plans Run To Completion]) or migrate properly, **then** delete.
6. **Dev/CI seeder or codegen** → keep, but enforce repo conventions (resolve_bucket_name / UCI / env-short / UTC) +
   idempotent/deterministic.
7. Every relocation / deletion is a **tracked plan todo** ([Fanning out work = a tracked plan todo]) + Commit+Push+Flip.

## Composes with

- [cli-convention.md](cli-convention.md) — the production run surface (`--operation`/`--mode`/`--asset-group`).
- **Peripheral Script Directories Under Primary-Consumer QG** ([quality-gates.md](quality-gates.md) STEP 5.65) — wires
  `e2e-testing/scripts/` + repo `scripts/` into a service's QG so they don't import-rot.
- Bucket-name SSOT (`resolve_bucket_name`) + cloud-agnostic I/O (UCI `get_storage_client`/`get_secret_client`).
- **Delete deprecated code** + **Temporary state must have a named successor** — the one-off lifecycle.
- `plans/active/migration_verification_orphan_safety_2026_06_10.md` — the GCS orphan-sweep gate before deleting any
  migration script.
