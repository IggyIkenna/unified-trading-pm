---
title: "Watchdog env-tier + bucket-SSOT integration (corrected scope)"
created: 2026-05-11
revised: 2026-05-12
author: ikenna-slot8 (original) — claude-corrected 2026-05-12 after factual audit
source:
  - plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md Q7(c)
  - deployment-service/scripts/vm/vm_zombie_watchdog.py
  - CLAUDE.md "No fire-and-forget VM launches" rule (events bucket SSOT)
  - CLAUDE.md "Bucket-name SSOT (b+)" rule (resolve_bucket_name discipline)
locked_by: live-defi-rollout
locked_since: 2026-05-11
severity: P1
suggested_owner: deployment-service maintainer (Ikenna-side, slot 1 main triage)
---

# Watchdog env-tier + bucket-SSOT integration

> **Revised 2026-05-12**: the original "watchdog reads from `{pid}-events` and must fan-in to 3 env-tiered events
> buckets" framing was **factually wrong**. `vm_zombie_watchdog.py` reads from `HEARTBEAT_BUCKET =
> f"deployment-scripts-{PROJECT_ID}"` (heartbeat + EXIT_STATUS blobs) and `VM_PREFIX_TO_BUCKET` data buckets
> (per-prefix shard freshness). It does **not** consume `{pid}-events`. The real gap when env-tiering rolls out
> is different — see below.

## What's actually broken (corrected scope)

`deployment-service/scripts/vm/vm_zombie_watchdog.py` has **two** real env-tier integration gaps + **one**
architectural feature request:

### Gap 1 — `VM_PREFIX_TO_BUCKET` hardcodes flat bucket names

`VM_PREFIX_TO_BUCKET` dict (lines ~100-450) contains ~72 entries of the form:

```python
"mdps-sports-bucket-": f"market-data-tick-sports-{PROJECT_ID}",
"cme-events-": f"market-data-tick-tradfi-{PROJECT_ID}",
# ... ~70 more
```

When the bucket-SSOT migration rolls out (`bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6,
2026-05-15→05-19), every `market-data-tick-{asset_group}-{pid}` bucket becomes env-tiered:
`market-data-tick-{asset_group}-{pid}-{env}` (or whatever the resolver produces). The watchdog's flat-name lookups
will silently miss the env-tier suffix → false-negative on shard-freshness checks → real zombies stay invisible.

**Fix**: route every bucket name through
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud="gcp", kind=<...>, asset_group=<...>, env=os.environ["DEPLOYMENT_ENV"])`.
Convert the dict to a `(prefix → (kind, asset_group))` mapping + resolve at lookup time. Composes with the
ml_artefact_path_resolver_consumer_sweep_2026_05_12 work (same shape, same root cause).

**Effort**: ~1 hr; 72 dict entries to remap; the resolver call is a 1-line replacement per lookup site.

### Gap 2 — `HEARTBEAT_BUCKET` hardcoded; needs env-tier check

```python
HEARTBEAT_BUCKET = f"deployment-scripts-{PROJECT_ID}"
```

This is the ops bucket containing `vm-heartbeat/{vm}.txt` + `vm-logs/{vm}/EXIT_STATUS` + tarballs + launcher scripts.
**Question for operator**: should `deployment-scripts-{pid}` itself go env-tiered (`deployment-scripts-{pid}-{env}`),
or stay flat as a project-wide ops bucket?

- **If env-tiered**: watchdog needs the same `resolve_bucket_name` retrofit as Gap 1, but for `kind="deployment-scripts"`
  (or whatever the canonical name is — add to `cloud-providers.yaml` if missing).
- **If kept flat**: leave the hardcode + add a `# bucket-name-ssot-exempt: deployment-scripts (project-wide ops)` comment
  + add to QG STEP 5.69 allowlist.

**Operator decision needed before fix**.

### Feature request — should watchdog also consume `{pid}-events-{env}/events/`?

Today the watchdog uses two signals to call a VM "zombie": (a) stale heartbeat blob, (b) stale shard parquet in the
per-prefix data bucket. CLAUDE.md "No fire-and-forget VM launches" rule says **every VM launch must be paired with
active event-stream verification** at `gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`
— required: STARTED within 60s, ≥1 progress event/hour, STOPPED/FAILED at exit.

**Question**: should the watchdog ADD events-stream consumption as a third zombie signal? Pros: redundant
fail-detection (heartbeat blob might be written by a defunct process that never emitted STOPPED); composes with the
unified-events-interface UI shipped same week. Cons: ~3 buckets to fan-in (env-tiered events) + correlation-id tracking
across many blobs/hour + watchdog-VM-throughput concern (the original 2-tier framing of this issue).

**If yes**, then the original "fan-in to 3 env buckets" architecture question DOES become relevant for the events-stream
half. Same architecture decision as before:
- **(i) Single watchdog fans in all 3 env event buckets** — simpler ops; throughput-unknown.
- **(ii) Per-env watchdog VMs (3 total)** — cleaner isolation; ~3× operational cost.

**Operator decision needed** (this is the feature-request gate; the gaps 1+2 above ship regardless).

## Why it matters

- Gap 1 is a **silent correctness bug** — watchdog will look healthy in logs (no errors; `list_blobs` returns
  empty) while real zombies stay invisible. Composes with the 2026-05-05 incident (VM_PREFIX_TO_BUCKET-not-registered
  → silent money burn) but worse because the dict IS populated; just resolves to wrong env's bucket.
- Gap 2 is a smaller question — depends on the global bucket-naming convention for ops/heartbeat buckets.
- Feature request is a maturity item: events-stream consumption would close the "VM exited without writing EXIT_STATUS"
  failure mode that scenario 06 (`defi_mempool_congestion`) + scenario 02 (`defi_chain_rpc_outage_solana`) can both
  produce.

## Recommended decisions

1. **Gap 1**: ship now (P1) — coordinated with bucket-SSOT Phase 2.6 (2026-05-15→05-19). Without this, Phase 2.6
   leaves the watchdog blind.
2. **Gap 2**: operator picks env-tier vs flat for `deployment-scripts-{pid}`. Recommend **flat** (it's a
   project-wide ops bucket; env-tiering doesn't add isolation value here; just adds 3 buckets to provision).
3. **Feature request**: operator picks. Recommend **defer to post-cutover** as Phase 3 of this issue —
   instrument watchdog for the 2 existing signals first (gap 1 land), measure VM-zombie false-negative rate over
   7-day continuous run, then decide if events-stream consumption is worth the throughput cost.

## Cross-references

- Bucket-SSOT plan Q7(c): `bucket_name_ssot_canonicalisation_2026_05_10.md` § "Open questions Q7"
- ML bucket-SSOT sweep: `plans/archive/issues/ml_artefact_path_resolver_consumer_sweep_2026_05_12.md` (same shape;
  precedent for "route all consumers through resolve_bucket_name + ratchet via QG STEP 5.69")
- CLAUDE.md "No fire-and-forget VM launches" rule (feature-request rationale)
- CLAUDE.md "VM Naming Convention" rule (watchdog dict requirement)
- Phase 2.6 cutover window: 2026-05-15→05-19
- Composes with scenarios 02 (RPC outage), 05 (gas surge), 06 (mempool congestion) which can produce VMs that look
  alive on heartbeat but never write EXIT_STATUS.

## Resolution status

🟡 OPEN —
- Gap 1: ready to ship (P1); needs ~1hr; should coordinate with Phase 2.6 timing
- Gap 2: needs operator pick (deployment-scripts-{pid} flat vs env-tiered)
- Feature request: defer to post-cutover Phase 3; measure first, then decide
