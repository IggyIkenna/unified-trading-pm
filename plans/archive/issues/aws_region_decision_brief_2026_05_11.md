---
title: "AWS region decision brief — us-east-1 vs ap-northeast-1 (b+ Phase 0i)"
created: 2026-05-11
author: ikenna-extra-hands-tab
source:
  - plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md (Phase 0i)
  - plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md (GAP-2.4.F)
  - deployment-service/configs/cloud-providers.yaml (live yaml)
  - deployment-service/scripts/aws/setup-defi-buckets.sh:28 (region default)
  - configs/cloud-providers.yaml:59 (PM yaml default — pre-Phase-2 shape)
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# AWS region decision brief — us-east-1 vs ap-northeast-1

> **Severity**: P1 — region pinning under (b+) Phase 0i. Operator decision needed before Phase 0c provisioning lands
> (window 2026-05-15→05-19). **Suggested owner**: Ikenna operator decision; slot 4 Harsh implements per chosen region.
> **Drafted by extra-hands main-clone session.**

## TL;DR — actual state vs what the plan body assumes

The bucket_name_ssot plan body Phase 0i says: "GCP all `asia-northeast1` (Tokyo); AWS all `us-east-1` (Virginia) OR
operator decides to move AWS to `ap-northeast-1` (Tokyo) for matched-region within-cloud." This **understates the
current reality**:

- **`deployment-service/scripts/aws/setup-defi-buckets.sh:28`** — `REGION="${AWS_DEFAULT_REGION:-ap-northeast-1}"`
  (Tokyo). Line 14 comment: "defaults to ap-northeast-1 (Tokyo) per buildspec.aws.yaml."
- **The 10 DeFi buckets shipped 2026-05-08 via this script** were therefore provisioned in `ap-northeast-1`, NOT
  `us-east-1`.
- **`configs/cloud-providers.yaml:59` (PM stub yaml)** — `region: ${AWS_REGION:-us-east-1}` (Virginia). This is the
  STALE default; the setup script's `ap-northeast-1` overrides it operationally.

So the question isn't "stay us-east-1 or move to ap-northeast-1" — it's **"ratify the de-facto ap-northeast-1 standard
or revert to us-east-1."** The bias is toward ratify since the migration cost (already in ap-northeast-1) is zero.

## The 3 options

| Option  | Description                                                                | Setup-script default match?          | Migration cost                                                                                                                                                         | Operational match                                                                                                                               |
| ------- | -------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **(a)** | **Ratify ap-northeast-1 as canonical AWS region** (matched with GCP Tokyo) | ✅ Yes                               | Zero — already there. Update PM stub yaml `AWS_REGION` default to `ap-northeast-1`. Update plan body Phase 0i.                                                         | Best — within-cloud + cross-cloud both Tokyo (~1ms RTT GCP↔AWS within Tokyo); $0 within-cloud egress; minimal cross-cloud egress (same metro). |
| (b)     | Move AWS to us-east-1 (revert setup script + migrate the 10 DeFi buckets)  | ❌ No (script edit + data migration) | High — migrate 10 buckets from ap-northeast-1 → us-east-1 (~few hours data transfer + cross-region egress charges). Then provision Phase 0c bucket fleet in us-east-1. | Worst — adds GCP-Tokyo ↔ AWS-Virginia ~150ms RTT + cross-region egress charges (~$0.09/GB GCP→AWS).                                            |
| (c)     | Multi-region split (some buckets us-east-1, some ap-northeast-1)           | Partial                              | High — ongoing operational complexity tracking which kind lives where.                                                                                                 | Worst — defeats the (b+) "single region per cloud for $0 within-cloud sync" target.                                                             |

## Recommendation

**(a) — ratify ap-northeast-1 as canonical AWS region.** Three reasons:

1. **Zero migration cost** — buckets already in ap-northeast-1 per the setup script default that's been operational
   since 2026-05-08.
2. **Matched-region with GCP** — GCP `asia-northeast1` (Tokyo) + AWS `ap-northeast-1` (Tokyo) = same metro. Cross-cloud
   rsync (`aws_migration_defi_first` Phase 5) pays ~1ms RTT instead of ~150ms; cross-cloud egress charges drop ~10× vs
   trans-Pacific (GCP Tokyo → AWS Tokyo same-metro is ~$0.01-0.02/GB vs ~$0.09-0.12/GB for trans-Pacific).
3. **Citadel-grade discipline** — single region per cloud is the (b+) target; matched-region across clouds simplifies
   the cross-cloud sync mental model + eliminates a class of latency-sensitive bugs in cross-cloud reads.

## What lands if (a) approved

- **PM yaml stub fix** — `configs/cloud-providers.yaml:59` change default from `us-east-1` to `ap-northeast-1`. Surgical
  1-line edit.
- **Live yaml verification** — confirm `deployment-service/configs/cloud-providers.yaml` doesn't have a stale
  `AWS_REGION` default elsewhere; if it does, fix to match.
- **bucket_name_ssot plan body Phase 0i update** — replace "us-east-1 (Virginia) OR operator decides to move AWS to
  ap-northeast-1 (Tokyo)" with "ap-northeast-1 (Tokyo) — ratified per operator decision 2026-05-11; matched-region with
  GCP asia-northeast1 for $0 within-cloud egress + minimal cross-cloud egress."
- **code_freeze GAP-2.4.F update** — same content update.
- **Phase 0c provisioning** — Harsh slot 4 provisions the ~150 new AWS buckets in `ap-northeast-1` (matches existing
  - setup script default).
- **Cost projection** — for context: ~150 AWS buckets × variable storage. Same-region within-cloud sync (Phase 0h prod →
  staging/dev) = $0 egress. Cross-cloud rsync (only for AWS migration parity, GCP→AWS or AWS→GCP) = ~$0.01-0.02/GB metro
  (vs ~$0.09/GB trans-Pacific). For a 10TB cross-cloud sync: $100-200 metro vs $900+ trans-Pacific = ~5x savings.
- **CLAUDE.md key rule update** — bucket-name SSOT operator decision (b+) entry already says "GCP all asia-northeast1
  (Tokyo); AWS all us-east-1 (or ap-northeast-1 for matched region per operator decision)." Update to "AWS all
  ap-northeast-1 (Tokyo) — matched-region with GCP per operator ratification 2026-05-11."

## What lands if (b) approved (revert to us-east-1)

This is the high-cost option. If selected:

- Migrate 10 existing DeFi buckets (and any other ap-northeast-1 buckets) to us-east-1 via `aws s3 sync` cross-region
  copy. Several-hour data transfer + cross-region egress fees.
- Update setup-defi-buckets.sh + buildspec.aws.yaml + PM stub yaml + live yaml to default us-east-1.
- Provision Phase 0c new buckets in us-east-1.
- Pay the ~150ms RTT cost on every cross-cloud rsync going forward + ~5x cross-cloud egress.
- Net: ~1-2 AI-day extra for the migration + ongoing latency + cost premium.

**Don't recommend unless** there's a non-obvious reason like AWS service availability (some niche AWS service only in
us-east-1 — not the case for S3 / EC2 / Lambda we use) or compliance (no current driver).

## Composes with

- [`bucket_name_ssot_canonicalisation_2026_05_10.md`](../bucket_name_ssot_canonicalisation_2026_05_10.md) Phase 0i —
  this brief is the operator-input doc for that phase.
- [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  GAP-2.4.F — same.
- [`aws_migration_defi_first_2026_05_07.md`](../aws_migration_defi_first_2026_05_07.md) Phase 2 — region default for the
  ~150 NEW AWS buckets to provision.
- CLAUDE.md "Bucket-name SSOT operator decision (b+)" key rule — region pinning sub-bullet.

## Operator action

Reply: `(a)` ratify ap-northeast-1 / `(b)` revert to us-east-1 / `(c)` multi-region split / hold + reason. Slot 1 (or
this session) implements per decision.

## ✅ RESOLVED 2026-05-11 — Operator answer: (a) ratify ap-northeast-1

**Status**: ✅ RESOLVED. Operator (Ikenna) decision: **option (a) — ratify ap-northeast-1 (Tokyo) for AWS** as the
canonical region for matched-region pairing with GCP `asia-northeast1`.

**What landed** (PM@<this commit>):

- `configs/cloud-providers.yaml:59` — `${AWS_REGION:-us-east-1}` → `${AWS_REGION:-ap-northeast-1}` + comment citing
  operator decision 2026-05-11.
- `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0i — flipped `[ ] P1` → `[x] P1` with operator-ratified
  status; AWS canonical region documented as `ap-northeast-1`.
- `code_freeze_migrate_backfill_sequencing_2026_05_10.md` GAP-2.4.F — annotated "OPERATOR RATIFIED ap-northeast-1
  2026-05-11"; same-metro Tokyo trade-off captured.
- `cursor-configs/CLAUDE.md` "Bucket-name SSOT operator decision (b+)" key rule — Region pinning sub-bullet updated to
  AWS `ap-northeast-1` ratified.
- Cross-side ping in `plans/active/_agent_pings.md` confirming (a) so Harsh slot 4 provisions Phase 0c buckets in
  `ap-northeast-1`.

**Net cost / benefit**:

- Migration cost: **zero** (already in ap-northeast-1 per setup script default).
- Within-cloud sync (Phase 0h) ongoing cost: $0 egress (single region).
- Cross-cloud rsync ongoing cost: ~5× cheaper than trans-Pacific (~$0.01-0.02/GB metro vs ~$0.09/GB trans-Pacific).
- Latency: GCP ↔ AWS Tokyo same-metro = ~1ms RTT (vs ~150ms trans-Pacific).

**Phase 0c provisioning direction for Harsh slot 4**: provision the ~150 new AWS buckets in `ap-northeast-1`. Use
`setup-defi-buckets.sh` pattern (defaults match) or extend Terraform with explicit `region = "ap-northeast-1"`. Reject
any `aws s3 mb --region=<other>` invocation per GAP-2.4.F + Phase 0i.
