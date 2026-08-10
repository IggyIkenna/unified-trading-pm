---
doc_type: codex-ssot
title: Cloud spend forecast + Google Cloud credits position (2026-08-09)
summary: >-
  Measured GCP/AWS spend to 2026-08-09, the measured agent-fleet token volume (3.55T tokens/yr) that sits OUTSIDE the
  cloud bill on flat-fee subscriptions, the promotional-credit coverage map (which services get credit and which get
  none), and the 12-month consumption forecast built for the Google Cloud negotiation. Records the FINAL commercial
  position — a bespoke THREE-YEAR tapering deal at 80/50/30% ($2.0M gross, $870k support, $1.13M paid to Google), NOT a
  startup-programme application — against a declined-case fallback of ~$1k/mo (bulk storage only) with compute split
  across AWS and Azure. Section 5 records the DART-led restructure of the client-facing deliverable, the verified
  public-positioning facts it may assert, the consultancy-risk mitigations, what was deliberately REMOVED, and the two
  claim-accuracy rulings (strategy-catalogue count dropped; Vertex/GPU/BigQuery never used).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [cost, credits, gcp, aws, vertex-ai, forecast, finops, commercial]
related:
  [
    /codex/11-project-management/dual-cloud-cost-ops-playbook.md,
    /codex/05-infrastructure/billing-cost-observability.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-08-09
authoritative_for:
  [
    measured cloud spend baseline as at 2026-08-09,
    measured agent-fleet token volume and its unit economics,
    google cloud promotional-credit service-coverage map,
    12-month cloud consumption forecast scenarios 2026-09..2027-08,
    google-facing deliverable structure and the positioning facts it may assert,
  ]
referenced_by: []
owner:
last_reviewed: 2026-08-09
code_refs:
  [
    unified-trading-pm/scripts/finops/measure_agent_fleet_tokens.py,
    unified-trading-pm/scripts/finops/cloud_spend_forecast_2026_08.py,
    unified-trading-pm/scripts/finops/llm_and_research_unit_economics.py,
  ]
---

# Cloud spend forecast + Google Cloud credits position (2026-08-09)

> **CODEX-PRIVATE / commercially sensitive.** Prepared for the Google Cloud credits + committed-use conversation. Client
> names, mandates and fee structures were deliberately EXCLUDED from the external deliverable — do not add them.
>
> **Positioning SSOT for anything client-facing is <https://www.odum-research.com>, not this doc.** Section 5 records
> what was verified there on 2026-08-09 and what must NOT be asserted without re-verifying. Quickmerge could not commit
> from this host (4/4 failures, see `/plans/active/issues/quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md`);
> this doc and the `code_refs` tooling landed via a path-scoped `git commit` instead.
>
> **Client-facing deliverable**: <https://claude.ai/code/artifact/4b2f07d2-2db2-4b07-a388-c6158af593c2> (private
> artifact; share link from the artifact page). Repo copy of record:
> `/codex/11-project-management/cloud-spend-forecast-2026-08.html` — its provenance header carries the five editing
> traps, including the mandatory `node --check` on the extracted inline script. Regenerate numbers with the
> `scripts/finops/` tooling in `code_refs`, never by hand.

## 1. Measured actuals (the anchor)

GCP billing export `central-element-323112.billing_export.gcp_billing_export_v1_016B25_109840_AF2ACB`, queried
2026-08-09. **The account bills in GBP** — USD is `SUM(cost / currency_conversion_rate)` per row.

| Month              | GCP gross USD                  | GCP net USD | AWS USD       | Note                                         |
| ------------------ | ------------------------------ | ----------- | ------------- | -------------------------------------------- |
| 2026-01            | —                              | —           | 153           | **GCP billing export not yet enabled**       |
| 2026-02 .. 2026-04 | **~90,000** (operator records) | —           | 16 / 170 / 18 | **PRE-EXPORT. Real spend, not in BigQuery.** |
| 2026-05            | 14,466                         | 13,280      | 5             | Platform build-out begins                    |
| 2026-06            | 19,017                         | 16,060      | 36            | Multi-asset-group backfill                   |
| 2026-07            | 20,147                         | 16,246      | 1,020         | AWS CI runner fleet stands up                |
| 2026-08 (1-9)      | 7,707                          | 4,098       | 1,036         | Partial month                                |

- **Aug-2026 exit run-rate: ~$26,000/mo combined** (GCP ~$24,300 trimmed daily mean + AWS
  $1,700).
  Trimmed = 1-8 Aug excluding the single highest day (8 Aug ran ~2.5x normal on a backfill wave). Untrimmed GCP would
  read $28,200/mo
  — **the conservative reading was used deliberately.**
- **AWS is $1,700/mo** (operator-confirmed after rightsizing, 2026-08-09), decomposing as **self-hosted CI VM $550 + AO
  orchestrator $1,000 + ~$200 misc — ALL of it migrating to GCP.** GitHub Actions
  ~$60/mo sits outside this and is
  unchanged by migration (not GCP spend). The measured 2-8 Aug daily mean implied $3,300/mo
  before the cut.
- **GCP CI spend runs ALONGSIDE the self-hosted VM, not instead of it**: Cloud Build
  $878/mo + Artifact Registry
  $199/mo (measured Aug). Operator-confirmed 2026-08-09.
- **PRE-EXPORT SHAPE (operator records, 2026-08-09)**: the annual credits programme ran ~15 months to Apr 2026,
  ~$90k total. NOT flat — Nov-Feb averaged **~$4,600/mo (~all credit)**; **Mar 9-Apr 30 alone was ~$30k gross /
  ~$20k
  net**, i.e. credit was already covering only ~1/3 before the programme formally ended. Then
  $61,422
  measured 1 May-9 Aug. **August projects to ~$23,000 gross.** **Feb-Apr is NOT immaterial** — an earlier draft
  called it "pre-ramp" and wrong. The export was enabled 2026-04-30 and is not retroactive; certify the Feb-Apr figure
  from Cloud Billing console → Reports → group by month → export CSV before quoting it externally.
- Estate at measurement: **112 TB across 79 buckets**. GCS cost splits ~48% object operations / ~30% stored bytes / ~22%
  retrieval — **it tracks pipeline throughput, not corpus size.**
- **`deployment-scripts-*` holds 51 TB** of accumulating deployment tarballs with no lifecycle rule. Real cleanup owed.

## 2. Measured agent-fleet token volume (the biggest single finding)

Measured from Claude Code transcripts, 7 complete days (2026-08-02..08), via
`scripts/finops/measure_agent_fleet_tokens.py`:

| Token class      | 7-day  | Share  |
| ---------------- | ------ | ------ |
| cache_read       | 53.59B | 98.3%  |
| cache_write      | 0.80B  | 1.5%   |
| output           | 0.10B  | 0.19%  |
| input (uncached) | 0.001B | 0.002% |
| **total**        | 54.49B | —      |

- **7.8B tokens/day on the orchestrator alone**; operator estimate +25% from the two operator laptops.
- **Fleet ≈ 296B tokens/month ≈ 3.55 TRILLION/year.** ~355k cached tokens per request; ~21k assistant turns/day.
- **This runs on 6 Claude + 1 DeepSeek accounts at ~$1,500/mo — entirely OFF the cloud bill.** The DeepSeek account
  matters commercially: we already run a mixed-model fleet, so Model Garden routing is not hypothetical.

### Unit economics (`llm_and_research_unit_economics.py`)

| Basis                                              | $/month | $/year    | vs today |
| -------------------------------------------------- | ------- | --------- | -------- |
| ACTUAL: 6 Claude + 1 DeepSeek account              | 1,500   | 18,000    | 1.0x     |
| Anthropic API standard $3.00/$15.00, +10% regional | 126,146 | 1,513,800 | **84x**  |
| Vertex published card $2.20/$11.00                 | 94,478  | 1,133,700 | 63x      |
| 50% open-weight Model Garden + 25% batch           | 76,690  | 920,300   | 51x      |
| 80% open-weight + 30% batch                        | 54,863  | 658,400   | 37x      |
| **Risk case: no effective cache tier**             | 604,165 | 7,250,000 | 403x     |

- Blended effective rate paid today ≈ **$0.005 per million tokens** vs list ≈ **$0.43/M**.
- **FORECAST BASIS**: Max-tier accounts roughly HALVE the effective rate. Standard GCP/Vertex terms = **2x =
  $3,000/mo**
  (a 10% discount would put it ~$2,700, so
  $3,000 is the conservative side). Bucket also carries the $1,000/mo AO orchestrator VM = **~$4,000/mo combined** at
  current fleet size.
- The Sonnet-5 introductory rate ($2.00/$10.00) **expires 2026-08-31 — before the forecast window opens.** Use standard.
- Opus 5 on Vertex assumed at first-party parity ($5/$25) **pending a quote** — only 3.6% of the token mix.
- **Prompt caching is the load-bearing assumption.** At 98% cache reads, losing the 0.1x read multiplier is a 6x swing.

## 3. Promotional-credit coverage map (what to point the discount ask at)

Recurring monthly `PROMOTION` credit, `tier-0` (single grant id, epoch suffix rolls monthly). **Not service-restricted,
but it does not reach everything.**

| Month   | Credit USD | Coverage of gross                                                       |
| ------- | ---------- | ----------------------------------------------------------------------- |
| May     | 1,091      | 7.5%                                                                    |
| Jun     | 2,896      | 15.2%                                                                   |
| Jul     | 3,784      | 18.8%                                                                   |
| Aug 1-9 | 3,573      | 46.4% (**bucket drained inside the first week; list price thereafter**) |

**Covered** (1 May-9 Aug, USD gross → credit): Compute Engine 22,319→4,009 · Cloud Run 20,844→4,005 · Cloud Storage
14,588→2,503 · Cloud Build 1,599→329 · Artifact Registry 808→253 · Memorystore 363→99 · Pub/Sub 247→79 · Cloud SQL
118→32 · Scheduler/Secret Manager/KMS (small).

**ZERO coverage — where the ask must point:**

| Service                      | Today                     | Why it matters forward                                             |
| ---------------------------- | ------------------------- | ------------------------------------------------------------------ |
| **Vertex AI / Model Garden** | $0                        | The whole agent-fleet migration; $0.9-1.5M/yr list value           |
| **GPU / accelerators**       | $0                        | Gates the ML line ($36k → $223k across scenarios)                  |
| **Networking / egress**      | $225 gross, **$0 credit** | Only material live service with no coverage; grows on multi-region |
| **BigQuery**                 | ~$0                       | Grows with client analytics + external research users              |

## 4. Forecast scenarios (2026-09 .. 2027-08)

Eight cost lines, each anchored to its measured Aug-2026 value and grown against a named physical driver. Full monthly
detail: `scripts/finops/cloud_spend_forecast_2026_08_monthly.csv`.

| Scenario     | 12-mo USD   | 12-mo GBP   | Exit $/mo   | x today  | Infra only (ex agent-LLM) |
| ------------ | ----------- | ----------- | ----------- | -------- | ------------------------- |
| Conservative | 426,970     | 321,200     | 40,500      | 1.6x     | 355,570                   |
| **Base**     | **815,000** | **613,000** | **103,500** | **4.0x** | **721,900**               |
| Ambitious    | 1,788,900   | 1,345,600   | 269,500     | 10.3x    | 1,664,900                 |

**Research backtesting is the #2 line** and scales as (archetypes in research) x (universe width). Operator cadence: 10
backtests/archetype/day · ~1,000 backtests to take one strategy live · 1 T+1 batch=live reconciliation per live
archetype/day. Per-backtest ~$0.60 narrow universe, ~$8.50 full pool. Exits at $10.7k / $39.3k / $120k per month.

### Modelling decision to preserve

**The agent-LLM line is DERIVED, not list-priced.** Operator derivation (2026-08-09):

```
current spend (6 Claude Max accounts)          $3,000/mo
  x 2.0   standard Anthropic rate limits cost ~2x Max-tier economics
  x 0.9   10% discount
  = 1.8x  ->  ~$5,400/mo at current fleet size, scaling with fleet growth
```

Giving **$59.4k / $77.1k /
$103.8k** of token spend. The `agent_llm` bucket also carries the **AO orchestrator VM
($1,000/mo today on AWS,
migrating, scaling with fleet)** — total bucket **$71.4k / $93.1k /
$124.0k**. This is NOT the metered-list cost of the measured
volume ($76k-126k/mo) — a forecast line asserting we would
pay $1.1M/yr for something we currently get for $36k/yr is a fiction and would discredit the whole document. **The ~20x
gap between the derived line and metered list IS the credit ask**, stated separately. An earlier draft priced the line
at list and was corrected on operator challenge ("40k per month weird we spend 3k").

### Two further corrections applied 2026-08-09 (both material)

- **`batch_pipeline` is EPHEMERAL backfill AND its steady state is tiny.** An early draft ran it flat at
  $13-24k/mo for
  twelve months. Operator sizing (2026-08-09): each month processes 30 days of new data ≈ **2% of the historical
  corpus**; live streaming through IS/MTDS/rest-of-pipeline adds a similar volume again ⇒ ongoing monthly cost ≈ **6% of
  the one-time backfill cost** ≈ **~$400/mo
  incremental backfill + ~$400/mo live streaming = ~$800/mo steady state**. Of the
  ~$151k spent on GCP to date the operator judges **~90% to be ONE-OFF build-out** — initial backfill, pipeline
  migrations and re-processing as the schema settled — **not recurring operating cost**. That is normal for a platform
  in build-out and should be framed as non-recurring, NOT as waste (operator direction 2026-08-09). Correcting this cut the base case by ~$212k
  across two passes. **RECONCILED 2026-08-09**: the ~$150k figure is real and is ~$90k (Feb-Apr, pre-export) + $61.4k
  (measured, May-Aug) — it was NOT a discrepancy with the export, just a wider window than the export covers.
- **`ml_train_infer` is GPU-based** from the point accelerators land. CPU training today is a cost workaround, not a
  design choice — which is precisely why GPU quota + pricing in `asia-northeast1` is a named ask.

### The ask, as structured — FINAL POSITION (2026-08-09)

The forecast scenarios below are supporting evidence. **The proposal itself is a single structure:**

|                                            | Monthly     | Annual       |
| ------------------------------------------ | ----------- | ------------ |
| Gross consumption on GCP                   | **$25,000** | **$300,000** |
| Net paid by Odum                           | **$5,000**  | **$60,000**  |
| Credit / committed-rate treatment required | **$20,000** | **$240,000** |
| **Effective discount**                     | **80%**     | **80%**      |

**If declined**: Google Cloud reduces to
**~$1,000/mo** — bulk storage only, which is genuinely best-in-class and which
we keep. Compute, model inference and CI split across **AWS and Azure** by where each workload prices best. Google's
revenue from us falls from ~$24,000/mo
to ~$1,000/mo. Framing agreed with the operator: state plainly that we do NOT want the three-way split (more surfaces to
secure, more billing to reconcile, engineering weeks lost) but will do it if the arithmetic does not close.

**$25,000/mo is a FLOOR, not a ceiling** — August already tracks ~$23,000. The scenario model shows the same workload
reaching $99,700/mo in the Ambitious case (the committed Base plan itself exits at $28,100/mo — see § "Scenario model
RE-ANCHORED" below). Gross above $25k is upside for Google, not a larger ask from us.

### Committed run-rate composition (the $25k/mo, by cost line)

| Cost line                                | Gross $/mo | Net at 80% |
| ---------------------------------------- | ---------: | ---------: |
| Data capture & storage                   |      6,000 |      1,200 |
| Strategy research & backtesting          |      5,000 |      1,000 |
| Agent LLM inference + orchestrator VM    |      4,000 |        800 |
| Paper, live trading & T+1 reconciliation |      3,500 |        700 |
| ML training & inference (GPU)            |      2,500 |        500 |
| CI/CD & orchestrator infrastructure      |      2,000 |        400 |
| Batch pipeline (steady state)            |      1,200 |        240 |
| Analytics & client platform              |        800 |        160 |
| **Total**                                | **25,000** |  **5,000** |

Deliberately NOT today's mix: backfill collapses 13,000 -> 1,200 and research takes its place. Storage being the largest
line is what makes the fallback position coherent — it is the one thing worth keeping on GCP regardless.

### Named service asks (zero credit coverage today)

Vertex AI / Model Garden · GPU accelerators in `asia-northeast1` · Networking/egress (only material live service with $0
coverage) · BigQuery. Plus AWS migration support and Spot/Batch job-shaping guidance.

### Scenario model — RE-ANCHORED 2026-08-09 (operator ruling; supersedes the model's own labels)

**The committed plan IS the base case.** The operator rejected the earlier presentation twice: first because the plan
sat _below_ a "base" case, which reads as asking for less than our own conservative estimate; then again because a
relabel alone still left three lines. Final structure in the deliverable is exactly three series:

| Series in the deliverable                   | 12-mo gross | Exit $/mo | What it is                                           |
| ------------------------------------------- | ----------: | --------: | ---------------------------------------------------- |
| **Base — the committed plan** (the ask)     |     300,000 |    28,100 | $20.7k→$28.1k/mo; what the taper is priced on        |
| **Ambitious — same roadmap, unconstrained** |     780,300 |    99,700 | was the model's "base"; now the upside line          |
| **No arrangement — GCP reduced to storage** |      32,750 |     1,000 | $5k/mo decaying to $1k as compute moves to AWS+Azure |

**Mapping back to `cloud_spend_forecast_2026_08.py`** (the script's labels are now STALE — do not quote them raw):

- script `base` (780,300) → deliverable **"Ambitious"**
- script `ambitious` (1,740,400) → **DROPPED ENTIRELY.** It dwarfed the other lines, forced the y-axis to
  $300k and
  squashed the committed plan onto the axis; it was also never the ask. Dropping it rescaled the chart to $125k
  and made the plan legible.
- script `conservative` (162,860, a
  $13k/mo self-imposed cap) → **DROPPED**, superseded by the measured declined-case
  position (~$1k/mo storage-only).
- deliverable **"Base"** (300,000) is NOT in the script at all — it is the quarterly service-family plan from section 4.

**If the script is re-run, re-label its output to match this table** or the deliverable and the tooling will disagree.
The reconciliation that makes the whole document hang together: _ambitious reaches within twelve months a scale the
committed plan does not reach until year three ($780k vs the plan's $600k in Y2, $1.1M in Y3)_ — same roadmap, different
speed, so funding changes WHEN Google's consumption arrives, not WHAT gets built.

## 5. Deliverable restructure — DART-led narrative (2026-08-09, second pass)

The deliverable was rewritten the same day after reviewing the live public positioning at
<https://www.odum-research.com>. **The numbers did not change; the story around them did.** The first draft read as "we
run a lot of AI agents and therefore need compute credits" — an internal engineering-productivity pitch. It now reads as
"Odum has built regulated institutional trading infrastructure and Google Cloud is the layer it scales on."

**Positioning facts, verified on the live site — use these, do not re-derive or invent:**

| Fact                                                                                                                                  | Source                      |
| ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| FCA-authorised, firm reference **975797**, regulated since **2023**                                                                   | site header + `/regulatory` |
| Tagline: "Trading infrastructure tailored to your ambition"                                                                           | `/` hero                    |
| **DART** is the named product (`/platform`)                                                                                           | nav + `/platform`           |
| Spine: RESEARCH → EXECUTION → MONITORING → REPORTING → GOVERNANCE                                                                     | `/`                         |
| Markets: digital assets, traditional, **sports and prediction markets**                                                               | `/` standfirst              |
| DART's three delivery modes: client-provided signals · full research-to-execution · Odum-provided signals                             | `/platform`                 |
| Five engagement routes: build new · consolidate fragmented · bring-your-own-IP · regulated operating models · Odum-managed strategies | `/` cards                   |
| "We operate one codebase across research, execution, reporting, and compliance"                                                       | `/` — why-Odum              |

**Structure now**: six main sections (proposition · DART · why consumption grows · the twelve-month forecast · the case
for Google · why Google specifically) + a five-part technical appendix (agent-fleet measurement · research unit
economics · credit coverage · scenario model · method and caveats). Detail lives in the appendix so the commercial
reviewer never has to read it.

**The forecast is now presented by GCP service family, not by internal cost line.** The internal 8-bucket view moved to
appendix D. Quarterly plan (monthly average within each quarter, `x3` for the quarter; sums to exactly $300,000):

| Service family                      |         Q1 |         Q2 |         Q3 |         Q4 |        Year |
| ----------------------------------- | ---------: | ---------: | ---------: | ---------: | ----------: |
| Compute — CE, Cloud Run, Batch, GKE |      9,800 |     10,400 |     10,900 |     11,100 |     126,600 |
| Cloud Storage                       |      5,500 |      5,900 |      6,500 |      6,700 |      73,800 |
| Vertex AI + accelerators            |      3,800 |      5,800 |      6,600 |      7,000 |      69,600 |
| Networking, Pub/Sub, databases      |      1,300 |      1,900 |      1,900 |      2,200 |      21,900 |
| BigQuery + client analytics         |        300 |        500 |        800 |      1,100 |       8,100 |
| **Total /mo**                       | **20,700** | **24,500** | **26,700** | **28,100** | **300,000** |

**Post-credit picture added** (the investment case Google actually evaluates): Year 1
$300k credit-supported → Year 2
$600k → Year 3
$1.1M, labelled illustrative. The argument is that **the workload is not created by the credit** — it
exists and is growing; the credit only determines where it runs. Demand ($780k
base case) already exceeds the ask ($300k), so the credit converts deferred work into consumption rather than funding a
workload that evaporates on expiry.

### REMOVED from the deliverable — do not reintroduce (operator ruling 2026-08-09)

- **The "7 Claude accounts → 2" optimisation narrative.** An internal efficiency KPI, not an investment thesis.
- **All discussion of OpenRouter / DeepSeek / Kimi / Qwen / Groq / open-weight routing / "route to cheapest provider".**
  Reads to a cloud vendor as three pages explaining how hard we plan to avoid paying them. Stay model-agnostic
  internally; do not advertise it.
- **Client, mandate and counterparty detail** (unchanged from the first pass — still excluded).

### This is NOT a startup-programme application — operator ruling 2026-08-09

**Odum already holds the Scale tier.** This is a **bespoke three-year commercial negotiation with the account team**.
That closes several questions a later session would otherwise re-open after reading Google's public programme pages:

- **The 5-year incorporation rule does NOT apply** (Odum Research Ltd incorporated 2021-07-27 — irrelevant here).
- **Scale-tier / AI-first-tier caps do NOT apply.** $200k-over-2yr and $350k-over-2yr are programme numbers.
- **DO NOT contort the Gemini story to qualify for the AI-first tier.** There is no tier to qualify for. The honest
  boundary stands: the agentic layer runs in production against Odum's OWN research and engineering; the client-facing
  surface is roadmap and labelled as such. Chasing a tier was the only reason to overstate it; that reason is gone.

### The proposal — TAPERING three-year structure (SUPERSEDES the flat one-year 80% framing above)

| Term                        |         Gross | Discount | Google support |     Odum pays |
| --------------------------- | ------------: | -------: | -------------: | ------------: |
| Year 1 (2026-09 .. 2027-08) |       300,000 |      80% |        240,000 |        60,000 |
| Year 2                      |       600,000 |      50% |        300,000 |       300,000 |
| Year 3                      |     1,100,000 |      30% |        330,000 |       770,000 |
| **Three-year total**        | **2,000,000** |  **44%** |    **870,000** | **1,130,000** |

**The two numbers that carry the pitch**: Google's annual support is roughly FLAT (240k → 300k → 330k, +37%) while
Odum's annual cash payment grows **12.8x** (60k → 300k → 770k). By year three Google collects more cash from Odum in one
year than it extended in support across the first two. Years 2-3 gross are planning figures — labelled as such, never
presented as commitments.

### Consultancy-risk mitigation (from external review — genuinely material, keep these)

Google's startup guidance excludes dev shops, consultancies and agencies. Odum's own site language ("five engagement
routes", "scoped engagements", "reviewed case by case") is correct on the site but reads as a consultancy to a Google
reviewer. Applied to the deliverable:

- Opens "DART is Odum Research's institutional capital-markets technology platform" + an explicit **"It is a platform,
  not a consulting engagement"** paragraph (multi-tenant core; onboarding configures, does not fork).
- "Three delivery modes" → **"Three deployment configurations of one platform"**.
- The "five entry routes" bullet REPLACED with a data-gravity bullet.
- "client / mandate" → "institutional user" wherever it referred to platform usage.

### Other integrations from the same review (all applied)

- **AI control-boundary model** — probabilistic agentic research → validation/approval gate (tests, backtests, promotion
  ladder, human approval) → deterministic production (pre-trade risk, position limits, capital isolation, T+1 recon,
  kill switches). Headline: **no language model reaches capital.** True, and the single best de-risking argument for a
  high-consequence domain.
- **Institutional control requirements table** (IAM, client isolation, KMS custody, gated deploys, risk controls, audit,
  residency) — argues why this is a Google Cloud decision, not a GPU-price decision.
- **Data gravity** as the stickiness argument. **FCA wording tightened** so authorisation is not implied to endorse
  DART, Google or any venue.

### Two claim-accuracy rulings — operator, 2026-08-09

- **"2,000+ strategy catalogue" was TRIED, then DROPPED.** It briefly ran as a hero tile, but it is not on the live site
  and not derivable from anything measured here — the only uncertifiable claim in a document whose credibility rests on
  everything else being measured. The tile now reads **"Hundreds — of systematic strategy variants across five asset
  groups"**. **Do not reinstate a specific count** without a verifiable source; the marginal persuasive value of
  "2,000+" over "hundreds" is small and the downside if a reviewer probes it is not.
- **Vertex AI, GPU/accelerators and BigQuery have NEVER been used — spend is nil, coverage is nil.** The operator
  queried this on reading the draft, which is the signal that a Google reviewer could misread it too. The credit table
  now renders those rows as an em-dash (not `$0`) and labels them **NOT YET USED**, and the caption states outright that
  they are absent rather than under-covered. **Keep that distinction** — it is the entire forward ask, and it is also
  the thing most easily misread as "we already tried Vertex and spent nothing".

### Remaining operator-owned item

- **Mar 9 – Apr 30 at ~$30k gross / ~$20k net is an estimate**, not export-derived — the only unmeasured figure left.
  Certify from the Cloud Billing console if a certified number is required.

## 6. Lessons + traps (do not re-learn these)

- **Flat-fee subscriptions hide enormous consumption.** Nobody had the token number before this measurement; it turned
  out to be the largest single item in the forecast. Re-measure before any renewal or migration decision.
- **`cache_read` dominates (98%).** Any token report that shows only input+output understates volume ~50x.
- **The GCP billing export is not retroactive** and started 2026-04-30 — do not assume history exists in BigQuery, and
  do NOT infer that missing months were small. Feb-Apr 2026 carried
  ~$90k that the export simply cannot see; an early
  draft dismissed the gap as "pre-ramp, immaterial" and was wrong by ~$90k.
  Ask the operator before characterising a data gap as immaterial.
- **The account bills in GBP.** Reporting raw `cost` as USD overstates by ~33%. Always divide by
  `currency_conversion_rate` per row.
- **The promo credit drains early in the month** once consumption exceeds the bucket — average coverage % is misleading;
  look at the daily burn.
- **Measured AWS ≠ current AWS.** Daily means over a window that includes a spin-up spike overstate the steady state;
  confirm with the operator before quoting.
- **Max-tier subscriptions are ~2x cheaper than standard rate limits** for the same work — so a subscription-to-cloud
  migration is a 2x step before any discount, not a 20x one. Do not derive the migration budget from metered list.
- **Do not model a finite job as a run-rate.** Backfill, migrations and one-off sweeps complete. Ask "does this recur?"
  of every line before annualising it — an early draft overstated the base case by ~$148k on this alone.
- **A single mismatched quote in inline JS blanks EVERY chart on the page.** 2026-08-09: adding a table to the
  deliverable's `<script>` closed a string with `"` that opened with `'`. The SyntaxError killed the whole script, so
  all three charts AND every dynamically-rendered table went blank while the static prose kept rendering — the page
  looked half-alive, not obviously broken. **ALWAYS extract the script and `node --check` it before publishing** (the
  recipe is in the HTML's provenance header). Validating the Python that WRITES the HTML is not the same as validating
  the HTML.
- **Assert-before-write saved us repeatedly.** The edit scripts asserted every anchor string existed before writing the
  file. Several runs failed mid-way on a stale anchor and wrote nothing — no partial corruption. Keep that pattern.
- **A publish can silently ship a stale file.** Twice an edit script failed its assert (wrote nothing) while the
  subsequent Artifact publish still ran, re-publishing the UNCHANGED file. Verify the edit landed before publishing.
- **Do not characterise a data gap as immaterial without asking.** An early draft called the pre-export window
  "pre-ramp, immaterial" — it was ~$90k, and the platform had been at production scale the whole time. The narrative
  claim "dormant until May" was flatly wrong and would have been embarrassing if the counterparty checked.
- **Ask which lines an intuition covers before concluding a model is wrong.** The operator's "$500k-1M aggressive"
  matched the infra-only band almost exactly; it simply excluded the agent-LLM line.
- **Operator intuition was calibrated on infra-only.** The stated expectation ("$500k-1M aggressive") matched the
  infra-only band almost exactly; it excluded the agent-LLM line entirely. Ask which lines an intuition covers before
  concluding a model is too aggressive.
- **READ THE COMPANY'S OWN PUBLIC POSITIONING BEFORE WRITING ANY EXTERNAL DOCUMENT.** The first draft was built entirely
  from internal telemetry and told an internal story ("we run a large agent fleet"). The live site tells a far stronger
  one — FCA-authorised since 2023, DART as a named product, five engagement routes, cross-asset coverage including
  sports and prediction markets. **None of that was in the first draft.** Cost: a full rewrite. `www.odum-research.com`
  is the positioning SSOT for anything client-facing.
- **`WebFetch` returns only the title on a JS-rendered site.** odum-research.com returned nothing but the `<title>` via
  WebFetch, which reads as "the site has no content" — it does not. Use Playwright (`browser_navigate` +
  `browser_evaluate` on `document.body.innerText`) for any SPA, and enumerate `a[href]` to find real sub-pages rather
  than guessing URLs (`/dart` and `/dart-trading-infrastructure` both 404; the real path is `/platform`).
- **`node --check` passing does NOT mean the chart is right — RENDER IT AND LOOK.** 2026-08-09: the rewrite's
  `niceTicks()` stopped at the last tick _below_ the data max, so `scaleMax` came out at $20k for $25k bars,
  $80k for
  $84.3k bars, and $200k for $263.5k bars. Because `svg { overflow: visible }`, the oversized bars escaped the
  plot area and overlapped the prose above the figure. The JS parsed cleanly and the arithmetic was correct — **the bug
  was visible only on screen.** Serve the file (`python3 -m http.server`) and screenshot it; assert `getBBox().y >= 0`
  against the viewBox as a cheap automated check.
- **Literal non-ASCII inside inline `<script>` mojibakes without a charset header.** Em-dashes in JS string literals
  rendered as `â€”` when served by `python3 -m http.server` (no charset). Entities in the static HTML were fine — only
  the script strings broke. Keep the inline script pure ASCII with `\uXXXX` escapes; it costs nothing and survives any
  serving context.
- **Charts that sample CSS custom properties must redraw on `data-theme` changes, not just `prefers-color-scheme`.** The
  viewer's explicit light/dark toggle stamps `data-theme` on `<html>` and fires no media-query event, so a
  `matchMedia`-only listener leaves stale grid/axis/ink colours from the previous theme. A `MutationObserver` with
  `attributeFilter: ["data-theme"]` is the fix.
- **A cost document for a vendor is a commercial document, not an engineering one.** Detail that proves rigour to a
  technical reviewer actively damages the pitch with a commercial one — and enumerating your cheapest-provider strategy
  to the provider is worse than merely verbose. Main document carries the case; appendix carries the proof.
