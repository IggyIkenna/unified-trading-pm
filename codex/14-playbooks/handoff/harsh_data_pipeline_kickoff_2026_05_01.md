---
title: Harsh — data-pipeline-completion kickoff
audience: Harsh
created: 2026-05-01
status: active
owner: Ikenna
scope: [engineer, admin]
---

# Harsh — data-pipeline-completion kickoff

You're picking up the **instruments-service + market-tick-data + market-data-processing** completion epic. Goal: every
asset group in the MVP universe at 100% honest coverage, batch only. Everything you need is in this repo + the
workspace; nothing on Ikenna's local machine is required.

## Read these in this order (≈45 min total)

1. **[backfill-completion-playbook.md](../backfill-completion-playbook.md)** — operational SSOT. Cutoffs, MVP target,
   bundling/schema invariants, special cases (VIX, sports odds-API), credentials policy, known gotchas.
2. **[active plan: instruments_and_market_tick_data_completion_2026_05_01.plan.md](../../../plans/archive/instruments_and_market_tick_data_completion_2026_05_01.plan.md)**
   — phased execution DAG. Phase 0 unblockers → Phase 1 sports → Phase 2 cefi → Phase 3 tradfi → Phase 4 prediction →
   Phase 5 defi → Phase 6 verification.
3. **`.claude/CLAUDE.md` at workspace root** — the workspace-wide rules. Especially the Key Rules section, which has
   `validate_api_keys_for_venues` venue-name gotcha, `record_empty` semantics, manifest v5 contract, VM tarball
   deployment, singleton-locked launchers.
4. **[02-data/availability-manifest-and-data-status.md](../../02-data/availability-manifest-and-data-status.md)** —
   manifest 3-state semantics (`captured` / `empty_confirmed` / `attempted_failed`).
5. **[05-infrastructure/vm-tarball-deployment.md](../../05-infrastructure/vm-tarball-deployment.md)** — how backfill VMs
   boot. Always re-tar with the right `--asset-group` flag after a code change.
6. Skim **[02-data/schema-governance.md](../../02-data/schema-governance.md)** + the per-asset-group docs in `02-data/`
   as you hit each phase — don't read them upfront, look them up on demand.

## What's already in flight (don't collide with this)

A separate agent is running the sports instruments work. Before launching anything new on sports:

```bash
gcloud compute instances list --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"' --format='table(name,status,zone)'
```

If `af` / `tm` / `sfi` / `fs` are still `RUNNING`, let them finish. The `manifest-consolidator` is a long-lived daemon —
that one is supposed to stay up. Sports headline coverage trajectory this session was 74% → 80%; you're picking up to
drive it to 100%.

## How to load deployment-ui locally (for the data-status drilldown)

```bash
cd unified-trading-system-repos/deployment-ui
bash scripts/dev-tiers.sh --tier 2          # local UI off-mock + local API off-mock (real GCP via ADC)
# UI: http://localhost:5183  |  API: http://localhost:8004
```

Tier 2 needs ADC: `gcloud auth application-default login` once. T1 = both mock (UI + API hit fixtures, no GCP). T0 =
UI-only mock. T3/T4 (cloud-deployed) are not yet deployed for this stack — local is the SSOT for now.

If the drilldown shows bugs (CSV download empty, day-shard list capped, schema modal blank, sports/MTDS+MDPS view
split), those are **Phase 0 in the active plan** — fix them first before you can use the UI to drive backfill
verification.

## MVP target (the C5 dataset — what you're driving to 100%)

Full spec in the playbook's "MVP target" section. Quick version:

- **CeFi**: top ~20–25 assets, spot+futures+perps on `BINANCE-SPOT/FUTURES`, `OKX`, `UPBIT`, `BYBIT`, `HYPERLIQUID`;
  Deribit options **combos** (not single strikes).
- **TradFi**: CME ES futures + ES options chain (combo-bundled), CME BTC futures, BTC + ETH spot ETFs, VIX index
  (already done — 15m bundles from Barchart + last 90d from Yahoo Finance).
- **Prediction**: TradFi instruments routed through up/down combo schemas.
- **Sports**: parallel work — most of what's missing is already-fetched odds-API data that just needs MDPS processing.
- **Batch only.** Live ingestion is the next milestone, not part of this work.

## Invariants you must not violate

(All in the playbook's "Schema + bundling invariants" section. Calling out the high-impact ones here.)

1. **Single bundled file per (day × underlying × data_type)** — options/combos/features land as one parquet per
   underlying, never per-contract. The 2026-04-30 migration compacted ~13M legacy per-combo files into ~36k bundled
   files; do not regress.
2. **Today's code on today's data reproduces historical output.** Schema migrations rewrite the whole window — never
   leave old files in old shape + new in new shape.
3. **No duplicate schemas for the same logical data.** Two parquets for the same `(day × instrument × data_type)` means
   one is wrong; pick canonical, migrate, delete the loser.
4. **Data-status denominator clipped to "data was actually possible".** Pre-launch dates use `record_empty`, not
   `attempted_failed`.

## Credentials

All API keys in GCP Secret Manager (`central-element-323112`). `ApiKeyReloader` (UTL) fetches them at runtime. No local
`.env` files, no inline keys. If a backfill fails with "missing key", check the secret exists in Secret Manager first;
if it's missing or stale, ping Ikenna — don't go hunting for a local copy.

### One-time GCP setup (do this first, before any backfill)

ADC is fine; the only outstanding access bits are Pub/Sub. The deployment-api emits events to `deployment-api-events`
and your account needs `pubsub.topics.publish`. Ikenna will run these as project owner:

```bash
# 1. Create the missing topic
gcloud pubsub topics create deployment-api-events --project=central-element-323112

# 2. Grant your account Pub/Sub publisher role
gcloud projects add-iam-policy-binding central-element-323112 \
  --member="user:harshkantariya@odum-research.com" \
  --role="roles/pubsub.publisher"
```

After those run, `bash scripts/dev-tiers.sh --tier 2` should boot cleanly with backend events flowing. If you see
`PERMISSION_DENIED ... pubsub.topics.publish`, those two commands haven't been run yet — ping Ikenna.

## How to start

1. Run the playbook's "What to check before kicking off Phase 1 sports work" checklist (3 commands).
2. Pick up Phase 0 in the active plan (UI unblockers). Without these, you can't see what's missing or verify shards.
3. Once Phase 0 is green, drive Phases 1–5 in order. Phases run sequentially per the DAG; within a phase, parallelise
   what's marked `[PARALLEL]`.
4. End each phase by running `instruments-service/scripts/reconcile_phantom_manifest_rows.py --asset-group <X>` and
   re-snapshotting the deployment-ui drilldown.

## Where to ping Ikenna

- Missing / stale Secret Manager entries.
- Schema decisions that would affect more than one asset_group's bundling.
- Any "the playbook says X but the code does Y" mismatch — surface fast, do not silently work around.
- Anything you'd consider a workaround for an underlying issue. The workspace rule is "fix the root cause" — flag it if
  you're tempted to bypass.

Otherwise, ship — quickmerge with `--agent`, follow the workspace `.claude/CLAUDE.md` rules, and lean on the active plan
as the running todo list.
