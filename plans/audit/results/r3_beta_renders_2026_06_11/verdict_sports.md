# Verdict pack — SPORTS (G4 pre-apply, R7/R3 2026-06-11)

**Projection**: 786,508 rows (odds bucket; reference handled by the IS migrator — dry-run GREEN 2.67M rows).

**Adjudicated diff**: **GREEN — removed=0, captured_regressions=0.** 17,288 blank-status ODDS_API probe phantoms
honestly excluded; cell coverage identical.

**Open P1s (pre-apply)**: (1) 6,869 instruments-store rows with BLANK capture_status (characterize/re-stamp before
apply); (2) CF-5 oracle relabel fired zero relabels on MDPS (gates fall through — reason-relabel inert); (3)
C3_pre_launch_window 10,345 objects (2018-era footystats/api_football) need a UAC coverage-window decision. v1_archive:
integrity-clean + row-coverage 72,522/72,522 → drop-safe at G4.5.

**Evidence**: beta/live renders. Sweeps: odds E=0 + reference E=0 (19:09–19:10Z).

**G4 --apply for sports: AWAITING OPERATOR**
