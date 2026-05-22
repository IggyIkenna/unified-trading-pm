---
title: expected_unattempted production validation — pending Phase 3 MTDS run
created: 2026-05-19
author: slot-5
source:
  - expected_unattempted_propagation_chain_2026_05_12.md (Phase 6 validates)
locked_by: live-defi-rollout
---

> **🟡 SUBSUMED BY MEGA AUDIT** — findings absorbed by **Phase A3 (manifest divergence report)** per
> [mega_audit_and_plan_beefup_progression_2026_05_20.md](mega_audit_and_plan_beefup_progression_2026_05_20.md) (slot-1
> triage 2026-05-20). A3 produces the exact validation data this issue is waiting on. Do NOT work standalone.

## What I found

Phase 1+2 code (MTDS instruments-service pre-flight + MDPS DependencyChecker `record_expected_unattempted`) is shipped
and correct. However as of 2026-05-19 the CEFI/DeFi/TradFi manifests show 0 `expected_unattempted` rows because no
production MTDS batch has run on the post-Phase-1+2 code yet.

Manifest query (2026-05-19):

- cefi `_index/availability_index.parquet`: 2,632,931 rows — 0 expected_unattempted
- defi: 1,606,190 rows — 0 expected_unattempted
- tradfi: 321,436 rows — 0 expected_unattempted

Phase 1 MTDS code landed (pre-flight instruments-service manifest read → `record_expected_unattempted` for instruments
not in catalog). Phase 2 MDPS code landed at mdps@3f70cf6.

The four validation items deferred here are:

1. Manifest data-status panel shows `expected_unattempted` rows with correct reasons for instruments outside MVP scope.
2. A fresh MTDS dry-run on a sample date generates 0 new `attempted_failed` rows for instruments instruments-service
   says don't exist (Phase 1 live).
3. A fresh MDPS dry-run generates `expected_unattempted` rows for shards where MTDS said `empty_confirmed`.
4. `data_capture_rate = captured / (captured + empty_confirmed + attempted_failed
   - expected_unattempted)` is non-zero denominator across all asset_groups.

## Why it matters

These validates confirm the runtime propagation chain (instruments → MTDS → MDPS → features) is working end-to-end.
Without them the G3b gate is code-complete but not production-verified.

## Recommended decision

When Phase 3 MTDS production VMs run (2026-05-19→05-23 window per operator direction), re-run manifest query:

```bash
python3 - <<'EOF'
import subprocess, sys
for ag in ['cefi', 'defi', 'tradfi']:
    subprocess.run(['gcloud', 'storage', 'cp',
        f'gs://market-data-tick-{ag}-central-element-323112/_index/availability_index.parquet',
        f'/tmp/{ag}_manifest.parquet'], check=True)
    import pandas as pd
    df = pd.read_parquet(f'/tmp/{ag}_manifest.parquet')
    eu = len(df[df['capture_status'] == 'expected_unattempted'])
    print(f'{ag}: expected_unattempted={eu} / total={len(df)}')
EOF
```

Expected after Phase 3 MTDS run: eu > 0 for all 3 asset groups. Once confirmed, flip validates in
expected_unattempted_propagation_chain plan.
