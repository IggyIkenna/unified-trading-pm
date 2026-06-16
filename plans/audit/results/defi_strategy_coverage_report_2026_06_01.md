---
type: analysis
title: DeFi strategy data-coverage — honest breakdown per data_type × venue/chain
epic: defi_master
auditor: claude + operator
date: "2026-06-01"
status: complete
---

# DeFi strategy data-coverage — honest breakdown per data_type × venue/chain

_prd indexes; total strategy-relevant rows: 2,870,693_

## A. Per data_type × venue (in totality)

| ag     | data_type         | venue                |    rows | captured | empty_conf | attempted_failed | exp_unatt | other | v9% | date_min   | date_max   |
| ------ | ----------------- | -------------------- | ------: | -------: | ---------: | ---------------: | --------: | ----: | --: | ---------- | ---------- |
| cefi   | book_snapshot_5   |                      |     250 |      248 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | book_snapshot_5   | AAVEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | ADAF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | ASTER                |   5,706 |        0 |          0 |            5,706 |         0 |     0 |  0% | 2024-10-01 | 2026-05-03 |
| cefi   | book_snapshot_5   | ATOF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | AVAXF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | BINANCE-FUTURES      |  55,818 |   32,269 |          0 |           23,549 |         0 |     0 |  0% | 2019-12-30 | 2026-04-28 |
| cefi   | book_snapshot_5   | BINANCE-SPOT         | 102,063 |   51,224 |          0 |           50,839 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | book_snapshot_5   | BITFINEX-FUTURES     |  44,473 |   16,149 |          0 |           28,324 |         0 |     0 |  0% | 2020-01-01 | 2026-05-06 |
| cefi   | book_snapshot_5   | BITFINEX-SPOT        |  52,585 |   31,265 |          0 |           21,320 |         0 |     0 |  0% | 2020-01-01 | 2026-05-05 |
| cefi   | book_snapshot_5   | BITGET-FUTURES       |  31,140 |   18,060 |          0 |           13,080 |         0 |     0 |  0% | 2024-11-08 | 2026-05-06 |
| cefi   | book_snapshot_5   | BITGET-SPOT          |  19,183 |   17,687 |          0 |            1,496 |         0 |     0 |  0% | 2024-11-08 | 2026-05-05 |
| cefi   | book_snapshot_5   | BNBF0                |       2 |        2 |          0 |                0 |         0 |     0 |  0% | 2024-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | BTCF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | BYBIT                |  55,455 |   32,162 |          0 |           23,293 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | book_snapshot_5   | COINBASE-SPOT        |  53,965 |    2,272 |          0 |           51,693 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | book_snapshot_5   | COMPF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | DERIBIT              |  51,836 |   23,279 |          0 |           28,557 |         0 |     0 |  0% | 2019-03-30 | 2026-05-01 |
| cefi   | book_snapshot_5   | DOGEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | DOTF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | ETCF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2023-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | ETHF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | FILF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | HYPERLIQUID          |  11,715 |      895 |          0 |           10,820 |         0 |     0 |  0% | 2023-11-01 | 2026-05-04 |
| cefi   | book_snapshot_5   | KRAKEN-FUTURES       |  25,317 |    7,471 |          0 |           17,846 |         0 |     0 |  0% | 2020-01-01 | 2026-05-06 |
| cefi   | book_snapshot_5   | KRAKEN-SPOT          |  89,494 |   32,635 |          0 |           56,859 |         0 |     0 |  0% | 2020-01-01 | 2026-05-05 |
| cefi   | book_snapshot_5   | LIGHTER-ZKSYNC       |     444 |        0 |          0 |              444 |         0 |     0 |  0% | 2024-08-04 | 2025-05-30 |
| cefi   | book_snapshot_5   | LINKF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | LTCF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | NEOF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | OKX-FUTURES          |  46,223 |        0 |          0 |           46,223 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | book_snapshot_5   | OKX-SPOT             |  46,297 |      167 |          0 |           46,130 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | book_snapshot_5   | OKX-SWAP             |  30,895 |      126 |          0 |           30,769 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | book_snapshot_5   | PACIFICA-SOLANA      |   3,100 |        0 |          0 |            3,100 |         0 |     0 |  0% | 2025-07-01 | 2026-05-06 |
| cefi   | book_snapshot_5   | SHIBF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | SOLF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | TRXF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | UNIF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | UNKNOWN              |      19 |       17 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | book_snapshot_5   | UPBIT                |  56,105 |   20,165 |          0 |           35,940 |         0 |     0 |  0% | 2021-03-03 | 2026-04-28 |
| cefi   | book_snapshot_5   | XAUTF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | XLMF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | XRPF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | XTZF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | book_snapshot_5   | ZECF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker |                      |     250 |      248 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | derivative_ticker | AAVEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | ADAF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | ASTER                |   5,706 |        0 |          0 |            5,706 |         0 |     0 |  0% | 2024-10-01 | 2026-05-03 |
| cefi   | derivative_ticker | ATOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | AVAXF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | BINANCE-FUTURES      |  56,255 |   38,068 |          0 |           18,187 |         0 |     0 |  0% | 2019-12-30 | 2026-04-28 |
| cefi   | derivative_ticker | BITFINEX-FUTURES     |  35,926 |   17,155 |          0 |           18,771 |         0 |     0 |  0% | 2020-01-01 | 2026-05-06 |
| cefi   | derivative_ticker | BITFINEX-SPOT        |   2,224 |        0 |          0 |            2,224 |         0 |     0 |  0% | 2020-01-01 | 2026-01-11 |
| cefi   | derivative_ticker | BITGET-FUTURES       |  26,582 |   13,502 |          0 |           13,080 |         0 |     0 |  0% | 2024-11-08 | 2026-05-06 |
| cefi   | derivative_ticker | BITGET-SPOT          |   4,851 |        0 |          0 |            4,851 |         0 |     0 |  0% | 2024-11-08 | 2026-04-30 |
| cefi   | derivative_ticker | BNBF0                |       2 |        2 |          0 |                0 |         0 |     0 |  0% | 2024-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | BTCF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | BYBIT                |  53,862 |   35,259 |          0 |           18,603 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | derivative_ticker | COMPF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | DERIBIT              |  37,143 |    8,696 |          0 |           28,447 |         0 |     0 |  0% | 2019-03-30 | 2026-05-01 |
| cefi   | derivative_ticker | DOGEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | DOTF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | ETCF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2023-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | ETHF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | EXTENDED-STARKNET    |      10 |        0 |          0 |               10 |         0 |     0 |  0% | 2026-04-30 | 2026-04-30 |
| cefi   | derivative_ticker | FILF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | HYPERLIQUID          |  20,290 |   12,188 |          0 |            8,102 |         0 |     0 |  0% | 2023-11-01 | 2026-05-04 |
| cefi   | derivative_ticker | KRAKEN-FUTURES       |  22,739 |    9,260 |          0 |           13,479 |         0 |     0 |  0% | 2020-01-01 | 2026-05-06 |
| cefi   | derivative_ticker | KRAKEN-SPOT          |  18,496 |        0 |          0 |           18,496 |         0 |     0 |  0% | 2020-01-01 | 2026-04-30 |
| cefi   | derivative_ticker | LIGHTER-ZKSYNC       |      10 |        0 |          0 |               10 |         0 |     0 |  0% | 2026-04-30 | 2026-04-30 |
| cefi   | derivative_ticker | LINKF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | LTCF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | NEOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | OKX-FUTURES          |  22,012 |        0 |          0 |           22,012 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | derivative_ticker | OKX-SWAP             |  47,637 |   16,877 |          0 |           30,760 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | derivative_ticker | PACIFICA-SOLANA      |      10 |        0 |          0 |               10 |         0 |     0 |  0% | 2026-04-30 | 2026-04-30 |
| cefi   | derivative_ticker | SHIBF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | SOLF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | TRXF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | UNIF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | UNKNOWN              |      19 |       17 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | derivative_ticker | XAUTF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | XLMF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | XRPF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | XTZF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | derivative_ticker | ZECF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     |                      |     222 |      220 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | futures_chain     | AAVEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | ADAF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | ATOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | AVAXF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | BINANCE-FUTURES      |  20,251 |        0 |          0 |           20,251 |         0 |     0 |  0% | 2019-12-30 | 2026-04-28 |
| cefi   | futures_chain     | BITFINEX-FUTURES     |  12,184 |        0 |          0 |           12,184 |         0 |     0 |  0% | 2020-01-01 | 2026-04-30 |
| cefi   | futures_chain     | BITFINEX-SPOT        |   2,224 |        0 |          0 |            2,224 |         0 |     0 |  0% | 2020-01-01 | 2026-01-11 |
| cefi   | futures_chain     | BITGET-FUTURES       |   4,860 |        0 |          0 |            4,860 |         0 |     0 |  0% | 2024-11-08 | 2026-05-01 |
| cefi   | futures_chain     | BITGET-SPOT          |   4,851 |        0 |          0 |            4,851 |         0 |     0 |  0% | 2024-11-08 | 2026-04-30 |
| cefi   | futures_chain     | BNBF0                |       2 |        2 |          0 |                0 |         0 |     0 |  0% | 2024-01-01 | 2026-01-01 |
| cefi   | futures_chain     | BTCF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | futures_chain     | BYBIT                |  17,180 |      444 |          0 |           16,736 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | futures_chain     | COMPF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | DERIBIT              |  10,416 |       58 |          0 |           10,358 |         0 |     0 |  0% | 2019-03-30 | 2026-05-01 |
| cefi   | futures_chain     | DOGEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | DOTF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | futures_chain     | ETCF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2023-01-01 | 2026-01-01 |
| cefi   | futures_chain     | ETHF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | futures_chain     | EXTENDED-STARKNET    |       2 |        0 |          0 |                2 |         0 |     0 |  0% | 2026-04-30 | 2026-04-30 |
| cefi   | futures_chain     | FILF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | KRAKEN-FUTURES       |  10,608 |        0 |          0 |           10,608 |         0 |     0 |  0% | 2020-01-01 | 2026-04-30 |
| cefi   | futures_chain     | KRAKEN-SPOT          |  18,496 |        0 |          0 |           18,496 |         0 |     0 |  0% | 2020-01-01 | 2026-04-30 |
| cefi   | futures_chain     | LIGHTER-ZKSYNC       |   1,120 |        0 |         60 |            1,060 |         0 |     0 |  0% | 2024-08-01 | 2026-05-06 |
| cefi   | futures_chain     | LINKF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | futures_chain     | LTCF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | futures_chain     | NEOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | PACIFICA-SOLANA      |     620 |        0 |          0 |              620 |         0 |     0 |  0% | 2025-07-01 | 2026-05-06 |
| cefi   | futures_chain     | SHIBF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | SOLF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | TRXF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | UNIF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | futures_chain     | UNKNOWN              |      24 |       19 |          0 |                5 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | futures_chain     | XAUTF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | futures_chain     | XLMF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | XRPF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | XTZF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | futures_chain     | ZECF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     |                      |     243 |      241 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | options_chain     | AAVEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | ADAF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | ATOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | AVAXF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | BITFINEX-FUTURES     |  12,184 |        0 |          0 |           12,184 |         0 |     0 |  0% | 2020-01-01 | 2026-04-30 |
| cefi   | options_chain     | BITFINEX-SPOT        |   2,224 |        0 |          0 |            2,224 |         0 |     0 |  0% | 2020-01-01 | 2026-01-11 |
| cefi   | options_chain     | BITGET-FUTURES       |   4,860 |        0 |          0 |            4,860 |         0 |     0 |  0% | 2024-11-08 | 2026-05-01 |
| cefi   | options_chain     | BITGET-SPOT          |   4,851 |        0 |          0 |            4,851 |         0 |     0 |  0% | 2024-11-08 | 2026-04-30 |
| cefi   | options_chain     | BNBF0                |       2 |        2 |          0 |                0 |         0 |     0 |  0% | 2024-01-01 | 2026-01-01 |
| cefi   | options_chain     | BTCF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | options_chain     | COMPF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | DERIBIT              |  10,437 |       79 |          0 |           10,358 |         0 |     0 |  0% | 2019-03-30 | 2026-05-01 |
| cefi   | options_chain     | DOGEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | DOTF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | options_chain     | ETCF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2023-01-01 | 2026-01-01 |
| cefi   | options_chain     | ETHF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | options_chain     | EXTENDED-STARKNET    |       2 |        0 |          0 |                2 |         0 |     0 |  0% | 2026-04-30 | 2026-04-30 |
| cefi   | options_chain     | FILF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | KRAKEN-FUTURES       |  10,608 |        0 |          0 |           10,608 |         0 |     0 |  0% | 2020-01-01 | 2026-04-30 |
| cefi   | options_chain     | KRAKEN-SPOT          |  18,496 |        0 |          0 |           18,496 |         0 |     0 |  0% | 2020-01-01 | 2026-04-30 |
| cefi   | options_chain     | LIGHTER-ZKSYNC       |   1,120 |        0 |         60 |            1,060 |         0 |     0 |  0% | 2024-08-01 | 2026-05-06 |
| cefi   | options_chain     | LINKF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | options_chain     | LTCF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | options_chain     | NEOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | PACIFICA-SOLANA      |     620 |        0 |          0 |              620 |         0 |     0 |  0% | 2025-07-01 | 2026-05-06 |
| cefi   | options_chain     | SHIBF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | SOLF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | TRXF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | UNIF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | options_chain     | UNKNOWN              |      21 |       14 |          0 |                7 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | options_chain     | XAUTF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | options_chain     | XLMF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | XRPF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | XTZF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | options_chain     | ZECF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            |                      |     250 |      248 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | trades            | AAVEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | ADAF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | ASTER                |   5,706 |        0 |          0 |            5,706 |         0 |     0 |  0% | 2024-10-01 | 2026-05-03 |
| cefi   | trades            | ATOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | AVAXF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | BINANCE-FUTURES      |  57,918 |   34,443 |          0 |           23,475 |         0 |     0 |  0% | 2019-12-30 | 2026-04-28 |
| cefi   | trades            | BINANCE-SPOT         | 103,782 |   52,992 |          0 |           50,790 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | trades            | BITFINEX-FUTURES     |  44,657 |   16,333 |          0 |           28,324 |         0 |     0 |  0% | 2020-01-01 | 2026-05-06 |
| cefi   | trades            | BITFINEX-SPOT        |  56,559 |   35,246 |          0 |           21,313 |         0 |     0 |  0% | 2020-01-01 | 2026-05-05 |
| cefi   | trades            | BITGET-FUTURES       |  31,395 |   18,315 |          0 |           13,080 |         0 |     0 |  0% | 2024-11-08 | 2026-05-07 |
| cefi   | trades            | BITGET-SPOT          |  19,223 |   17,731 |          0 |            1,492 |         0 |     0 |  0% | 2024-11-08 | 2026-05-06 |
| cefi   | trades            | BNBF0                |       2 |        2 |          0 |                0 |         0 |     0 |  0% | 2024-01-01 | 2026-01-01 |
| cefi   | trades            | BTCF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | trades            | BYBIT                |  55,481 |   32,708 |          0 |           22,773 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | trades            | COINBASE-SPOT        | 132,100 |   93,361 |          0 |           38,739 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | trades            | COMPF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | DERIBIT              |  68,424 |   39,509 |          0 |           28,915 |         0 |     0 |  0% | 2019-03-30 | 2026-05-01 |
| cefi   | trades            | DOGEF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | DOTF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | trades            | ETCF0                |       3 |        3 |          0 |                0 |         0 |     0 |  0% | 2023-01-01 | 2026-01-01 |
| cefi   | trades            | ETHF0                |       6 |        6 |          0 |                0 |         0 |     0 |  0% | 2020-01-01 | 2026-01-01 |
| cefi   | trades            | FILF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | HYPERLIQUID          |  11,760 |      940 |          0 |           10,820 |         0 |     0 |  0% | 2023-11-01 | 2026-05-04 |
| cefi   | trades            | KRAKEN-FUTURES       |  25,333 |    7,488 |          0 |           17,845 |         0 |     0 |  0% | 2020-01-01 | 2026-05-06 |
| cefi   | trades            | KRAKEN-SPOT          |  98,860 |   42,001 |          0 |           56,859 |         0 |     0 |  0% | 2020-01-01 | 2026-05-06 |
| cefi   | trades            | LINKF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | trades            | LTCF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | trades            | NEOF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | OKX-FUTURES          | 154,095 |  107,872 |          0 |           46,223 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | trades            | OKX-SPOT             | 173,099 |  157,871 |          0 |           15,228 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | trades            | OKX-SWAP             |  98,233 |   67,473 |          0 |           30,760 |         0 |     0 |  0% | 2020-01-01 | 2026-04-28 |
| cefi   | trades            | SHIBF0               |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | SOLF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | TRXF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | UNIF0                |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | trades            | UNKNOWN              |      33 |       31 |          0 |                2 |         0 |     0 |  0% | 2020-01-01 | 2026-04-14 |
| cefi   | trades            | UPBIT                |  56,479 |   20,506 |          0 |           35,973 |         0 |     0 |  0% | 2021-03-03 | 2026-04-28 |
| cefi   | trades            | XAUTF0               |       5 |        5 |          0 |                0 |         0 |     0 |  0% | 2021-01-01 | 2026-01-01 |
| cefi   | trades            | XLMF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | XRPF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | XTZF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| cefi   | trades            | ZECF0                |       4 |        4 |          0 |                0 |         0 |     0 |  0% | 2022-01-01 | 2026-01-01 |
| defi   | lending_indices   | AAVEV3-ARBITRUM      |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | lending_indices   | AAVEV3-AVALANCHE     |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | lending_indices   | AAVEV3-BASE          |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | lending_indices   | AAVEV3-BSC           |   1,921 |        0 |      1,921 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-05 |
| defi   | lending_indices   | AAVEV3-ETHEREUM      |   1,533 |        0 |      1,533 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-13 |
| defi   | lending_indices   | AAVEV3-LINEA         |   2,460 |        0 |      2,460 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-09-25 |
| defi   | lending_indices   | AAVEV3-OPTIMISM      |   1,676 |        0 |      1,676 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-03 |
| defi   | lending_indices   | AAVEV3-POLYGON       |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | lending_indices   | AAVEV3-SCROLL        |   2,310 |        0 |      2,310 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-28 |
| defi   | lending_indices   | AAVEV3-ZKSYNC        |   2,290 |        0 |      2,290 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-08 |
| defi   | lending_indices   | BALANCER-ETHEREUM    |     820 |        0 |        820 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-03-30 |
| defi   | lending_indices   | COMPOUNDV3-ARBITRUM  |   1,928 |        0 |      1,928 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-12 |
| defi   | lending_indices   | COMPOUNDV3-BASE      |   2,063 |        0 |      2,063 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-25 |
| defi   | lending_indices   | COMPOUNDV3-ETHEREUM  |   1,697 |        0 |      1,697 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-24 |
| defi   | lending_indices   | COMPOUNDV3-OPTIMISM  |   2,236 |        0 |      2,236 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-14 |
| defi   | lending_indices   | COMPOUNDV3-POLYGON   |   1,870 |        0 |      1,870 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-02-13 |
| defi   | lending_indices   | COMPOUNDV3-SCROLL    |   2,303 |        0 |      2,303 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-21 |
| defi   | lending_indices   | CURVE-ETHEREUM       |     748 |        0 |        748 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-01-18 |
| defi   | lending_indices   | DRIFT-SOLANA         |   1,417 |        0 |      1,417 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-17 |
| defi   | lending_indices   | ETHENA-ETHEREUM      |   2,240 |        0 |      2,240 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-18 |
| defi   | lending_indices   | ETHERFI-ETHEREUM     |   1,940 |        0 |      1,940 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-24 |
| defi   | lending_indices   | FRAX-ETHEREUM        |   1,085 |        0 |      1,085 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-20 |
| defi   | lending_indices   | GMX-ARBITRUM         |   1,339 |        0 |      1,339 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-31 |
| defi   | lending_indices   | GMX-AVALANCHE        |   1,465 |        0 |      1,465 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-01-04 |
| defi   | lending_indices   | JITO-SOLANA          |   1,687 |        0 |      1,687 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-14 |
| defi   | lending_indices   | KAMINO               |      32 |        0 |          0 |               32 |         0 |     0 |  0% | 2022-11-01 | 2025-01-17 |
| defi   | lending_indices   | KAMINO-SOLANA        |   1,695 |        0 |      1,695 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-22 |
| defi   | lending_indices   | LIDO-ETHEREUM        |   1,083 |        0 |      1,083 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-18 |
| defi   | lending_indices   | MARGINFI             |      30 |        0 |          0 |               30 |         0 |     0 |  0% | 2022-11-01 | 2025-01-16 |
| defi   | lending_indices   | MARINADE-SOLANA      |   1,309 |        0 |      1,309 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-01 |
| defi   | lending_indices   | ORCA-SOLANA          |   1,135 |        0 |      1,135 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-08 |
| defi   | lending_indices   | RAYDIUM-SOLANA       |   1,147 |        0 |      1,147 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-20 |
| defi   | lending_indices   | ROCKETPOOL-ETHEREUM  |   1,407 |        0 |      1,407 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-07 |
| defi   | lending_indices   | SOLEND               |      29 |        0 |          0 |               29 |         0 |     0 |  0% | 2022-11-01 | 2025-01-16 |
| defi   | lending_indices   | SUSHISWAPV3-ETHEREUM |   1,919 |        0 |      1,919 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-03 |
| defi   | lending_indices   | UNISWAPV2-ETHEREUM   |     854 |        0 |        854 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-05-03 |
| defi   | lending_indices   | UNISWAPV3-ARBITRUM   |   1,338 |        0 |      1,338 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-30 |
| defi   | lending_indices   | UNISWAPV3-BASE       |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | lending_indices   | UNISWAPV3-ETHEREUM   |   1,219 |        0 |      1,219 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-05-03 |
| defi   | lending_indices   | UNISWAPV3-OPTIMISM   |   1,445 |        0 |      1,445 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-15 |
| defi   | lending_indices   | UNISWAPV3-POLYGON    |   1,450 |        0 |      1,450 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-20 |
| defi   | lending_indices   | UNISWAPV4-ETHEREUM   |   2,587 |        0 |      2,587 |                0 |         0 |     0 |  0% | 2018-01-01 | 2025-01-30 |
| defi   | oracle_prices     | AAVEV3               |   3,160 |    3,160 |          0 |                0 |         0 |     0 |  0% | 2024-05-02 | 2026-01-23 |
| defi   | oracle_prices     | AAVEV3-ARBITRUM      |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | oracle_prices     | AAVEV3-AVALANCHE     |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | oracle_prices     | AAVEV3-BASE          |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | oracle_prices     | AAVEV3-BSC           |   1,921 |        0 |      1,921 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-05 |
| defi   | oracle_prices     | AAVEV3-ETHEREUM      |   1,533 |        0 |      1,533 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-13 |
| defi   | oracle_prices     | AAVEV3-LINEA         |   2,460 |        0 |      2,460 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-09-25 |
| defi   | oracle_prices     | AAVEV3-OPTIMISM      |   1,676 |        0 |      1,676 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-03 |
| defi   | oracle_prices     | AAVEV3-POLYGON       |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | oracle_prices     | AAVEV3-SCROLL        |   2,310 |        0 |      2,310 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-28 |
| defi   | oracle_prices     | AAVEV3-ZKSYNC        |   2,290 |        0 |      2,290 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-08 |
| defi   | oracle_prices     | BALANCER-ETHEREUM    |     820 |        0 |        820 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-03-30 |
| defi   | oracle_prices     | COMPOUNDV3-ARBITRUM  |   1,928 |        0 |      1,928 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-12 |
| defi   | oracle_prices     | COMPOUNDV3-BASE      |   2,063 |        0 |      2,063 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-25 |
| defi   | oracle_prices     | COMPOUNDV3-ETHEREUM  |   1,697 |        0 |      1,697 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-24 |
| defi   | oracle_prices     | COMPOUNDV3-OPTIMISM  |   2,236 |        0 |      2,236 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-14 |
| defi   | oracle_prices     | COMPOUNDV3-POLYGON   |   1,870 |        0 |      1,870 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-02-13 |
| defi   | oracle_prices     | COMPOUNDV3-SCROLL    |   2,303 |        0 |      2,303 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-21 |
| defi   | oracle_prices     | CURVE-ETHEREUM       |     748 |        0 |        748 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-01-18 |
| defi   | oracle_prices     | DRIFT-SOLANA         |   1,417 |        0 |      1,417 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-17 |
| defi   | oracle_prices     | ETHENA               |     631 |      631 |          0 |                0 |         0 |     0 |  0% | 2024-05-03 | 2026-01-23 |
| defi   | oracle_prices     | ETHENA-ETHEREUM      |   2,240 |        0 |      2,240 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-18 |
| defi   | oracle_prices     | ETHERFI              |     631 |      631 |          0 |                0 |         0 |     0 |  0% | 2024-05-03 | 2026-01-23 |
| defi   | oracle_prices     | ETHERFI-ETHEREUM     |   1,940 |        0 |      1,940 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-24 |
| defi   | oracle_prices     | FRAX-ETHEREUM        |   1,085 |        0 |      1,085 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-20 |
| defi   | oracle_prices     | GMX-ARBITRUM         |   1,339 |        0 |      1,339 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-31 |
| defi   | oracle_prices     | GMX-AVALANCHE        |   1,465 |        0 |      1,465 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-01-04 |
| defi   | oracle_prices     | JITO-SOLANA          |   1,687 |        0 |      1,687 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-14 |
| defi   | oracle_prices     | KAMINO-SOLANA        |   1,695 |        0 |      1,695 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-22 |
| defi   | oracle_prices     | LIDO                 |     631 |      631 |          0 |                0 |         0 |     0 |  0% | 2024-05-03 | 2026-01-23 |
| defi   | oracle_prices     | LIDO-ETHEREUM        |   1,083 |        0 |      1,083 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-18 |
| defi   | oracle_prices     | MARINADE-SOLANA      |   1,309 |        0 |      1,309 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-01 |
| defi   | oracle_prices     | ORCA-SOLANA          |   1,135 |        0 |      1,135 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-08 |
| defi   | oracle_prices     | RAYDIUM-SOLANA       |   1,147 |        0 |      1,147 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-20 |
| defi   | oracle_prices     | ROCKETPOOL-ETHEREUM  |   1,407 |        0 |      1,407 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-07 |
| defi   | oracle_prices     | SUSHISWAPV3-ETHEREUM |   1,919 |        0 |      1,919 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-03 |
| defi   | oracle_prices     | UNISWAPV2-ETHEREUM   |     854 |        0 |        854 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-05-03 |
| defi   | oracle_prices     | UNISWAPV3-ARBITRUM   |   1,338 |        0 |      1,338 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-30 |
| defi   | oracle_prices     | UNISWAPV3-BASE       |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | oracle_prices     | UNISWAPV3-ETHEREUM   |   1,219 |        0 |      1,219 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-05-03 |
| defi   | oracle_prices     | UNISWAPV3-OPTIMISM   |   1,445 |        0 |      1,445 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-15 |
| defi   | oracle_prices     | UNISWAPV3-POLYGON    |   1,450 |        0 |      1,450 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-20 |
| defi   | oracle_prices     | UNISWAPV4-ETHEREUM   |   2,587 |        0 |      2,587 |                0 |         0 |     0 |  0% | 2018-01-01 | 2025-01-30 |
| defi   | perp_funding      | AAVEV3-ARBITRUM      |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | perp_funding      | AAVEV3-AVALANCHE     |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | perp_funding      | AAVEV3-BASE          |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | perp_funding      | AAVEV3-BSC           |   1,921 |        0 |      1,921 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-05 |
| defi   | perp_funding      | AAVEV3-ETHEREUM      |   1,533 |        0 |      1,533 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-13 |
| defi   | perp_funding      | AAVEV3-LINEA         |   2,460 |        0 |      2,460 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-09-25 |
| defi   | perp_funding      | AAVEV3-OPTIMISM      |   1,676 |        0 |      1,676 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-03 |
| defi   | perp_funding      | AAVEV3-POLYGON       |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | perp_funding      | AAVEV3-SCROLL        |   2,310 |        0 |      2,310 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-28 |
| defi   | perp_funding      | AAVEV3-ZKSYNC        |   2,290 |        0 |      2,290 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-08 |
| defi   | perp_funding      | BALANCER-ETHEREUM    |     820 |        0 |        820 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-03-30 |
| defi   | perp_funding      | COMPOUNDV3-ARBITRUM  |   1,928 |        0 |      1,928 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-12 |
| defi   | perp_funding      | COMPOUNDV3-BASE      |   2,063 |        0 |      2,063 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-25 |
| defi   | perp_funding      | COMPOUNDV3-ETHEREUM  |   1,697 |        0 |      1,697 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-24 |
| defi   | perp_funding      | COMPOUNDV3-OPTIMISM  |   2,236 |        0 |      2,236 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-14 |
| defi   | perp_funding      | COMPOUNDV3-POLYGON   |   1,870 |        0 |      1,870 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-02-13 |
| defi   | perp_funding      | COMPOUNDV3-SCROLL    |   2,303 |        0 |      2,303 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-21 |
| defi   | perp_funding      | CURVE-ETHEREUM       |     748 |        0 |        748 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-01-18 |
| defi   | perp_funding      | DRIFT                |     435 |        0 |         11 |              424 |         0 |     0 | 94% | 2022-11-01 | 2026-05-16 |
| defi   | perp_funding      | DRIFT-SOLANA         |   1,417 |        0 |      1,417 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-17 |
| defi   | perp_funding      | ETHENA-ETHEREUM      |   2,240 |        0 |      2,240 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-18 |
| defi   | perp_funding      | ETHERFI-ETHEREUM     |   1,940 |        0 |      1,940 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-24 |
| defi   | perp_funding      | FRAX-ETHEREUM        |   1,085 |        0 |      1,085 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-20 |
| defi   | perp_funding      | GMX-ARBITRUM         |   1,339 |        0 |      1,339 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-31 |
| defi   | perp_funding      | GMX-AVALANCHE        |   1,465 |        0 |      1,465 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-01-04 |
| defi   | perp_funding      | JITO-SOLANA          |   1,687 |        0 |      1,687 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-14 |
| defi   | perp_funding      | KAMINO-SOLANA        |   1,695 |        0 |      1,695 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-22 |
| defi   | perp_funding      | LIDO-ETHEREUM        |   1,083 |        0 |      1,083 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-18 |
| defi   | perp_funding      | MARINADE-SOLANA      |   1,309 |        0 |      1,309 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-01 |
| defi   | perp_funding      | ORCA-SOLANA          |   1,135 |        0 |      1,135 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-08 |
| defi   | perp_funding      | RAYDIUM-SOLANA       |   1,147 |        0 |      1,147 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-20 |
| defi   | perp_funding      | ROCKETPOOL-ETHEREUM  |   1,407 |        0 |      1,407 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-07 |
| defi   | perp_funding      | SUSHISWAPV3-ETHEREUM |   1,919 |        0 |      1,919 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-03 |
| defi   | perp_funding      | UNISWAPV2-ETHEREUM   |     854 |        0 |        854 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-05-03 |
| defi   | perp_funding      | UNISWAPV3-ARBITRUM   |   1,338 |        0 |      1,338 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-30 |
| defi   | perp_funding      | UNISWAPV3-BASE       |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | perp_funding      | UNISWAPV3-ETHEREUM   |   1,219 |        0 |      1,219 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-05-03 |
| defi   | perp_funding      | UNISWAPV3-OPTIMISM   |   1,445 |        0 |      1,445 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-15 |
| defi   | perp_funding      | UNISWAPV3-POLYGON    |   1,450 |        0 |      1,450 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-20 |
| defi   | perp_funding      | UNISWAPV4-ETHEREUM   |   2,587 |        0 |      2,587 |                0 |         0 |     0 |  0% | 2018-01-01 | 2025-01-30 |
| defi   | staking_yields    | AAVEV3-ARBITRUM      |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | staking_yields    | AAVEV3-AVALANCHE     |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | staking_yields    | AAVEV3-BASE          |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | staking_yields    | AAVEV3-BSC           |   1,921 |        0 |      1,921 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-05 |
| defi   | staking_yields    | AAVEV3-ETHEREUM      |   1,533 |        0 |      1,533 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-13 |
| defi   | staking_yields    | AAVEV3-LINEA         |   2,460 |        0 |      2,460 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-09-25 |
| defi   | staking_yields    | AAVEV3-OPTIMISM      |   1,676 |        0 |      1,676 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-03 |
| defi   | staking_yields    | AAVEV3-POLYGON       |   1,535 |        0 |      1,535 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-03-15 |
| defi   | staking_yields    | AAVEV3-SCROLL        |   2,310 |        0 |      2,310 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-28 |
| defi   | staking_yields    | AAVEV3-ZKSYNC        |   2,290 |        0 |      2,290 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-08 |
| defi   | staking_yields    | BALANCER-ETHEREUM    |     820 |        0 |        820 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-03-30 |
| defi   | staking_yields    | COMPOUNDV3-ARBITRUM  |   1,928 |        0 |      1,928 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-12 |
| defi   | staking_yields    | COMPOUNDV3-BASE      |   2,063 |        0 |      2,063 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-25 |
| defi   | staking_yields    | COMPOUNDV3-ETHEREUM  |   1,697 |        0 |      1,697 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-24 |
| defi   | staking_yields    | COMPOUNDV3-OPTIMISM  |   2,236 |        0 |      2,236 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-14 |
| defi   | staking_yields    | COMPOUNDV3-POLYGON   |   1,870 |        0 |      1,870 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-02-13 |
| defi   | staking_yields    | COMPOUNDV3-SCROLL    |   2,303 |        0 |      2,303 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-04-21 |
| defi   | staking_yields    | CURVE-ETHEREUM       |     748 |        0 |        748 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-01-18 |
| defi   | staking_yields    | DRIFT-SOLANA         |   1,417 |        0 |      1,417 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-17 |
| defi   | staking_yields    | ETHENA-ETHEREUM      |   2,240 |        0 |      2,240 |                0 |         0 |     0 |  0% | 2018-01-01 | 2024-02-18 |
| defi   | staking_yields    | ETHERFI-ETHEREUM     |   1,940 |        0 |      1,940 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-24 |
| defi   | staking_yields    | FRAX-ETHEREUM        |   1,085 |        0 |      1,085 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-20 |
| defi   | staking_yields    | GMX-ARBITRUM         |   1,339 |        0 |      1,339 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-31 |
| defi   | staking_yields    | GMX-AVALANCHE        |   1,465 |        0 |      1,465 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-01-04 |
| defi   | staking_yields    | JITO-SOLANA          |   1,687 |        0 |      1,687 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-14 |
| defi   | staking_yields    | KAMINO-SOLANA        |   1,695 |        0 |      1,695 |                0 |         0 |     0 |  0% | 2018-01-01 | 2022-08-22 |
| defi   | staking_yields    | LIDO-ETHEREUM        |   1,083 |        0 |      1,083 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-12-18 |
| defi   | staking_yields    | MARINADE-SOLANA      |   1,309 |        0 |      1,309 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-01 |
| defi   | staking_yields    | ORCA-SOLANA          |   1,135 |        0 |      1,135 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-08 |
| defi   | staking_yields    | RAYDIUM-SOLANA       |   1,147 |        0 |      1,147 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-02-20 |
| defi   | staking_yields    | ROCKETPOOL-ETHEREUM  |   1,407 |        0 |      1,407 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-11-07 |
| defi   | staking_yields    | SUSHISWAPV3-ETHEREUM |   1,919 |        0 |      1,919 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-04-03 |
| defi   | staking_yields    | UNISWAPV2-ETHEREUM   |     854 |        0 |        854 |                0 |         0 |     0 |  0% | 2018-01-01 | 2020-05-03 |
| defi   | staking_yields    | UNISWAPV3-ARBITRUM   |   1,338 |        0 |      1,338 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-08-30 |
| defi   | staking_yields    | UNISWAPV3-BASE       |   2,046 |        0 |      2,046 |                0 |         0 |     0 |  0% | 2018-01-01 | 2023-08-08 |
| defi   | staking_yields    | UNISWAPV3-ETHEREUM   |   1,219 |        0 |      1,219 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-05-03 |
| defi   | staking_yields    | UNISWAPV3-OPTIMISM   |   1,445 |        0 |      1,445 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-15 |
| defi   | staking_yields    | UNISWAPV3-POLYGON    |   1,450 |        0 |      1,450 |                0 |         0 |     0 |  0% | 2018-01-01 | 2021-12-20 |
| defi   | staking_yields    | UNISWAPV4-ETHEREUM   |   2,587 |        0 |      2,587 |                0 |         0 |     0 |  0% | 2018-01-01 | 2025-01-30 |
| tradfi | ohlcv_1m          |                      |     826 |      791 |          0 |               35 |         0 |     0 |  0% | 2020-01-01 | 2026-04-10 |
| tradfi | ohlcv_1m          | BARCHART             |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | ohlcv_1m          | CBOE                 |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | ohlcv_1m          | CME                  |  65,400 |   62,911 |        933 |            1,556 |         0 |     0 |  0% | 2018-01-06 | 2026-05-21 |
| tradfi | ohlcv_1m          | FX                   |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | ohlcv_1m          | ICE                  |   3,172 |    2,240 |        927 |                5 |         0 |     0 |  0% | 2018-01-06 | 2026-05-14 |
| tradfi | ohlcv_1m          | NASDAQ               |   2,904 |    1,247 |        933 |              724 |         0 |     0 |  0% | 2018-01-06 | 2026-05-21 |
| tradfi | ohlcv_1m          | NYSE                 |   4,110 |    2,016 |        931 |            1,163 |         0 |     0 |  0% | 2018-01-06 | 2026-05-21 |
| tradfi | ohlcv_1m          | UNKNOWN              |     118 |      113 |          0 |                5 |         0 |     0 |  0% | 2020-01-01 | 2026-04-10 |
| tradfi | ohlcv_1m          | YAHOO_FINANCE        |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | trades            |                      |     944 |      904 |          0 |               40 |         0 |     0 |  0% | 2020-01-01 | 2026-04-10 |
| tradfi | trades            | BARCHART             |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | trades            | CBOE                 |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | trades            | CME                  |  19,481 |   17,650 |      1,171 |              660 |         0 |     0 |  0% | 2018-01-06 | 2026-05-18 |
| tradfi | trades            | FX                   |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | trades            | ICE                  |   1,607 |      679 |        928 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | trades            | NASDAQ               |   1,650 |      653 |        953 |               44 |         0 |     0 |  0% | 2018-01-06 | 2026-05-07 |
| tradfi | trades            | NYSE                 |   1,362 |      309 |        977 |               76 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |
| tradfi | trades            | UNKNOWN              |     118 |      113 |          0 |                5 |         0 |     0 |  0% | 2020-01-01 | 2026-04-10 |
| tradfi | trades            | YAHOO_FINANCE        |     931 |        0 |        931 |                0 |         0 |     0 |  0% | 2018-01-06 | 2026-05-03 |

## B. Per data_type × chain (chain-scoped data_types)

| data_type       | chain     |   rows | captured | empty_conf | attempted_failed | v9% | date_min   | date_max   |
| --------------- | --------- | -----: | -------: | ---------: | ---------------: | --: | ---------- | ---------- |
| lending_indices | ARBITRUM  |  6,140 |        0 |      6,140 |                0 |  0% | 2018-01-01 | 2023-04-12 |
| lending_indices | AVALANCHE |  3,000 |        0 |      3,000 |                0 |  0% | 2018-01-01 | 2022-03-15 |
| lending_indices | BASE      |  6,155 |        0 |      6,155 |                0 |  0% | 2018-01-01 | 2023-08-25 |
| lending_indices | BSC       |  1,921 |        0 |      1,921 |                0 |  0% | 2018-01-01 | 2023-04-05 |
| lending_indices | ETHEREUM  | 19,132 |        0 |     19,132 |                0 |  0% | 2018-01-01 | 2025-01-30 |
| lending_indices | LINEA     |  2,460 |        0 |      2,460 |                0 |  0% | 2018-01-01 | 2024-09-25 |
| lending_indices | OPTIMISM  |  5,357 |        0 |      5,357 |                0 |  0% | 2018-01-01 | 2024-02-14 |
| lending_indices | POLYGON   |  4,855 |        0 |      4,855 |                0 |  0% | 2018-01-01 | 2023-02-13 |
| lending_indices | SCROLL    |  4,613 |        0 |      4,613 |                0 |  0% | 2018-01-01 | 2024-04-28 |
| lending_indices | SOLANA    |  8,481 |        0 |      8,390 |               91 |  0% | 2018-01-01 | 2025-01-17 |
| lending_indices | ZKSYNC    |  2,290 |        0 |      2,290 |                0 |  0% | 2018-01-01 | 2024-04-08 |
| oracle_prices   | ARBITRUM  |  6,140 |        0 |      6,140 |                0 |  0% | 2018-01-01 | 2023-04-12 |
| oracle_prices   | AVALANCHE |  3,000 |        0 |      3,000 |                0 |  0% | 2018-01-01 | 2022-03-15 |
| oracle_prices   | BASE      |  6,155 |        0 |      6,155 |                0 |  0% | 2018-01-01 | 2023-08-25 |
| oracle_prices   | BSC       |  1,921 |        0 |      1,921 |                0 |  0% | 2018-01-01 | 2023-04-05 |
| oracle_prices   | ETHEREUM  | 24,185 |    5,053 |     19,132 |                0 |  0% | 2018-01-01 | 2026-01-23 |
| oracle_prices   | LINEA     |  2,460 |        0 |      2,460 |                0 |  0% | 2018-01-01 | 2024-09-25 |
| oracle_prices   | OPTIMISM  |  5,357 |        0 |      5,357 |                0 |  0% | 2018-01-01 | 2024-02-14 |
| oracle_prices   | POLYGON   |  4,855 |        0 |      4,855 |                0 |  0% | 2018-01-01 | 2023-02-13 |
| oracle_prices   | SCROLL    |  4,613 |        0 |      4,613 |                0 |  0% | 2018-01-01 | 2024-04-28 |
| oracle_prices   | SOLANA    |  8,390 |        0 |      8,390 |                0 |  0% | 2018-01-01 | 2022-08-22 |
| oracle_prices   | ZKSYNC    |  2,290 |        0 |      2,290 |                0 |  0% | 2018-01-01 | 2024-04-08 |
| perp_funding    | ARBITRUM  |  6,140 |        0 |      6,140 |                0 |  0% | 2018-01-01 | 2023-04-12 |
| perp_funding    | AVALANCHE |  3,000 |        0 |      3,000 |                0 |  0% | 2018-01-01 | 2022-03-15 |
| perp_funding    | BASE      |  6,155 |        0 |      6,155 |                0 |  0% | 2018-01-01 | 2023-08-25 |
| perp_funding    | BSC       |  1,921 |        0 |      1,921 |                0 |  0% | 2018-01-01 | 2023-04-05 |
| perp_funding    | ETHEREUM  | 19,132 |        0 |     19,132 |                0 |  0% | 2018-01-01 | 2025-01-30 |
| perp_funding    | LINEA     |  2,460 |        0 |      2,460 |                0 |  0% | 2018-01-01 | 2024-09-25 |
| perp_funding    | OPTIMISM  |  5,357 |        0 |      5,357 |                0 |  0% | 2018-01-01 | 2024-02-14 |
| perp_funding    | POLYGON   |  4,855 |        0 |      4,855 |                0 |  0% | 2018-01-01 | 2023-02-13 |
| perp_funding    | SCROLL    |  4,613 |        0 |      4,613 |                0 |  0% | 2018-01-01 | 2024-04-28 |
| perp_funding    | SOLANA    |  8,825 |        0 |      8,401 |              424 |  5% | 2018-01-01 | 2026-05-16 |
| perp_funding    | ZKSYNC    |  2,290 |        0 |      2,290 |                0 |  0% | 2018-01-01 | 2024-04-08 |
| staking_yields  | ARBITRUM  |  6,140 |        0 |      6,140 |                0 |  0% | 2018-01-01 | 2023-04-12 |
| staking_yields  | AVALANCHE |  3,000 |        0 |      3,000 |                0 |  0% | 2018-01-01 | 2022-03-15 |
| staking_yields  | BASE      |  6,155 |        0 |      6,155 |                0 |  0% | 2018-01-01 | 2023-08-25 |
| staking_yields  | BSC       |  1,921 |        0 |      1,921 |                0 |  0% | 2018-01-01 | 2023-04-05 |
| staking_yields  | ETHEREUM  | 19,132 |        0 |     19,132 |                0 |  0% | 2018-01-01 | 2025-01-30 |
| staking_yields  | LINEA     |  2,460 |        0 |      2,460 |                0 |  0% | 2018-01-01 | 2024-09-25 |
| staking_yields  | OPTIMISM  |  5,357 |        0 |      5,357 |                0 |  0% | 2018-01-01 | 2024-02-14 |
| staking_yields  | POLYGON   |  4,855 |        0 |      4,855 |                0 |  0% | 2018-01-01 | 2023-02-13 |
| staking_yields  | SCROLL    |  4,613 |        0 |      4,613 |                0 |  0% | 2018-01-01 | 2024-04-28 |
| staking_yields  | SOLANA    |  8,390 |        0 |      8,390 |                0 |  0% | 2018-01-01 | 2022-08-22 |
| staking_yields  | ZKSYNC    |  2,290 |        0 |      2,290 |                0 |  0% | 2018-01-01 | 2024-04-08 |

## C. schema_version distribution per data_type (read from DATA)

| ag     | data_type         |      rows | v-distribution   |
| ------ | ----------------- | --------: | ---------------- |
| cefi   | book_snapshot_5   |   782,181 | v8:782,181       |
| cefi   | derivative_ticker |   354,124 | v8:354,124       |
| cefi   | futures_chain     |   103,160 | v8:103,160       |
| cefi   | options_chain     |    65,768 | v8:65,768        |
| cefi   | trades            | 1,193,489 | v8:1,193,489     |
| defi   | lending_indices   |    64,404 | v8:64,404        |
| defi   | oracle_prices     |    69,366 | v8:69,366        |
| defi   | perp_funding      |    64,748 | v8:64,341 v9:407 |
| defi   | staking_yields    |    64,313 | v8:64,313        |
| tradfi | ohlcv_1m          |    80,254 | v8:80,254        |
| tradfi | trades            |    28,886 | v8:28,886        |

## D. empty_confirmed reasons (verify owed-data vs genuine absence)

| ag     | data_type       | error_reason                      |   rows |
| ------ | --------------- | --------------------------------- | -----: |
| defi   | lending_indices | EXPECTED_PRE_GENESIS_CHAIN        | 34,411 |
| defi   | oracle_prices   | EXPECTED_PRE_GENESIS_CHAIN        | 34,411 |
| defi   | perp_funding    | EXPECTED_PRE_GENESIS_CHAIN        | 34,411 |
| defi   | staking_yields  | EXPECTED_PRE_GENESIS_CHAIN        | 34,411 |
| defi   | lending_indices | EXPECTED_INSTRUMENT_NOT_LISTED    | 29,902 |
| defi   | oracle_prices   | EXPECTED_INSTRUMENT_NOT_LISTED    | 29,902 |
| defi   | perp_funding    | EXPECTED_INSTRUMENT_NOT_LISTED    | 29,902 |
| defi   | staking_yields  | EXPECTED_INSTRUMENT_NOT_LISTED    | 29,902 |
| tradfi | trades          | EXPECTED_WEEKEND                  |  7,224 |
| tradfi | ohlcv_1m        | EXPECTED_WEEKEND                  |  6,956 |
| tradfi | trades          | EXPECTED_HOLIDAY                  |    521 |
| tradfi | ohlcv_1m        | EXPECTED_HOLIDAY                  |    487 |
| cefi   | futures_chain   | EXPECTED_PRE_VENUE_LAUNCH         |     60 |
| cefi   | options_chain   | EXPECTED_PRE_VENUE_LAUNCH         |     60 |
| defi   | perp_funding    | EXPECTED_PAST_SOURCE_COVERAGE_END |      8 |
| tradfi | trades          | EXPECTED_OUT_OF_COVERAGE_WINDOW   |      8 |
| tradfi | ohlcv_1m        | SOURCE_RETURNED_ZERO              |      5 |
| defi   | perp_funding    | SOURCE_RETURNED_ZERO              |      3 |
