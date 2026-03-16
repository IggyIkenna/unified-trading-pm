# Variables for AWS production environment
# Mirrors the GCP prod pattern but for AWS CodeBuild + ECR + ECS/Fargate

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "uts-prod"
}

variable "aws_account_id" {
  description = "AWS account ID (used for ECR URI construction)"
  type        = string
  default     = "427895769566"
}

# ---------------------------------------------------------------------------
# Service list — every repo that produces a Docker image and runs in ECS.
# Derived from workspace-manifest.json (services + api-services + batch).
# Libraries (unified-trading-library) get their own ECR repo but no ECS task.
# ---------------------------------------------------------------------------

variable "service_repos" {
  description = "Services that need ECR repos + CodeBuild projects + ECS task definitions"
  type        = list(string)
  default = [
    # --- Services (21) ---
    "alerting-service",
    "elysium-defi-system",
    "execution-service",
    "features-calendar-service",
    "features-commodity-service",
    "features-cross-instrument-service",
    "features-delta-one-service",
    "features-multi-timeframe-service",
    "features-onchain-service",
    "features-sports-service",
    "features-volatility-service",
    "instruments-service",
    "market-data-processing-service",
    "market-tick-data-service",
    "ml-inference-service",
    "ml-training-service",
    "pnl-attribution-service",
    "position-balance-monitor-service",
    "risk-and-exposure-service",
    "strategy-service",
    "trading-agent-service",
    # --- API services (8) ---
    "batch-audit-api",
    "client-reporting-api",
    "deployment-api",
    "execution-results-api",
    "market-data-api",
    "ml-inference-api",
    "ml-training-api",
    "trading-analytics-api",
    # --- Batch services (1) ---
    "batch-live-reconciliation-service",
    # --- Config API (1) ---
    "config-api",
  ]
}

variable "library_repos" {
  description = "Libraries that need ECR repos (base images) but no ECS task"
  type        = list(string)
  default = [
    "unified-trading-library",
  ]
}

variable "codebuild_compute_type" {
  description = "CodeBuild compute type"
  type        = string
  default     = "BUILD_GENERAL1_SMALL"
}

variable "codebuild_image" {
  description = "CodeBuild Docker image (must support docker-in-docker)"
  type        = string
  default     = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "unified-trading-system"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}
