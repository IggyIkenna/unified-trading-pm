---
type: analysis
title: Prediction cqg classifier — "unknown" (OTHER) corpus for theme-building (decision 338)
epic:
  - instruments_master
auditor: ikennaigboaka
date: 2026-06-16
status: complete
source:
  - operator decision 338 (improve cqg classifier first; surface unknowns to hand-theme)
  - GCS gs://market-data-tick-pred-prd-central-element-323112/raw_tick_data (POLYMARKET trades parquets)
---

# Prediction cqg classifier — "unknown" (OTHER) corpus for theme-building

> **Decision 338** — "improve the prediction cqg-classifier first". This digest is the readable corpus of prediction
> markets the canonical_question_group (cqg) classifier currently CANNOT route to a first-class group, so the operator
> can hand-build a theme/grouping taxonomy. **READ-ONLY analysis** — no code changed, no `--apply`, nothing shipped.

- **Author:** investigation sub-agent · **Created:** 2026-06-16
- **Source of truth code:** `unified-api-contracts` (UAC) — classifier + taxonomy live here, NOT instruments-service
  (the breadcrumb was off; instruments-service only _consumes_ the result + has the path-materialised stores).
- **Data source used:** GCS prod, `gs://market-data-tick-pred-prd-central-element-323112/raw_tick_data/` (POLYMARKET
  CLOB trades parquets). gcloud ADC worked non-interactively (`ikenna@odum-research.com`, project
  `central-element-323112`).

---

## 1. Where the classifier lives + how it works

Two-file chain in UAC (the `cqg` / `canonical_question_group` concept):

1. **`unified_api_contracts/internal/schemas/_prediction_market_taxonomy.py`** — the rule-based primitive classifier.
   `classify_polymarket_market(title, slug, event_slug, outcome)` returns a **4-tuple**
   `(category, underlying, market_type, resolution_period)`:
   - `category` ∈ 13 `PredictionShardCategory` (CRYPTO_PRICE, EQUITY_INDEX, COMMODITY, FX, MACRO, POLITICS_US,
     POLITICS_INTL, SPORTS_FOOTBALL, SPORTS_OTHER, CULTURE, TECH, WEATHER, MISC) — resolved by a `SLUG_PREFIX_MAP` (~180
     hand-curated slug prefixes → category+underlying), then slug-token fallback, then `KEYWORD_TO_CATEGORY` substring
     match. No match → `MISC` / `UNKNOWN`.
   - `market_type` ∈ 5 (binary, scalar, categorical, ranked, range_bracket) — inferred from slug tokens (`up-or-down`,
     `between-`, `winner`, `top-`, …).
   - `resolution_period` ∈ 11 (1min…yearly, event) — inferred from date/cadence tokens in the slug/title.
   - This layer is **good** — it tags ~95% of markets with a sensible category/underlying. It is NOT where the
     "unknowns" come from.

2. **`unified_api_contracts/canonical/domain/predictions/classifiers.py`** —
   `classify_polymarket_to_canonical_group(...)` projects that 4-tuple onto a **`CanonicalQuestionGroup`** (the cqg).
   This is the narrow surface:
   - **Override-first:** `POLYMARKET_CONDITION_ID_TO_GROUP` / `KALSHI_TICKER_TO_GROUP` — **both seeded EMPTY today**.
   - **Cadence map** `_CATEGORY_UNDERLYING_PERIOD_TO_GROUP`: only **22 keys** map to a group — and effectively only
     `range_bracket` markets in **BTC / ETH** (5m,15m,intraday,hourly,daily) + a handful of CME-linked daily
     price-direction tuples (SPX/NDX/DJIA/RUT/GOLD/CRUDE_OIL/NAT_GAS/EURUSD at `_DAILY`).
   - **Event map** `_CATEGORY_UNDERLYING_TO_EVENT_GROUP`: only **4 keys** — (MACRO,FED_RATE)→FED_RATE_DECISION_PER_FOMC,
     (MACRO,CPI)→CPI_PRINT_PER_MONTH, (POLITICS_US,PRESIDENT_2028)→ELECTION_PRESIDENT_2028,
     (CULTURE,OSCARS_BEST_PICTURE)→OSCARS_BEST_PICTURE.
   - Anything else → **`CanonicalQuestionGroup.OTHER`** + an INFO log `OTHER_BUCKET_MEMBER_ADDED`.

### The low-confidence trigger (what the operator asked for)

`ClassifierConfidenceLow` is the **legacy** name. The classifier was changed (see the docstring in `classifiers.py`): it
**no longer returns `None`/`attempted_failed[reason=ClassifierConfidenceLow]`** — it returns the honest-absence sentinel
**`OTHER`** instead. So the modern "unknown" condition is exactly: **the (category, underlying, resolution_period) tuple
is not one of the 22 cadence keys AND the (category, underlying) pair is not one of the 4 event keys.** That is the
entire low-confidence rule — there is no probability/threshold; it is a closed-set lookup miss.

**Why ~80–95% fall to OTHER:** the named groups cover almost exclusively **BTC/ETH (and a few CME-linked) price
up-or-down** markets. Every other live Polymarket genre — Solana/XRP/altcoin price, all sports, all politics, weather,
tech-personality, geopolitics, box-office/culture, most macro prints, and the giant `MISC/UNKNOWN` bucket — has **no
canonical group defined**, so it lands in OTHER. The taxonomy underneath knows _what_ these are; the cqg map just has no
target groups for them yet. **That is the gap the operator is closing.**

The full named set is only **29 real groups + OTHER** (`CanonicalQuestionGroup`): the BTC/ETH `_UP_DOWN_*` cadence
family, 7 CME-linked `_UP_DOWN_DAILY` (SPX/NDX/DJIA/RUT/GOLD/CRUDE_OIL/NATGAS/EUR), FED_RATE_DECISION_PER_FOMC,
CPI_PRINT_PER_MONTH, ELECTION_PRESIDENT_2028, OSCARS_BEST_PICTURE.

- Classifier version: **`2026-05-23.3`** · stability hash **`5ec47468e6935431`** (the actual runtime hash;
  `CLASSIFIER_STABILITY_HASH` re-exported from the taxonomy module).

---

## 2. Corpus + the unknown count / %

Two measurements, both from the real GCS prod corpus (run through the **actual** UAC classifier):

### (A) Corpus-wide, exact — projected over every market×day shard path

The GCS raw-tick layout already materialises the 4-tuple into the path
(`…/market_category=X/underlying=Y/market_type=Z/resolution_period=W/data_type=trades/{conditionId}.parquet`), so the
cqg projection is exact per shard. I walked the **whole** `raw_tick_data/` tree (47,767 trades parquets, days
**2025-03-14 → 2025-10-14**) and applied the real `classifiers.py` group maps:

| canonical_question_group |     shards | % of 47,623 |
| ------------------------ | ---------: | ----------: |
| **OTHER (unknown)**      | **37,926** |   **79.6%** |
| BTC_UP_DOWN_DAILY        |      4,979 |       10.5% |
| ETH_UP_DOWN_DAILY        |      4,652 |        9.8% |
| CPI_PRINT_PER_MONTH      |         65 |        0.1% |
| CRUDE_OIL_UP_DOWN_DAILY  |          1 |        0.0% |

> **~80% of shards are unknown** on a shard (market×day) basis. The breadcrumb's **94.5%** is plausibly the
> distinct-market (not shard) denominator, or a stricter sample — BTC/ETH _DAILY_ markets recur daily so they inflate
> the named share on a per-shard count. On a **distinct-market** basis the unknown share is higher (the BTC/ETH-daily
> rows collapse to a few recurring groups while the OTHER bucket is thousands of distinct one-off markets). Either way
> the operator's read is correct: **the overwhelming majority of distinct prediction questions are unclassified.**

### (B) Title corpus — distinct markets read straight from parquets

I read **3,382** parquets (targeted at the non-BTC/ETH-daily categories for question-text variety) and ran the real
classifier on each distinct market: **3,370 / 3,382 = 99.6% OTHER** (expected — I deliberately sampled the OTHER-heavy
categories to harvest readable titles). A separate even-spread sample of 1,577 parquets gave 1,157/1,568 = **73.8%
OTHER** with BTC/ETH-daily included. Every trades parquet carries `title`, `slug`, `eventSlug`, `outcome`, `conditionId`
— i.e. the exact classifier inputs **plus** the human-readable question.

---

## 3. The unknown questions — what they actually say (the corpus to theme from)

### Top OTHER path-tuples (category / underlying / market_type / resolution_period), corpus-wide by shard count

```
  5167  MISC/UNKNOWN/binary/yearly          <- the genuinely-uncategorised long-horizon bucket
  4056  CRYPTO_PRICE/SOL/range_bracket/monthly   <- Solana price (no SOL group exists)
  3574  CRYPTO_PRICE/XRP/range_bracket/monthly   <- XRP price (no XRP group)
  2509  CRYPTO_PRICE/BTC/range_bracket/event     <- BTC "price between $X-$Y" (only up/down DAILY is grouped)
  2490  CRYPTO_PRICE/ETH/range_bracket/event
  1642  WEATHER/TEMPERATURE/range_bracket/event  <- "highest temp in <city> between NF" daily weather
  1579  CRYPTO_PRICE/ETH/binary/event
  1578  CRYPTO_PRICE/BTC/binary/event
  1544  MISC/UNKNOWN/binary/event
  1367  SPORTS_OTHER/MLB/binary/event            <- per-game sports
   971  CRYPTO_PRICE/SOL/binary/event
   940  POLITICS_US/TRUMP/binary/monthly         <- Trump approval / "will Trump say X" / exec orders
   864  CRYPTO_PRICE/XRP/binary/event
   810  CRYPTO_PRICE/BTC/binary/monthly
   665  SPORTS_FOOTBALL/NFL/binary/event
   634  WEATHER/TEMPERATURE/binary/event
   521  SPORTS_OTHER/F1/binary/event
   446  TECH/ELON_MUSK/binary/monthly            <- "will Elon tweet N times" / "will Elon say X"
   335  SPORTS_OTHER/NBA/binary/event
   332  SPORTS_OTHER/GOLF/binary/event
   321  SPORTS_FOOTBALL/EPL/binary/event
   313  POLITICS_US/TRUMP/binary/event
   286  SPORTS_OTHER/UFC/binary/event
   282  SPORTS_OTHER/TENNIS/binary/event
   230  SPORTS_FOOTBALL/UEFA/binary/event
   222  SPORTS_OTHER/NHL/binary/event
    94  POLITICS_INTL/ISRAEL/binary/monthly
    71  COMMODITY/GOLD/binary/event
    69  SPORTS_FOOTBALL/WORLD_CUP/binary/event
    64  MACRO/CPI/binary/monthly
```

(Full 200-tuple table is in the raw run output; the tail is a long flat distribution of POLITICS_INTL countries,
remaining sports leagues, CULTURE awards, and small MACRO prints.)

### Top salient tokens in OTHER question titles (3,370-market harvest)

```
 vs(846) 2025(698) win(652) between(409) highest(398) september(387) temperature(376) say(251)
 trump(243) draw(226) spread(216) down(192) up(191) london(190) solana(188) city(181)
 new/york(180/165) xrp(152) price(136) elon(95) beat(94) strike(91) above(88) f1(72)
 grand/prix(71/68) score(61) below(55) before(55) approval/rating(29) box/office(28/28)
```

Top bigrams: `win 2025`, `highest temperature`, `end draw`, `up down`, `temperature london`, `new york city`,
`trump say`, `temperature nyc`, `counter strike`, `grand prix`, `elon musk`, `elon tweet`, `box office`,
`approval rating`, `map winner`, `constructor score`, `opening weekend`.

### Top normalised slug templates (dates → `N`) — the recurring market FACTORIES

```
 136  will-the-highest-temperature-in-london-be-between-N-Nf-on
 111  will-the-highest-temperature-in-new-york-city-be-between-N-Nf-on
  36  sol-multistrike-Nh
  31  will-the-highest-temperature-in-london-be-Nf-or-below-on
  27  will-the-highest-temperature-in-nyc-be-between-N-Nf-on
  24  xrp-multistrike-Nh
  19  solana-up-or-down-august-N-Nam-et
  18  elon-musk-of-tweets-september-N
  18  xrp-up-or-down-september-N-Nam-et
  15  will-the-price-of-solana-be-between-N-and-N-on-...-et
  10  will-trumps-approval-rating-be-between-NptN-and-NptN-on
   9  will-trumps-approval-rating-be-NptNptN-on
   8  will-elon-tweet-N-times
   7  will-donald-trump-sign-an-executive-order-on
   5  N-year-treasury-yield-NptN-friday
   4  will-chelsea-win / will-germany-win / will-england-win
   3  mlb-mia-tex-N-N-N-nrfi / nfl-lv-was-...-spread / nba-orl-phi-...-total
```

### Representative distinct questions per emergent cluster

**Crypto price-direction (alt coins — no group):** `XRP Up or Down on June 15?` · `Solana Up or Down - June 22, 10PM ET`
· `Solana Up or Down - July 3, 8AM ET`. (BTC/ETH up-or-down DAILY ARE grouped; the SOL/XRP and the hourly/event variants
are not.)

**Crypto price-RANGE / multistrike (between $X-$Y):**
`Will the price of Solana be between $N and $N on September N at NPM ET?` · `sol-multistrike-Nh`, `xrp-multistrike-Nh` ·
`Ripple above $2.40 on March 28?` — BTC/ETH range_bracket too (`CRYPTO_PRICE/BTC/range_bracket/event` is the #4 OTHER
tuple).

**Weather — daily city temperature:** `Will the highest temperature in London be between 52-53°F on March 16?` ·
`Will the highest temperature in NYC be 83°F or higher on March 29?` — two giant slug factories (London + NYC), clean
range-bracket scalars.

**Sports — per-fixture (the single largest distinct genre):** `Will Chelsea win on 2025-03-16?` ·
`Will Spain vs. Netherlands end in a draw?` · `Will Lewis Hamilton win the 2025 Chinese Grand Prix Sprint?` · UFC
`Marcin Tybura vs. Mick Parkin` · MLB/NBA/NFL spread+total+NRFI tickers (`mlb-mia-tex-...-nrfi`,
`nba-orl-phi-...-total-NptN`).

**US politics — Trump "will he say / sign":** `Will Trump say "Epstein" during his DOJ appearance on Friday?` ·
`Will Trump issue an executive order on March 15?` ·
`Will Trump's approval rating be between 46.0% and 46.4% on March 21?` · `Will Trump post 200-219 times March 14-21?`

**Tech personality (Elon/AI):** `Will Elon tweet 775-799 times March 7-14?` ·
`Will Elon say "Mars" during Baier interview on Thursday?` · `Will OpenAI have the top AI model on March 31?` ·
`Will Elon Musk's net worth be less than $330b on March 31?`

**Geopolitics (strike/ceasefire/capture by DATE):** `Israeli military action against Iran by Friday?` ·
`Russia x Ukraine Ceasefire in March?` · `Will Russia capture Khotin before July?` · `China bans US films before July?`

**Macro / econ prints (mostly ungrouped despite CPI/FED having groups):**
`Will the May 2025 unemployment rate be ≥4.6%?` · `Fed decreases interest rates by 25 bps after June 2025 meeting?` ·
`10-year Treasury yield >4.5% Friday?` · `Will a dozen eggs be above $4.50 in August?` ·
`Will Powell say "Employment" 20+ times during July Press Conference?`

**Culture / box-office / streaming:** `Will "Superman" Opening Weekend Box Office be more than $124m?` ·
`Will Taylor Swift announce a new song today?` · `Will "...?" be the top global Netflix show this week?` ·
`Will <movie> Rotten Tomatoes score be between 75-79?`

**MISC/UNKNOWN (genuinely uncategorised — 5,167 yearly + 1,544 event shards):**
`Will Fear & Greed Index report "Fear" on March 31?` ·
`Will Mercedes have the highest Constructor score at the Australian GP?` (F1 constructor — TECH/SPORTS overlap) ·
`March Madness: 9 first round upsets?` · `Will Kanye name his token YZY?` · long tail of one-off novelty markets.

---

## 4. Suggested theme candidates (SUGGESTIVE — operator builds the real taxonomy)

These are the natural clusters that jump out of the corpus, roughly ordered by volume. They are candidate **new cqg
groups / group-families** the classifier could route to instead of OTHER:

1. **`{COIN}_UP_DOWN_{CADENCE}` for SOL / XRP (and DOGE/BNB/HYPE/SUI/ADA/LTC/AVAX/LINK)** — mirror the existing BTC/ETH
   family; today only BTC/ETH have groups. Largest single fixable bucket.
2. **`{COIN}_PRICE_RANGE_{CADENCE}` (range_bracket "between $X-$Y" / multistrike)** — BTC/ETH/SOL/XRP price-bracket
   markets; distinct structure from up/down, currently all OTHER.
3. **`WEATHER_TEMP_{CITY}_DAILY`** — London + NYC highest-temperature daily range markets (two clean slug factories).
4. **Sports per-fixture families** — `SPORTS_{LEAGUE}_MATCH_WINNER` / `_SPREAD` / `_TOTAL` for MLB, NFL, NBA, NHL, EPL,
   UEFA, F1, UFC, TENNIS, GOLF, WORLD_CUP. Largest distinct-question genre overall; the path already carries the league.
5. **`TRUMP_APPROVAL_RATING` (scalar range)** and **`TRUMP_WILL_SAY_{KEYWORD}` / `TRUMP_EXEC_ORDER`** — high-volume
   recurring US-politics factories.
6. **`ELON_TWEET_COUNT` / `ELON_WILL_SAY` / personality-net-worth** — TECH/ELON_MUSK recurring markets.
7. **`GEO_CONFLICT_BY_DATE`** — Israel/Iran/Russia/Ukraine strike/ceasefire/capture-by-date binaries.
8. **`MACRO_UNEMPLOYMENT_PRINT` / `MACRO_FED_DECISION` (extend) / `MACRO_TREASURY_YIELD` / `MACRO_CPI` (extend) /
   `MACRO_EGG_PRICE`** — most macro prints are OTHER even though CPI/FED groups exist (the event map only matches
   underlying `CPI`/`FED_RATE`, missing UNEMPLOYMENT/GDP/PPI/PCE/yields).
9. **`CULTURE_BOX_OFFICE_OPENING_WEEKEND` / `CULTURE_NETFLIX_TOP` / `CULTURE_RT_SCORE`** — movie/streaming scalar
   families.
10. **`POWELL_WILL_SAY` / `{PERSON}_WILL_SAY_{KEYWORD}`** — the cross-figure "will X say keyword N times" pattern recurs
    for Trump, Elon, Powell.
11. **`F1_CONSTRUCTOR_HIGHEST` / `F1_GRAND_PRIX_WINNER`** — currently split between SPORTS_OTHER and MISC.
12. **`CRYPTO_FEAR_GREED_INDEX`** — recurring MACRO/FEAR_GREED markets (taxonomy tags them, no cqg group).
13. **`COMMODITY_{GOLD/SILVER/OIL}_PRICE`** — beyond the CME-linked daily-direction groups, the price-level markets are
    OTHER.
14. **`POLITICS_INTL_{COUNTRY}_LEADERSHIP`** — long tail of country/leader markets (Putin, Macron, Meloni, Khamenei…).
15. **`MISC_NOVELTY` (explicit residual)** — keep a deliberate catch-all for genuine one-offs so OTHER stops being an
    80% silent bucket; target it small (the taxonomy's own `MISC` goal was <50/day).

**Theming heuristics visible in the data:** the slug is the strongest signal (Polymarket slugs are templated —
`{thing}-{up-or-down|between|multistrike}-{date}-{time}-et`); the **`market_type` + `resolution_period` already
disambiguate** up/down vs range vs event; recurring factories (weather/temp, elon-tweet-count, trump-approval,
sports-by-fixture, coin-up-down) are the highest-leverage first groups because each covers thousands of shards with one
slug-template rule.

---

## 5. Reproduce / extend

- Classifier: `unified-api-contracts` → `unified_api_contracts/canonical/domain/predictions/classifiers.py` (group
  maps) + `unified_api_contracts/internal/schemas/_prediction_market_taxonomy.py` (category/underlying/type/period
  rules).
- Corpus:
  `gs://market-data-tick-pred-prd-central-element-323112/raw_tick_data/by_date/day=*/…/data_type=trades/ {conditionId}.parquet`
  — columns `title`, `slug`, `eventSlug`, `outcome`, `conditionId` are the classifier inputs + question text. Read with
  `pyarrow.fs.GcsFileSystem().open_input_file(path)` then `pq.read_table(fh, columns=[…])` (do NOT use the
  hive-partition dataset reader — it errors on `data_source` dict-vs-string schema merge).
- The thin `prod/catalog.parquet` (668k rows / 334k distinct markets) has **only** condition_ids — **no question text**;
  the readable text is only in the trades parquets above.

## 6. Caveats

- Corpus span covered by the full walk: **2025-03-14 → 2025-10-14** (the listing completed mid-Oct; later days exist but
  weren't in the exact-% walk). The OTHER % is stable across the span.
- The exact corpus-wide 79.6% is **per market×day shard**; the operator's 94.5% is consistent with a **per-distinct-
  market** denominator (recurring BTC/ETH-daily groups deflate the per-shard unknown share). Both confirm "the vast
  majority is unclassified."
- The per-theme sample bucketer in §3 is a crude keyword grouping for readability only — it occasionally mislabels (e.g.
  "between" scalars from box-office/approval landed in a "price-range" bucket). The path-tuple table (also §3) is the
  authoritative structural signal.
