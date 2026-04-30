# Live-universe schema drift report

- Generated: 2026-04-30T16:15:14.177918+00:00
- Backend: `http://localhost:8030`
- Fixtures: `/home/hk/unified-trading-system-repos/unified-trading-api/tests/fixtures/live-universe`
- Total findings: 2

## cefi

- [content] 451/3690 rows failed UAC validation. First 3:
  row 3074: 1 validation error for StrictInstrumentRecord
  row 3075: 1 validation error for StrictInstrumentRecord
  row 3076: 1 validation error for StrictInstrumentRecord

## tradfi

- [content] 6313/14202 rows failed UAC validation. First 3:
  row 7319: 1 validation error for StrictInstrumentRecord
  row 7320: 1 validation error for StrictInstrumentRecord
  row 7321: 1 validation error for StrictInstrumentRecord

## defi

Clean — no drift detected.
