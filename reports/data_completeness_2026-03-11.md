# Data Completeness Report — 2026-03-11

**Overall:** 26/33 sources passing (94.5% average coverage) **Threshold:** 95.0%

| Source                            | Asset Class | Criticality   | Coverage% | Pass | Expected | Actual |
| --------------------------------- | ----------- | ------------- | --------- | ---- | -------- | ------ |
| databento_eod                     | tradfi      | important     | 87.5%     | ✗    | 8        | 7      |
| ecb                               | tradfi      | informational | 87.5%     | ✗    | 8        | 7      |
| fred                              | tradfi      | informational | 87.5%     | ✗    | 8        | 7      |
| ofr                               | tradfi      | informational | 87.5%     | ✗    | 8        | 7      |
| openbb                            | tradfi      | informational | 87.5%     | ✗    | 8        | 7      |
| yahoo_finance                     | tradfi      | important     | 87.5%     | ✗    | 8        | 7      |
| deribit                           | crypto_cefi | critical      | 80.0%     | ✗    | 86400    | 69120  |
| aave_v3                           | crypto_defi | critical      | 97.0%     | ✓    | 7200     | 6984   |
| balancer                          | crypto_defi | critical      | 97.0%     | ✓    | 7200     | 6984   |
| binance                           | crypto_cefi | critical      | 97.0%     | ✓    | 86400    | 83808  |
| bybit                             | crypto_cefi | critical      | 97.0%     | ✓    | 86400    | 83808  |
| coinbase                          | crypto_cefi | critical      | 97.0%     | ✓    | 86400    | 83808  |
| curve                             | crypto_defi | critical      | 97.0%     | ✓    | 7200     | 6984   |
| hyperliquid                       | crypto_cefi | critical      | 97.0%     | ✓    | 86400    | 83808  |
| okx                               | crypto_cefi | critical      | 97.0%     | ✓    | 86400    | 83808  |
| uniswap_v3                        | crypto_defi | critical      | 97.0%     | ✓    | 7200     | 6984   |
| betfair                           | sports      | important     | 97.0%     | ✓    | 11520    | 11174  |
| odds_api                          | sports      | important     | 97.0%     | ✓    | 1920     | 1862   |
| pinnacle                          | sports      | important     | 97.0%     | ✓    | 1920     | 1862   |
| features-cross-instrument-service | feature     | important     | 96.9%     | ✓    | 1440     | 1396   |
| features-delta-one-service        | feature     | critical      | 96.9%     | ✓    | 1440     | 1396   |
| features-multi-timeframe-service  | feature     | critical      | 96.9%     | ✓    | 1440     | 1396   |
| features-sports-service           | feature     | important     | 96.9%     | ✓    | 1440     | 1396   |
| features-volatility-service       | feature     | critical      | 96.9%     | ✓    | 1440     | 1396   |
| ml-inference-api                  | ml          | critical      | 96.9%     | ✓    | 1440     | 1396   |
| databento_intraday                | tradfi      | important     | 96.9%     | ✓    | 480      | 465    |
| features-onchain-service          | feature     | important     | 96.9%     | ✓    | 288      | 279    |
| arkham                            | onchain     | informational | 95.8%     | ✓    | 24       | 23     |
| coinglass                         | onchain     | important     | 95.8%     | ✓    | 24       | 23     |
| features-calendar-service         | feature     | informational | 95.8%     | ✓    | 24       | 23     |
| features-commodity-service        | feature     | informational | 95.8%     | ✓    | 24       | 23     |
| glassnode                         | onchain     | important     | 95.8%     | ✓    | 24       | 23     |
| ml-training-api                   | ml          | informational | 95.8%     | ✓    | 24       | 23     |
