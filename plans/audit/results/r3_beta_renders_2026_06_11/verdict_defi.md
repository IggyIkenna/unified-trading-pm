# Verdict pack — DEFI (G4 pre-apply, R7/R3 2026-06-11)

**Projection**: 1,580,037 rows. First-ever CF-11 honest-absence re-emit for defi (the pure object-scan was silently
dropping the 1.23M-row absence corpus — fixed mtds@77f1a61).

**Adjudicated diff**: removed=5,320, captured_regressions=0 (was 810 pre-adjudication). All removals are
respelling-supersession: AAVEV3/UNISWAPV2/3/4 venue-spelling duplicates (canonical twins verified 0-missing) + 104
EIGENLAYER data_type/instrument_type respells.

**Evidence**: beta/live renders as above. Sweep: E=0/unknown=0 (18:52Z). Also fixed in this wave: processed-candle
corpus pass-through (prior code falsely phantom-demoted captured processed rows — a REAL-RUN bug, not just projection).

**G4 --apply for defi: AWAITING OPERATOR**
