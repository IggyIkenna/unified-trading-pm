---
name: presentations-2026-03-13
overview: >
  Consolidates all presentation and business plans: 10 existing board presentations updated with latest system state, 3
  new presentations created (analytics, financials, status quo), Elysium DeFi partnership presentation, and GCP credits
  application. Hard deadlines: Rehearsal 2 March 18, Board meeting March 31.
type: business
epic: epic-business
status: active

completion_gates:
  code: none
  deployment: none
  business: B6

depends_on:
  - cicd_code_rollout_master_2026_03_13
  # Soft blocker: Plan 1 Phase 4 provides demo data for presentations

supersedes:
  - board_presentations_update_2026_03_10
  - elysium_defi_presentation_2026_03_10
  - gcp_credits_elysium_application_2026_03_10

todos:
  - id: presentations-update-existing
    content: >
      [HUMAN] P0. Update 10 existing board presentations with latest system state: current repo count (65), CI/CD
      pipeline status, version cascade, agent orchestration, coverage metrics, tier progression. Deadline: March 18
      (rehearsal 2).
    status: pending

  - id: presentations-create-new
    content: >
      [HUMAN+AGENT] P0. Create 3 new presentations: (1) Analytics — data pipeline, feature engineering, ML inference,
      (2) Financials — cost structure, GCP spend, projected revenue, (3) Status quo — current system state, what works,
      what's in progress. Deadline: March 18.
    status: pending

  - id: presentations-elysium-defi
    content: >
      [HUMAN+AGENT] P1. Elysium DeFi partnership presentation: architecture SVG showing 14-protocol coverage, backtest
      data from DeFi strategies, white-label fork capabilities, partnership terms. Deadline: March 31 (board meeting).
    status: pending

  - id: presentations-gcp-credits
    content: >
      [HUMAN] P1. GCP credits application via Google Cloud for Startups. Use Elysium Capital as applicant entity.
      Target: $150k credits covering 2-3 years compute. Requires Elysium materials from presentations-elysium-defi.
      Deadline: March 31.
    status: pending
    depends_on: [presentations-elysium-defi]

  - id: presentations-rehearsal-2
    content: >
      [HUMAN] P0. Rehearsal 2 delivery — all 13 presentations reviewed and polished. Date: March 18.
    status: pending
    depends_on: [presentations-update-existing, presentations-create-new]

  - id: presentations-board-meeting
    content: >
      [HUMAN] P0. Board meeting delivery — final presentations. Date: March 31.
    status: pending
    depends_on: [presentations-rehearsal-2, presentations-elysium-defi]
---
