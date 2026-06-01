# Resume prompt — Slot 2 / DeFi lane / C0 unified canonical migration (handoff 2026-06-01)

You are **slot 2** (DeFi lane) in `.tabs/2`, branch `tab/ikennaigboaka/2` tracking `origin/live-defi-rollout` (LDR).
Operator: Ikenna. You are resuming the DeFi canonicalisation migration. **Read this whole file, then the SSOTs it names,
before doing anything.** Boot:
`cd .tabs/2 && for r in unified-trading-pm market-tick-data-service deployment-service unified-api-contracts; do git -C $r fetch origin live-defi-rollout -q && git -C $r pull --ff-only origin live-defi-rollout; done`.

## Mission (operator, exact words)

"Everything needs to be on the right manifest and data schema (v9 canonical, per the plans). Migrate ONCE, on v9,
because we keep missing things and I don't want to do that anymore. Net result: all old buckets + old paths deleted, so
data-status/manifest has ONE source of truth and we can really see missing data." **The schema migrated TO must be
UNIFORM** (identical per data_type regardless of source layout) — that is key.

## Read these SSOTs first (do not act from memory)

- `plans/active/defi_manifest_canonicalisation_2026_06_01.md` — §MASTER (two-slot split: you own the DeFi lane §A–§G),
  §C (the gate), and especially the **"🛑 CRITICAL DISCOVERY"** block + **C0-RD1…RD5** todos (the binding spec).
- `codex/05-infrastructure/gcs-object-operations.md` — the **Migration-script performance contract** + the **Migration
  completeness + uniform-schema + legacy-deletion contract** (both HARD RULES codified this session).
- `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` — CF-1…CF-12 + "scope is a PRIOR, not a
  ceiling — fix-fully-autonomously".
- `market_tick_data_service/scripts/audit_canonical_form.py` (reusable CF data-state audit, built this session) and
  slot-4's `plans/audit/results/cf_manifest_audit_2026_06_01.py`.

## What is DONE + SAFE (do not redo)

- **L0 tarball reliability FIXED** (deployment-service): authoritative SHA-pinned VM pull (loud-fail on
  missing/mismatch) `a0fcba7`; watchdog covers `canonical-migration-legacy-` `1ac76a0`; mtds pin metadata read +
  launcher forwards `UAC/UTL/MTDS_TARBALL_SHA` `d90d50c`; launcher `defi` → `python -u … --workers 96` `6335856`. Issue
  RESOLVED `3ef1ec40b`.
- **C0 tool partially redesigned** (`market_tick_data_service/scripts/migrate_defi_full_v9_canonical.py`,
  mtds@`97b854f5`): ThreadPoolExecutor + day-prefix parallel listing + workers default 64 + stamps `asset_group` COLUMN
  (CF-2) + progress logging. **BUT it still only parses the flat `day=/category=` layout — see "remaining work".**
- **Reusable CF audit tool** `audit_canonical_form.py` shipped.
- **Plan/codex updated**: past-data affirmation `363517b41`; perf contract `4f57234ea`+`6a060242f`; 4 AG-plan
  propagation `03d84ebe4`; C0 discovery + C0-RD1..RD5 `7f0a41212`; completeness+uniform-schema contract `1a8ca7c31`.
- **NOTHING DELETED.** All source buckets intact. 6 source `_index` snapshotted →
  `_index/snapshots/pre_migration_2026_06_01.parquet`. The incomplete sharded run was killed; `-prd` buckets hold only a
  partial flat-subset + prior leftovers (idempotently overwritten on the real run — ignore them).

## The data-state truth (audited — TRUST THIS, re-verify before acting)

Each of the 6 DeFi source buckets (`{stem}-central-element-323112` for stem ∈ dex-pools, dex-swaps, lst-rates,
lending-indices, oracle-prices, perp-funding) holds **3 OVERLAPPING layouts** (dex-pools = 191,456 parquet):

1. `dex_pools/{venue}/{chain}/date=…` — **166,257 (87%)** — oldest, lowercase venue, `date=` not `day=`, no asset_group.
2. `day=/category=defi/venue=…` — 19,257 (10%) — flat (the ONLY one the current tool handles).
3. `raw_tick_data/by_date/day=/asset_group=defi/venue={CANONICAL}/…/data_type=…/` — ~5,900 (3%) — **best schema**
   (canonical `_V{N}` venue + asset_group) but **missing `pipeline_mode=`** + **partial coverage**. SAME venues across
   all trees (`curve`/`CURVE`, `aerodrome_v3`/`AERODROME_V3`) ⇒ **overlapping duplicates in different schemas +
   coverage, NOT complementary.** The `_index` is **100% non-v9** (v4/5/6/8) with **no source/asset_group/ pipeline_mode
   columns**. Dest = `{stem}-prd-central-element-323112`.

## Remaining work (in order) — C0-RD1…RD5

1. **C0-RD1/RD2/RD3 — finish the tool redesign.** Make `migrate_defi_full_v9_canonical.py`: (a) enumerate ALL 3 layouts
   (not just `day=`); (b) normalise each object to a canonical cell key `(venue→UAC _V{N}, chain, data_type, day)` —
   handle `date=` vs `day=`, bare `aerodrome_v3/BASE` segments vs `venue=`/`chain=`; (c) **dedup overlaps** (freshest
   schema → most-complete rows → latest write ts); (d) **UNIFORM output**: conform every chosen cell to the SINGLE UAC
   canonical schema for its data_type (identical columns + path) → write ONCE to `-prd`. Keep it conformant to the perf
   contract (ThreadPool, `--workers`, `--start/--end` date-shard, `python -u`, idempotent, per-object isolation).
2. **Verify locally** (small slice, dry) then **rebuild the tarball**
   (`bash deployment-service/scripts/vm/create-code-tarballs.sh --allow-dirty-tarball`, from `.tabs/2`) and confirm the
   new `mtds-code@<sha>.tar.gz` pin is in `gs://deployment-scripts-central-element-323112/code/`.
3. **Run sharded for <1h**: `export UAC_TARBALL_SHA=6261bea2… UTL_TARBALL_SHA=0f7198f2… MTDS_TARBALL_SHA=<new>`; launch
   ~4 date-shard VMs: `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh defi <start> <end> full`
   (e.g. 2020-01-01:2023-12-31, 2024, 2025, 2026-01-01:2026-06-01). Monitor ROBUSTLY (see gotchas).
4. **C0-RD4 completeness+uniformity gate**: `-prd` distinct-cell count ≥ union of all 3 source layouts; exactly ONE
   schema per data_type across all output; CF-1…CF-12 GREEN via `audit_canonical_form.py` on the rebuilt `-prd` `_index`
   (re-run the consolidator first). Only then C-GREEN.
5. **C0-RD5 delete ALL legacy** (every source bucket + every legacy path/tree) — ONLY after RD4 GREEN. One v9 SSOT.
6. Then the rest of the DeFi lane: §A writer fixes (A2a/A2b/A4/A5), §B consolidation/data-status, §D features, §E
   cefi-perp, §F docs, §G Solana MVP. (Slot 4 owns the other AGs; their buckets likely share the multi-layout shape —
   the CROSS-AG notes in their plans already warn them.)

## Lessons / gotchas (these cost time this session — honour them)

- **VERIFY DATA-STATE, never trust a constant/intent/headline cell-count.** The v9 constant lied (0% v9); the "16,206
  cells" prior was 10% of the real corpus. Read the actual `_index` columns + object trees.
- **Enumerate ALL top-level trees before migrating** — the target moved historically so layouts coexist; an unrecognised
  tree is review-blocking, never silently skipped.
- **Uniform output schema per data_type is the point** — non-uniform output recreates the mess.
- **Perf**: the walk is **I/O-bound** (18% CPU @ workers=32 on e2-standard-8). Use workers 96 + day-prefix listing; one
  VM is pool-capped (~100 conns) → **horizontal date-shard across VMs** is the <1h lever. No fire-and-forget.
- **Monitor robustly**: use a single `gcloud compute instances list --filter="name~canonical-migration-defi"` call
  (per-VM `describe` in a loop flakes → false GONE), and add a warmup guard (VMs are PROVISIONING at poll-1 → false "all
  done"). Both bit me this session.
- **Tarball**: rebuild after ANY mtds commit; verify the `@sha` pin uploaded before launch; the launcher forwards the
  pin env-vars so the VM provably runs your code.
- **Shell (zsh)**: `set -- $var` does NOT word-split — use `${r%%:*}`/`${r##*:}`. `status` is a read-only var in zsh.
- **Git**: prek auto-restore → commit with `--no-verify` when you see "Restored working tree changes"; stage by name
  (never `git add .`); LDR (esp. PM) is hot → expect rebase-loops (`git pull --rebase` + retry push); never touch
  foreign dirty files (`docs/*.svg`, `uv.lock` churn is not yours). QG: run `bash scripts/quality-gates.sh` on repos you
  touch; leave unrelated pre-existing CI/QG failures for other agents (operator directive).
