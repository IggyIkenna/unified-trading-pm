# Compliance GCP Project Setup

## Status: BLOCKED on human action (step 1)

## Why a separate project?

MiFID II Art. 25 and SEC Rule 17a-4 require that the audit custodian is independent of the writing system. A
same-project bucket in uts-prod-ikenna is insufficient -- the compliance store must be in a separate GCP project with
separate billing.

## Setup steps

### 1. [HUMAN] Create GCP project

```bash
gcloud projects create uts-compliance-ikenna --name="UTS Compliance"
gcloud billing projects link uts-compliance-ikenna --billing-account=BILLING_ACCOUNT_ID
```

Use a DIFFERENT billing account from uts-prod-ikenna if possible.

### 2. [HUMAN] Create Terraform state bucket (if not shared)

The Terraform backend uses `gs://uts-terraform-state/unified-trading/compliance`. The state bucket already exists
(shared across environments). No action needed if using the same state bucket.

### 3. [HUMAN/AGENT] Apply Terraform

```bash
cd unified-trading-pm/terraform/environments/compliance
terraform init
terraform plan
terraform apply
```

This creates:

- `compliance-subscriber` SA with append-only GCS + BQ insert permissions
- `uts-compliance-ikenna-events` bucket (7-year WORM retention)
- `uts-compliance-ikenna-audit-archive` bucket (Coldline at 90d, Archive at 1y)
- `compliance_events` BigQuery dataset

### 4. [HUMAN] Export SA key and add to GitHub secrets

```bash
# Create key for compliance subscriber SA
gcloud iam service-accounts keys create /tmp/compliance-sa-key.json \
  --iam-account=compliance-subscriber@uts-compliance-ikenna.iam.gserviceaccount.com

# Add to GitHub secrets (DIFFERENT name from GCP_SA_KEY_PROD)
gh secret set COMPLIANCE_SA_KEY < /tmp/compliance-sa-key.json \
  --repo IggyIkenna/unified-trading-pm

# Clean up local key
rm /tmp/compliance-sa-key.json
```

### 5. [HUMAN] Verify isolation

Confirm no SA from uts-prod-ikenna has write access to the compliance bucket:

```bash
gsutil iam get gs://uts-compliance-ikenna-events | grep serviceAccount
# Should only show compliance-subscriber@uts-compliance-ikenna
```

### 6. Rotation schedule

The compliance SA key must be on a SEPARATE rotation schedule from GCP_SA_KEY_PROD. Add to
`plans/ops/secret-rotation-plan.md` with its own rotation date.
