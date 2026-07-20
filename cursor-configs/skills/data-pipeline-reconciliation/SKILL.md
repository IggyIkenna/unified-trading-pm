---
name: data-pipeline-reconciliation
description:
  Reconcile one operator-given asset_group's data estate against the canonical target across the FOUR canonical surfaces
  — GCS object path, parquet content columns, manifest shard-atom key, and the catalogue/data-status render — over PROD
  buckets only. Phase 0 resolves + reachability-checks the prod buckets and loads the cutover register and
  accepted-exception list, Phase 1 runs the four-surface comparison per shard (manifest-driven, no new whole-corpus
  walk), Phase 2 sweeps the non-canonical path inventory and emits proof-gated delete SUGGESTIONS, then writes + prints
  the report. Read-only by construction — it never writes GCS, never writes the manifest, never runs a backfill. Deletes
  are suggestions only, gated on a five-part proof; prod-bucket deletes are a human-only hard stop. Never invents
  `--asset-group` — it must come from the operator. Composes with `/autonomous`'s no-pause contract — under
  `/autonomous`, loop to the next asset_group instead of stopping at "done, what's next." Trigger on
  `/data-pipeline-reconciliation`, "reconcile the data pipeline for <asset_group>", "check canonicalisation for
  <asset_group>", "are the GCS paths and manifest canonical", "find non-canonical prefixes", "what can we delete from
  the prod buckets".
---

# /data-pipeline-reconciliation — per-asset-group four-surface canonicalisation reconciliation

Answers one question for one asset_group, with evidence: **is this asset_group 100% canonical, and where exactly is it
not?** It compares the canonical target against reality on all four surfaces the workspace treats as load-bearing, over
**PROD buckets only** (`-prd-` tier; `-test-` buckets are out of scope by construction), and reports typed findings plus
delete **suggestions** that carry their own proof.

This is **not** a backfill smoke check. `/data-pipeline-check-is` and `/data-pipeline-check-mtds` prove the _write_ path
works against `-test-` buckets; this skill audits the _resting estate_ in prod and never writes anything. It does
statically audit those skills' write paths (§ 4c) but never runs them.

**Shard atom** (identical across writer / manifest / status / gate / UI — never invent another):
`pipeline_mode({mode}_{source}) · date · asset_group · venue · [chain] · instrument_type · data_type · (KEY) · [quote · margin] · source`.
`(KEY)` varies by grain pattern: `instrument_id` (flat-per-contract) · `underlying` (bundle-per-underlying — and
`underlying` is a KEY **only** in this pattern; elsewhere it is display-only) · `canonical_question_group` (prediction —
**manifest-only, never a path segment**). Keying prediction on `instrument_id` is how CQG bundle rows get wiped.

**The four surfaces**: (1) GCS object path + filename · (2) parquet **content** columns (`instrument_id`) · (3) the
manifest `_index` shard-atom key · (4) the catalogue / data-status render. **defi note (measured 2026-07-20):** the
symbolic `canonical_instrument_id` is **not** a raw-tick S2 content column — raw-tick content carries only the composite
`instrument_id`; `canonical_instrument_id` lives in the **catalogue (S4)**. Do not read it from S2 (it is a `KeyError`
there) — see reference-defi's two-id model. A shard is canonical only when all four agree at atom grain. Agreement on
three of four is the interesting case — that is where silent data loss lives.

**Durable rules live in codex, not here.** This file is a runbook that _references_ its SSOTs; when they change, it
inherits the change. Read these before trusting any verdict:

| Concern                         | SSOT                                                                                   |
| ------------------------------- | -------------------------------------------------------------------------------------- |
| What canonical IS (tie-breaker) | `codex/02-data/cross-asset-canonical-target-ssot.md`                                   |
| The comparison procedure        | `codex/02-data/four-surface-reconciliation-procedure.md`                               |
| Finding names + exception list  | `codex/02-data/reconciliation-finding-taxonomy.md`                                     |
| Delete safety (5-part proof)    | `codex/02-data/gcs-and-manifest-delete-safety-protocol.md`                             |
| Known non-canonical locations   | `codex/02-data/non-canonical-path-inventory.md`                                        |
| Per-AG effective-from dates     | `codex/02-data/canonical-cutover-register.md`                                          |
| Orphan oracle                   | `codex/02-data/orphan-object-detection.md`                                             |
| Manifest schema + coverage      | `codex/02-data/availability-manifest-and-data-status.md`, `…/honest-coverage-model.md` |
| Bucket naming + resolution      | `codex/05-infrastructure/bucket-isolation-model.md`                                    |
| GCS object ops                  | `codex/05-infrastructure/gcs-object-operations.md`                                     |

## 0. `--asset-group` is REQUIRED — never synthesize one

This reconciliation is meaningless without a real target. If the invoking prompt doesn't carry an explicit
`--asset-group <cefi|tradfi|defi|prediction|sports>`, **stop and ask the operator for one** before doing anything else.
Do not default to "all" and do not pick the first one — the per-AG code paths differ enough (§ 3) that a wrong guess
produces confidently-wrong findings.

An optional `--date-window <START>..<END>` narrows the manifest scan. Absent it, scan the full manifest for the AG —
that is a manifest read, not a corpus walk, and is allowed.

**Never synthesize scope inside the run either.** Enumerate cells from the UAC MVP predicate
`unified_api_contracts.canonical.crosscutting.mvp_scope.is_mvp()` and from `canonical_path_templates(<ag>)` — **never**
a hardcoded venue / prefix / data_type list. A hardcoded prefix list is precisely the Axis-10 drift bug that made a
phantom-audit `--apply` false-flag real captured rows as phantom.

## 1. Composing with `/autonomous`

- **Invoked plainly** (`/data-pipeline-reconciliation --asset-group defi`): run Phases 0→2 once for that asset_group,
  write + print the report, stop.
- **Invoked under `/autonomous`**: first read `cursor-configs/AUTONOMOUS_AGENT_RULES.md` +
  `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` per that skill's contract, then loop across asset_groups — see § 6. The
  no-pause / no-`DEFERRED` contract applies: don't stop mid-matrix to ask "should I continue?"
- **The loop never lifts a hard stop.** `/autonomous` is throttle, not bypass. Every human-only item in § 4b stays
  human-only no matter how many ticks have passed.

## 2. Phase 0 — resolution gate (a real check, not an assumption)

Four things must be true before any finding is trustworthy. Prove each; do not assume.

> **Run from a venv that imports BOTH UTL and UAC.** `resolve_bucket_name` (UTL) and the UAC oracle/templates must both
> import in the same interpreter. UAC's own `.venv` **cannot** import `unified_trading_library` — use a service venv
> that carries both (e.g. `market-tick-data-service/.venv`, MTDS/IS/UTL). Measured by a first-run AG that hit an
> `ImportError` from UAC's venv. Also: manifest downloads can be large (below) — `/tmp` is often a small tmpfs shared
> across slots; download the `_index` to a roomy filesystem (`$HOME`) to avoid `ENOSPC`.

**(a) Resolve the prod buckets from the registry, never by hand.** Every bucket via
`resolve_bucket_name(cloud, kind, asset_group=…, deployment_env=…)` (keyword-only) over `cloud-providers.yaml`. Never an
inline `gs://` (QG 5.69). Never a bucket-name **fragment** as a `kind` — `market-data-tick-defi` is a fragment, not a
yaml key, and the resolver raises on it. Never mutate process env to reach a **tier**: pass `deployment_env=`
explicitly. **BUT `GCP_PROJECT_ID` is a separate, REQUIRED env read** — the resolver substitutes `${GCP_PROJECT_ID}`
from process env for the project-id segment and **raises `BucketNamingError` if it is unset** (`bucket_naming.py:354`;
measured by 4/5 first-run AGs against a clean env). That project-id read is **not** the banned tier-mutation — the two
are orthogonal. Set `GCP_PROJECT_ID=central-element-323112` in env; still pass the tier via `deployment_env=`.

> ⚠️ **Do not use UTL `PATH_REGISTRY` / `build_bucket` for Group-A datasets.** Its rows are un-tiered and resolve to 15
> flat-named buckets that are **already deleted (404 on live probe)**. `cloud-providers.yaml` + `resolve_bucket_name` is
> the SSOT — see the bucket-name resolution authority section of `codex/05-infrastructure/bucket-isolation-model.md`.

**(b) Prove reachability, and record what you could not reach.** The service account may lack project-wide
`storage.buckets.list` — that is expected and is _not_ a finding. Probe each resolved bucket directly with a
**non-recursive** top-level listing. A bucket you could not reach becomes a declared **coverage gap** in the report, not
a silent omission. A report that omits an unreachable bucket without saying so is worse than no report.

**(c) Load the suppression inputs.** Read `codex/02-data/canonical-cutover-register.md` (to key `require_pipeline_mode`
and the other axes per-AG — pre-cutover data is _legitimately historical_, not non-canonical) and the accepted-exception
list in `codex/02-data/reconciliation-finding-taxonomy.md`. **Suppression is required, not optional** — re-reporting an
operator-accepted exception as a fresh finding destroys the report's signal and trains the reader to skim.

**(d) Read the cheap manifest status files — they are decisive, and 4/5 first-run AGs only found them by accident.**
Before any surface-3 verdict, read the `_index/*.json` status objects in the raw-tick bucket: `_index/latest.json`
(consolidator freshness / last run), `_index/phantom_audit_latest.json` (the published phantom count — **read it here,
never re-run the auditor**), and any `consolidator.lock` / `consolidator_stall_state.json`. **A locked or stale index
makes every surface-3 verdict `unavailable` (§ 3.1) and every count a lower bound** — a stale per-VM-shard fallback read
(vs a consolidated read) silently under-counts, which materially changed one AG's cross-bleed number. Record the
freshness/lock state in the report; it is a Phase-0 gate item alongside reachability.

**Refuse to proceed against a `-test-` bucket.** This skill's scope is prod. If a resolved name carries `-test-`, that
is a resolution bug — stop and report it rather than auditing the wrong estate.

## 3. Phase 1 — the four-surface comparison

Follow `codex/02-data/four-surface-reconciliation-procedure.md`. It is the SSOT for the per-shard comparison; this
section covers only how to _drive_ it and the per-AG hazards.

**Manifest-driven by default. Do not open a new whole-corpus GCS walk — that is review-blocking.** Where object
inspection is unavoidable, use only the three sanctioned no-walk routes:

1. **prefix-scoped listing** per unique `(date, venue[, chain])` derived from manifest rows (what the phantom auditor
   does);
2. **delimiter-based child-prefix listing** (`list_blobs(..., delimiter='/')` / the deployment-api storage facade's
   `list_prefixes`). ⚠️ **The UTL facade drops `.prefixes`** — `get_storage_client().list_blobs(...)` yields
   `BlobMetadata` and swallows the delimiter's child-prefixes (measured on sports). For child-prefix listing reach the
   native handle: `client._client.bucket(b).list_blobs(delimiter='/')`, then read `.prefixes`; or use a
   confirmed-working `storage_facade.list_prefixes`;
3. **reuse of an existing single walk** (`migration_orphan_sweep.py`), bundling every pass onto that ONE snapshot.

The reconciled rule is **one walk per corpus per campaign**, with all passes bundled onto that snapshot — see the shared
single-walk discipline statement in `availability-manifest-and-data-status.md` § 9 and
`codex/05-infrastructure/gcs-object-operations.md`.

**Canonical vs non-canonical is decided by the machine oracle**, UAC `canonical_path_violations()` — the inverse of the
path builders. Never re-implement path judgement in the skill; a second implementation drifts from the builders the day
the builders change. Pass `require_pipeline_mode` from the cutover register, **not** from its default (it defaults
`False`, so the machine gate is currently _weaker_ than the codex declaration — an unparameterised call silently passes
missing-`pipeline_mode` paths).

**⚠️ The oracle answers PATH STRUCTURE only — it does NOT validate the filename instrument-id.** It drops the last path
segment before validating; only `asset_group=tradfi` single-instrument shards have a stem rule. A CeFi corpus of
~811,200 wire-named / double-wrapped objects returns **0 violations == CANONICAL**. Structure and id-form are
**orthogonal — neither alone proves "canonical."** For surface-A id-form, run the canonical-id check
(`VENUE:ITYPE:BASE-QUOTE[@LIN|@INV][-YYYYMMDD][-STRIKE-C|P]` + `COMBO`) against the stem, never count chain
`underlying=…/ticks.parquet` fan-ins as violations, and **state in the report which of the two questions was actually
machine-checked.** SSOT: `codex/02-data/four-surface-reconciliation-procedure.md` § 4.3 +
`plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`.

### 3a. Surface 1+2 — path and content

For each shard in scope: classify the path via the oracle; where the grain is flat-per-contract, verify the **filename
stem equals the `instrument_id` content column byte-for-byte**. Stem-vs-column divergence is the highest-value finding
this skill produces, because both surfaces look individually valid.

> **defi two-id carve-out — do NOT byte-compare for defi POOL.** The defi filename stem is the machine `instrument_id`
> (a raw pool **address** / UUID), while the content `instrument_id` column is the **symbolic composite**
> (`ORCA-SOLANA:SOLANA_AMM_POOL:<addr>`). They differ **by design** (the two-id model, reference-defi) — a byte-for-byte
> stem check flags every defi POOL shard as a false regression. The symbolic-leaf writer is **not yet shipped** (cutover
> register § 5), so today's on-disk leaf is the address, not the symbolic id shown in some examples. Skip the stem
> byte-compare for defi; compare the machine key to the manifest key instead.

### 3b. Surface 3 — manifest

Compare the manifest `_index` shard-atom key against the path-derived atom. Report `capture_status` in the 4-state model
and honour `expected_unattempted` as **materialised by the writer** — never re-derive it.

**Read the `_index` efficiently — it is one multi-GiB / multi-M-row file, not a directory.** The consolidated
`_index/availability_index.parquet` can be ~1.66 GiB / ~52M rows (defi) down to ~74 MiB / ~5.2M rows (tradfi); a naive
`read_table` of all columns OOM'd a 15 GB box and a naive row-by-row aggregation over 10M rows burned ~5 min for several
first-run AGs. Read it with **pyarrow predicate pushdown on `(date, asset_group)` + column projection** (`columns=`
slim, `filters=` date), never a full load and never a walk. Where pre-computed `_index/audit/*.parquet` sweeps already
exist (e.g. `orphan_sweep_<ag>`), READ them rather than re-deriving.

**Report a number only with its formula named.** Three incompatible honest-coverage formulas exist in the corpus; the
live, CK3-certified one is `honest-coverage-model.md`'s
`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)` with `empty_confirmed`
**EXCLUDED**. An unnamed `%` is unfalsifiable. Also state that all 5 asset_groups gate Layer-2
(`instrument_gates_download=true`), so every `coverage_pct` is a **lower bound**; and never quote a defi coverage %
derived from the 1.38M denominator — the real one is 63.9M.

### 3c. Surface 4 — catalogue / data-status

Which catalogue applies depends on the layer under audit: **instruments** (the per-AG instruments-store catalogue),
**features**, **ml**, **strategy**. Compare the catalogue's identity fields against the canonical instrument-id grammar
and the canonical paths.

**If the catalogue mechanism is categorically absent for the whole AG** — no reader and no entry in the consumer's
`_CATALOG_ASSET_GROUPS` (prediction is absent; no `prediction_catalog_reader.py` exists) — surface 4 is `UNAVAILABLE`
for the **entire AG by construction**. Report it **once** as a declared coverage gap, not `unavailable` per shard, and
do not synthesize a surface-4 verdict that has no mechanism behind it. The "four surfaces = four bits, never collapse"
rule still holds per shard; a whole-AG missing surface is a single declared gap, not a collapse.

> ⚠️ `codex/02-data/data-catalogue-schema.md` is SUPERSEDED — it documents an artifact, writer, reader, updater and
> validating plan that do not exist. The shape deployment-api actually consumes is `shard_status[AG][VENUE].start_date`
> — see `codex/02-data/service-shard-status-catalogue.md`. Treat the live `data-catalogue.*.yaml` staleness
> (`last_updated` 2026-02-06, `auto_refreshed: null`) as a standing known condition, and report it as a
> **catalogue-freshness** finding once per run, not once per shard.

### 3d. Per-AG hazards — a generic loop produces destructive false positives on at least three of five

| AG             | What differs — and what a generic pass gets wrong                                                                                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **sports**     | **No `asset_group=` key at all** — the tree is `sports_reference/by_date/day={D}/pipeline_mode={m}_{s}/entity={E}/league={L}/`. `entity=` is never a `data_type`. A generic pass flags the whole estate.  |
| **prediction** | Manifest-only CQG bundle grain; raw objects are per-`conditionId`. **Do not run the phantom reconciler against it.** There is no `canonical_question_group=` path segment.                                |
| **defi**       | `chain=` exists and sits **after** `venue=` (operator-locked); venue is the **bare protocol** (`AAVE_V3`, never `AAVE_V3-ETHEREUM`); two-id model. Capture is currently **STOPPED** pending a writer fix. |
| **tradfi**     | Carries the write-time raising guard; `batch_massive` **read-recognition is deliberately KEPT** until the gated purge — flagging its 1.47M objects as orphans is a false positive.                        |
| **cefi**       | v5/v6 **dual chain-tail** hazard — W1 may emit bare `underlying=/ticks.parquet` while W2 emits the canonical `underlying=/quote=/margin=/ticks.parquet`. Scan for both; report the divergence.            |

### 3e. Two axes the skill must currently REFUSE to report on

Both are **unruled operator decisions** with the two sides citing the same operator on the same date in opposite
directions. Reporting either as a finding would be picking a side silently:

- **manifest `instrument_type` COLUMN case (C2a)** — do not report casing, do not propose or execute any casing
  migration. The **path** segment (lowercase) and the **id** middle segment (UPPER) _are_ settled and must still be
  enforced. Compare the column case-insensitively.
  > ⚠️ **The codex SSOTs currently DISAGREE on C2a (4/5 first-run AGs hit this).** `reconciliation-finding-taxonomy.md`
  > § 5.1 says C2a is **UNRULED → REFUSE**, while `canonical-cutover-register.md` § 3c, `four-surface-…procedure.md` § 7
  > (O2) and `gcs-and-manifest-delete-safety-protocol.md` § 4 say **RULED UPPERCASE 2026-07-20 (D1) → ENFORCE**. **Until
  > the codex is reconciled, this skill REFUSES** (follow the taxonomy) and surfaces the contradiction with both
  > citations — do NOT enforce a casing migration off the register alone. This is a flagged codex contradiction for the
  > orchestrator, not an executor decision.
- **defi market/event `LENDING` keying (decision D)** — do not flag `lending` on market/event data_types
  (`lending_indices`, `liquidation_events`, `flash_loan_events`, `position_data`) as non-canonical. Only `holdings` uses
  the `A_TOKEN`/`DEBT_TOKEN` split.

Surface the contradiction with both citations and a severity; **do not resolve it.**

## 4. Phase 2 — non-canonical sweep and delete suggestions

### 4a. Sweep

Reconcile the live estate against `codex/02-data/non-canonical-path-inventory.md`. Two directions, both required:

- **Register → reality**: for each inventory entry scoped to this AG, re-verify its disposition still holds.
- **Reality → register**: any non-canonical location found that is _not_ in the register is a **new finding** for the
  register (the doc's maintenance contract). **Concurrency clause (2/5 first-run AGs blocked on this):** under multi-AG
  / `/autonomous` execution with orchestrator-owned git, do **NOT** edit the shared `non-canonical-path-inventory.md`
  inline — sibling AGs touch the same file and this skill does not run git. Instead **emit a register-patch stanza in
  the report** (the exact row to append, with its disposition) for the orchestrator to apply serially. A single
  interactive run may edit the register directly.

Detect orphans per `codex/02-data/orphan-object-detection.md` — an object with no manifest row **and** outside the
oracle's expected set is invisible to every manifest-driven tool, which is exactly why it needs its own oracle.

### 4b. Delete suggestions — suggestions only, and they carry their proof

Deletes are **never executed by this skill**. It emits a suggestion with a disposition and the evidence behind it. Per
`codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, a suggestion may rise above `unknown` only with a
**five-part proof**: (1) the twin **resolves** via `gcs_describe_object`, not by path construction; (2) a **content**
verify, not existence; (3) grep-then-READ proof nothing still **writes** it; (4) grep-then-READ proof nothing still
**reads** it; (5) the **legacy-COPIED-not-MOVED** invariant is honoured. Any part failing → `no-migrate-first`.

Disposition vocabulary: `yes-twin-confirmed` · `yes-after-verify` · `no-migrate-first` · `no-still-authoritative` ·
`unknown`.

> **Why the content verify is mandatory, in one case.** An R5 content-verify overturned a DUP verdict that would
> otherwise have destroyed **32 legacy-only high-TVL Raydium pools** (XMR/USDC ~$47M, BNB/USDC ~$18M) whose paths looked
> duplicated. Path-shape similarity is not evidence of duplication.

**Human-only hard stops** — never crossed autonomously, on any tick:

- any **prod-bucket delete**;
- any **legacy-object delete after copy**;
- the tradfi `batch_massive` ~1.47M-object purge;
- anything touching `instrument_type` casing while C2a is unruled;
- the defi `dex_pools/` + `lending_indices/` delete — **the delete order in two live plan docs is stale**; see
  `plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`. The canonical twin is a **partial overlap**,
  not a duplicate: ORCA/RAYDIUM have canonical objects, while **KAMINO and SOLEND have none** — for those the legacy
  objects are the only copy. execution-service still references the legacy shape at runtime. Executing it destroys data.

> ⚠️ **Probe the right `instrument_type` or you will manufacture a false "twin absent" verdict.** Solana AMM venues
> write `instrument_type=solana_amm_pool`, **not** `instrument_type=pool`. A probe using `pool` returns zero for
> ORCA/RAYDIUM even though 14k+ canonical objects exist — measured 2026-07-20. An absence result is only evidence once
> you have confirmed you probed the vocabulary the writer actually emits; enumerate it from
> `canonical_path_templates(<ag>)` rather than assuming.

**`still_written_by: NONE-FOUND` is a grep result, not a proof of absence.** Docstrings are not evidence — the MTDS defi
handler docstrings describe `dex_pools/` writes the code does not perform, and three separate in-repo comments assert
the instruments-service writer emits the hive path while the code emits flat. **grep-then-READ, always.**

### 4c. Static audit of the backfill write paths (audit only — never run them)

Confirm the sibling smoke skills write to `-test-` buckets **only**, and that the underlying writers emit the canonical
grammar. This is a code read, not an execution — **never invoke a backfill from this skill.** A writer defect found here
is a finding for the report and a todo on the relevant plan; do not fix it inline (it belongs to that service's plan and
fixing it here risks a collision).

## 5. Write + present the report — do not just point at the file

Emit a markdown + sibling JSON pair at `plans/audit/results/data_pipeline_reconciliation_<AG>_<YYYY_MM_DD>.md` and
**print the full rendered markdown to stdout**.

**Relay the printed content directly to the operator in your response — do not say "done, see the report" and make them
open the file.** The report must carry:

- a **Bucket paths** table naming exactly which bucket each read targeted, and flagging any it could not reach (built
  from probe output — there is no generator, despite older "auto-generated" wording);
- the **index freshness / lock state** of every manifest read (consolidated vs per-VM-shard fallback, consolidator
  healthy vs locked/stale) — a stale/fallback read makes every count a lower bound (§ 2d);
- a **per-surface verdict per shard** — four surfaces means four bits, never collapsed into one pass/fail (three
  different failure modes on one cell must not become one); for a manifest-only-key AG (prediction, sports) whose per
  shard rows don't materialise, report at shard-**class** grain `(venue, data_type, pipeline_mode)` and say so;
- **typed findings** using the names in `codex/02-data/reconciliation-finding-taxonomy.md`, so consecutive runs diff
  cleanly;
- **suppressed** accepted-exception counts, shown as a count with a pointer — proving suppression happened without
  re-listing them;
- every `%` with **its formula named**, and marked as a lower bound;
- a **coverage gap** section listing anything not reached and why.

**No summary docs.** Findings that need tracking become `- [ ]` todos on the relevant active plan, or an issue doc at
`plans/active/issues/<slug>_<YYYY_MM_DD>.md`. A **big finding** (data-correctness / cross-repo / SSOT contradiction)
additionally **notifies the operator** in chat.

## 6. Under `/autonomous` — loop, don't stop at "done, what's next"

- After the report for the current asset_group, do **not** report "done" and wait.
- Pick the **next unreconciled** asset_group and repeat Phases 0→2, appending to (never overwriting) the campaign's
  reports.
- Stop only once every asset_group carries a four-surface verdict **and** every new non-canonical location has been
  added to the register. Then print the campaign summary: AGs reconciled / findings by type / delete suggestions by
  disposition / coverage gaps still open / unruled axes still blocking.
- **A flat progress metric across a tick is a STALL** — no new shard classified, no new finding, no new register entry.
  Diagnose it; never burn ticks repeating a failing action.
- **Contradictions do not resolve themselves on a later tick.** If an axis is blocked on an operator ruling, it stays
  blocked — record it and move to the next AG rather than re-deriving the same blocked verdict every pass.

## Extending to a new asset_group

Add its row to § 3d (the hazards table), its axes to `codex/02-data/canonical-cutover-register.md`, and its known
locations to `codex/02-data/non-canonical-path-inventory.md`. The four-surface procedure and the shard atom never change
— that is the point of them. If a new AG appears to need a fifth surface or a different atom, that is an SSOT change in
`codex/02-data/cross-asset-canonical-target-ssot.md` first, and this skill inherits it; do not special-case it here.

## Not wired into `quality-gates.sh`

This reconciliation does real GCS I/O and multi-minute-plus runtime against prod — it stays a standalone, on-demand
skill (cron-schedulable later via the `schedule` skill), never part of any repo's `quality-gates.sh`.
