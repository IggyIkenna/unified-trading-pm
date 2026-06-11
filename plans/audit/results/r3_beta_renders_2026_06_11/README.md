# R3 beta-render verdict packs — 2026-06-11

Per-AG pre-apply verdict packs (CF-20/V5-V6). Beta render = deployment-ui data-status with
`DATA_STATUS_BETA_MANIFEST_BLOB='_index/audit/projected_index_{asset_group}.parquet'`; live render = same views, env
unset. Renders show ALL asset groups in one view (the data-status tab is AG-inline) — per-service screenshots:
instruments + market tick data, beta vs live.

| AG         | diff verdict                              | pack                  |
| ---------- | ----------------------------------------- | --------------------- |
| sports     | GREEN 0/0                                 | verdict_sports.md     |
| defi       | 5,320 respelling-justified, 0 regressions | verdict_defi.md       |
| cefi       | garbage+phantom-justified                 | verdict_cefi.md       |
| prediction | superseded-grain + cqg P1 OPEN            | verdict_prediction.md |
| tradfi     | garbage+phantom+respelling-justified      | verdict_tradfi.md     |

Full adjudication narrative: plans/active/migration_verification_orphan_safety_2026_06_10.md Progress Log (2026-06-11
entries).
