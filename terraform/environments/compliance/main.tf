# Terraform: uts-compliance-ikenna GCP Project
# Purpose: Independent compliance custodian for MiFID II Art. 25 / SEC Rule 17a-4.
# Separate GCP project ensures custodial independence from uts-prod-ikenna.
#
# PREREQUISITE (HUMAN): Create uts-compliance-ikenna project with a separate
# billing account before applying this config. See compliance-setup.md in this dir.

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "uts-terraform-state"
    prefix = "unified-trading/compliance"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  default = "uts-compliance-ikenna"
}

variable "region" {
  default = "asia-northeast1"
}

# ── Enable required APIs ─────────────────────────────────────────────────────

resource "google_project_service" "storage" {
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "bigquery" {
  service            = "bigquery.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

# ── Compliance subscriber service account ────────────────────────────────────
# This SA has append-only GCS + BQ insert permissions ONLY.
# No SA from uts-prod-ikenna has write access to this bucket.

resource "google_service_account" "compliance_subscriber" {
  account_id   = "compliance-subscriber"
  display_name = "Compliance Subscriber SA"
  description  = "Append-only access to compliance GCS bucket and BigQuery dataset. Used by GHA workflows and compliance event subscriber."
}

# ── GCS: compliance events bucket (7-year WORM retention) ────────────────────

resource "google_storage_bucket" "compliance_events" {
  name          = "uts-compliance-ikenna-events"
  location      = var.region
  storage_class = "STANDARD"
  force_destroy = false

  # 7-year WORM retention (MiFID II / SEC 17a-4)
  retention_policy {
    is_locked        = true
    retention_period = 220752000 # 7 years in seconds (7 * 365.25 * 24 * 3600)
  }

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  depends_on = [google_project_service.storage]
}

# ── GCS: audit archive bucket (cold storage for old audit files) ─────────────

resource "google_storage_bucket" "audit_archive" {
  name          = "uts-compliance-ikenna-audit-archive"
  location      = var.region
  storage_class = "STANDARD"
  force_destroy = false

  # Lifecycle: move to Coldline after 90 days, Archive after 1 year
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
  }

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  depends_on = [google_project_service.storage]
}

# ── IAM: compliance SA can append to compliance events bucket ────────────────

resource "google_storage_bucket_iam_member" "compliance_events_writer" {
  bucket = google_storage_bucket.compliance_events.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.compliance_subscriber.email}"
}

# ── IAM: compliance SA can append to audit archive bucket ────────────────────

resource "google_storage_bucket_iam_member" "audit_archive_writer" {
  bucket = google_storage_bucket.audit_archive.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.compliance_subscriber.email}"
}

# ── BigQuery: compliance_events dataset ──────────────────────────────────────

resource "google_bigquery_dataset" "compliance_events" {
  dataset_id  = "compliance_events"
  location    = var.region
  description = "Immutable audit trail for manifest mutations, auth events, deployment events. MiFID II / SEC 17a-4 compliant."

  # Default 7-year expiration on tables (matches WORM policy)
  default_table_expiration_ms = 220752000000 # 7 years in milliseconds

  depends_on = [google_project_service.bigquery]
}

# ── IAM: compliance SA can insert rows into BigQuery ─────────────────────────

resource "google_bigquery_dataset_iam_member" "compliance_bq_editor" {
  dataset_id = google_bigquery_dataset.compliance_events.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.compliance_subscriber.email}"
}

# ── Outputs ──────────────────────────────────────────────────────────────────

output "compliance_subscriber_sa_email" {
  value       = google_service_account.compliance_subscriber.email
  description = "Email of the compliance subscriber service account. Store as GH secret COMPLIANCE_SA_KEY (separate from GCP_SA_KEY_PROD)."
}

output "compliance_events_bucket" {
  value       = google_storage_bucket.compliance_events.name
  description = "GCS bucket for compliance events (7-year WORM retention)"
}

output "audit_archive_bucket" {
  value       = google_storage_bucket.audit_archive.name
  description = "GCS bucket for cold storage of old audit files"
}

output "compliance_bq_dataset" {
  value       = google_bigquery_dataset.compliance_events.dataset_id
  description = "BigQuery dataset for compliance events"
}
