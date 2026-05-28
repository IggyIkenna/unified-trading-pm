# Slot 9 ping file — re-themed 2026-05-19

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-19 14:47 UTC] [main → slot 9] — RE-THEMED via --reset-slot. Prior theme: TBD (main fills from yesterday's
LEDGER + prior plan's DONE block on first read). New theme: TBD (main fills from today's work-split + plan-of-record +
spawn prompt).

[2026-05-20 UTC] [slot 9 → main] — DONE: QG GREEN SWEEP Cluster A complete.

- UAC: was already green, no changes needed.
- UTL: 9 codex violations fixed (imports-inside-functions checker bug fixed in PM; noqa/config-bootstrap exemptions for
  os.environ; print() false-positive fixed by renaming \_fingerprint→_schema_sig; empty fallbacks noqa'd; hardcoded
  project IDs removed from docstrings; SIZE_EXTRA_EXCLUDES/BROAD_EXCEPT_EXTRA_EXCLUDES/PIP_AUDIT_EXTRA_ARGS added to
  quality-gates.sh). utl@f63eb8e2 + pm@424b4319 pushed to live-defi-rollout.
- IS: was already green (CODEX_MAX_VIOLATIONS=4 within tolerance), no changes needed. Plan-of-record:
  work_split_2026_05_20_ikenna.md § Slot 9.

[2026-05-28 05:58 UTC] [slot 9 → main] — BLOCKED-OPERATOR-DECISION: pipeline_mode removal vs implementation

Working on cefi_venue_backfill_coverage_remediation_2026_05_27.md §6I item 3. The `pipeline_mode` column is empty/NULL
on every manifest row and absent as on-disk partition. Code passes values (BATCH_TARDIS, BATCH_DATABENTO, etc.) but
they're not persisted. Options: (1) REMOVE entirely (~50+ files, cleaner per "no technical debt"), or (2) IMPLEMENT
properly (adds partition dimension). Recommend REMOVE. Need operator decision to proceed.

[2026-05-28 06:05 UTC] [slot 9 → main] — PROGRESS: §6I manifest/migration defects

Completed from cefi_venue_backfill_coverage_remediation_2026_05_27.md §6I:

- ✅ Item 3: Chain dimension-modeling bug fixed — market-tick-data-service@2e91d74f
- ✅ Item 4: Phantom expected rows for inapplicable venue × data_type fixed — market-tick-data-service@3fa29d70
- ⏸️ Item 2: pipeline_mode decision — awaiting operator direction (see above)

Items 1 (env-tiered bucket cutover), 5 (instrument_type case drift), 6 (loose parquet files) still pending. Continuing
investigation on item 1 (dual-write issue) while awaiting pipeline_mode decision.
