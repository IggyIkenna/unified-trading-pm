---
title: "Instruments Foundation & Catalogue Completeness — gated rebuild, every asset group"
created: 2026-06-24
parent_epic: instruments_master
assigned_vm: vm-cefi
estimate_class: design
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 11
source:
  - operator directive 2026-06-24 (foundation-first reset; ask-every-gate; observability mandatory; coverage in-line with UI)
  - cefi instruments ground-truth audit 2026-06-24 (read-only; see §Starting state)
locked_by: live-defi-rollout
priority: P0
status: active
---

# Instruments Foundation & Catalogue Completeness — gated rebuild

**Codex SSOT (the standard this plan executes):**
`codex/02-data/instruments-foundation-and-catalogue-completeness.md`.

**Operator directive 2026-06-24 (the reset):** reference data is the foundation MTDS filters against. We were chasing
MTDS coverage while the instruments foundation had day-gaps, a paused daily capture, and late MVP tags — backwards.
Rebuild it in the **gated order**, **operator sign-off at every gate** (ask every time — do not run ahead). Every
backfill/roll-up/job must be a **registered, observable BATCH deployment** in the cockpit (no fire-and-forget). Every
coverage number flows through the **`compute_honest_coverage` SSOT** so the deployment-UI shows the same real number.
**cefi first**, then defi · tradfi · sports — same process.

## Starting state — cefi ground-truth audit (read-only, 2026-06-24)

GOOD: history 2019-03-30→2026-06-23 (2,640 days); MVP tags present (157,092 / 227,576); Binance stocks/commodities
present (AAPL/TSLA/MSTR/NVDA/XAU/XAG); `compute_honest_coverage` SSOT exists + deployment-api aligns.
RED: **3 day-gaps 06-19/20/21 silently absent** (99.9% is blind); **expected-universe not materialised** for missing
days; coverage is **per-(venue,day) shallow** (no depth); **per-venue cumulative count non-monotonic** (1000s of
day-over-day drops, unreconciled); **junk-symbol noise**; **daily-capture trigger (08:30) PAUSED**.
**MTDS cefi is PAUSED** (no backfill fleet running) pending this foundation.

---

## Phase 0 — cross-cutting foundations (block G2; build once, reused by every AG)

- [ ] [INFRA] P0. **Observability wiring (§0.5) for every instruments/MTDS backfill VM + roll-up job** — register as a
      classified `DeploymentTarget` (`classify_deployment_target` + `cloud_run_job_registry` / VM `lifecycle_class`),
      `ServiceBootstrap` + `log_event` + 60s `PIPELINE_HEARTBEAT` + ≥1 progress/hr, error→`#data-pipeline-alerts`,
      terminal `exit_code` + log-mtime persisted, **appears in `/deployments` BATCH tab with click-through to logs**.
      DoD: a launched job is click-through-able in the cockpit; SSH not required. SSOT:
      `codex/05-infrastructure/deployment-observability.md`.
- [ ] [SCRIPT] P0. **Layered coverage via the SSOT (day + depth)** — implement `day_coverage` + `depth_coverage` (§2)
      strictly through `compute_honest_coverage`, with the **expected-universe materialised** (missing days/instruments
      seeded `expected_unattempted`, gaps = 0% not absent). Surface BOTH per-AG/per-venue in manifest → `/data-status` →
      deployment-API → deployment-UI. **No ad-hoc coverage scripts** that diverge from the UI. DoD: UI shows day+depth
      per venue; a synthetic gap drags day_coverage down.
- [ ] [SCRIPT] P0. **Cumulative-drawdown health metric (§1.2)** — per venue, the cumulative-instruments-ever-seen series;
      any negative day-over-day delta = a hard defect (flag + block). Active-count drops must net to a typed reason
      (cefi/tradfi delisting; DeFi delisting OR `NOT_ENOUGH_TVL`). DoD: drawdown count per venue surfaced; target zero.
- [ ] [DESIGN] P1. **Expected-universe ORACLE design (§2.1)** — the `depth_coverage` denominator: (a) per-instrument
      true genesis from **venue truth** (not circular first-seen); (b) **time-varying futures expiry/listing rules** per
      venue, versioned by effective-date, in UAC. Ship **Tier-A proxy** first (labelled), **Tier-B truth** is the
      completion bar. DoD: design doc + the UAC rule-registry shape; sourcing decision for venue-truth genesis.
- [ ] [SCRIPT] P0. **Consolidation reconcile (§2.2)** — incremental for steady-state + **scoped `--force`/reconcile**
      after any backfill + periodic, reconciling **actual shards vs the materialised expected-universe** to *discover*
      unexpected-missing shards (→ 0% in day_coverage + re-fetch queue). Never a blind whole-corpus `--force` (clip the
      window; purge discipline vs the 32Gi OOM). DoD: a deleted/absent expected shard is surfaced as a gap, not silently
      merged-around.
- [ ] [SCRIPT] P0. **Drilldown-correctness guard (§2.3)** — (1) UI renders the SSOT value, never recomputes; (2)
      **reconciliation guard**: independent raw-GCS recompute == manifest/SSOT/UI (ε=0), wired as a QG step + watchdog →
      `#data-pipeline-alerts` on drift; (3) manifest-freshness watchdog + per-cell click→GCS traceability. DoD: a seeded
      manifest/raw divergence trips the guard; cockpit number is proven == ground-truth.

🚦 **GATE 0 — operator sign-off on Phase 0 before any backfill launches.**

---

## Phase 1 — cefi (FIRST), gated G1→G5

- [ ] [SCRIPT] P0. **G1 — instruments-service correct per-day** (mtds/instruments-service): code right + deterministic +
      on LDR + QG-green; single-day re-run byte-reproducible; **junk/test symbols rejected** at capture; per-instrument
      fields (available_from, type, symbol, MVP, universe-tag) correct. DoD: a sample day audited cell-correct.
- 🚦 **GATE G1 — sign-off.**
- [ ] [INFRA] P0. **G2 — backfill cefi all venues × all days × all years** (observable BATCH, un-pause + verify the
      daily 08:30 capture). DoD: **`day_coverage = 100%`** (no day-gaps incl. 06-19/20/21); cumulative monotonic (zero
      drawdowns); weekly type+symbol completeness; universe depth (MVP+Expanded+Binance-stocks/commodities); cockpit
      click-through green.
- 🚦 **GATE G2 — sign-off.**
- [ ] [SCRIPT] P0. **G3 — aggregate + verify the scheduler runs the latest code** — `build_instrument_catalogue.py` via
      `lifecycle-catalogue-regen-cefi` (01:00 UTC); verify the Cloud Run **image == latest LDR/main**, fired today,
      produced today's `catalog.parquet`, no silent staleness. DoD: catalogue available_from/available_to/MVP
      sample-correct; scheduler proven on latest code.
- 🚦 **GATE G3 — sign-off.**
- [ ] [SCRIPT] P0. **G4 — MTDS filters the catalogue per-day** — capture only catalogue-active-for-day instruments (no
      pre-listing, no post-expiry, no out-of-universe). DoD: spot-check MTDS attempts == catalogue-active-for-day.
- 🚦 **GATE G4 — sign-off, THEN resume cefi MTDS backfill (observable BATCH).**
- [ ] [SCRIPT] P0. **G5 — verify cefi MTDS coverage rises** (day+depth via SSOT) day-by-day; residual gaps each have a
      typed understood reason. DoD: coverage trends up; no new unexplained honest-absence/failed.
- 🚦 **GATE G5 — sign-off; cefi DONE.**

---

## Phase 2+ — defi · tradfi · sports (same G0→G5, after cefi DONE)

- [ ] [INFRA] P1. **defi** — same gates; DeFi `NOT_ENOUGH_TVL` active-drop nuance (§1.3); venue-launch-date genesis.
- [ ] [INFRA] P1. **tradfi** — same gates; Databento universe (GLBX/DBEQ/XCBF); ("tradfi perps" = Binance single-
      stocks/commodities are **cefi**).
- [ ] [INFRA] P1. **sports** — same gates; per-league fixtures universe.

---

## Operator gates (the sign-off points — ask every time)

GATE 0 (Phase 0 done) · G1 · G2 · G3 · G4 · G5 per AG. No gate is crossed without operator sign-off. No parallel-up
across gates within an AG.

## Codex SSOT updates

- NEW: `codex/02-data/instruments-foundation-and-catalogue-completeness.md` (the standard) — this plan executes it.
- CLAUDE.md: add a one-line pointer to the standard.
- Compose: `availability-manifest-and-data-status.md` (expected-universe materialisation) ·
  `deployment-observability.md` (§0.5) · `honest_coverage_formula_consolidation_2026_05_19.md` (SSOT) ·
  `foundation-completion-gate-discipline.md`.

## Progress log

- 2026-06-24 — Reset to foundation-first (operator). cefi MTDS paused. cefi instruments ground-truth audit done
  (read-only). Codex standard drafted + enriched (gated order · observability precondition · layered coverage ·
  expected-universe oracle · cumulative-drawdown · DeFi-TVL). This plan filed. **Awaiting GATE 0 sign-off.**
