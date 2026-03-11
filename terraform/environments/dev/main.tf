# Terraform: uts-dev-ikenna GCP Project
# Purpose: Isolated Cloud Build + Artifact Registry for feat/* branch builds

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
    prefix = "unified-trading/dev"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  default = "uts-dev-ikenna"
}

variable "region" {
  default = "asia-northeast1"
}

# Enable required APIs
resource "google_project_service" "cloudbuild" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Artifact Registry: Docker images
resource "google_artifact_registry_repository" "unified_trading" {
  repository_id = "unified-trading"
  location      = var.region
  format        = "DOCKER"
  description   = "Unified trading system Docker images (dev / feat/* branches)"

  # 90-day lifecycle cleanup for dev images
  cleanup_policies {
    id     = "delete-old-untagged"
    action = "DELETE"
    condition {
      older_than = "90d"
    }
  }

  depends_on = [google_project_service.artifactregistry]
}

# Cloud Build service account
resource "google_service_account" "cloud_build" {
  account_id   = "cloud-build-sa"
  display_name = "Cloud Build Service Account (dev)"
}

# IAM: AR Writer
resource "google_project_iam_member" "cb_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

# IAM: Cloud Run Developer
resource "google_project_iam_member" "cb_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

# IAM: Secret Manager Accessor
resource "google_project_iam_member" "cb_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

output "artifact_registry_host" {
  value = "${var.region}-docker.pkg.dev"
}

output "artifact_registry_repo" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/unified-trading"
}

output "cloud_build_sa_email" {
  value = google_service_account.cloud_build.email
}
