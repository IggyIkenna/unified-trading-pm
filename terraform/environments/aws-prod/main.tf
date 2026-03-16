# Terraform: AWS Production — Unified Trading System
# Purpose: ECR repositories + CodeBuild projects + IAM roles for production builds
# Mirrors GCP prod (Cloud Build + Artifact Registry) for AWS multi-cloud deployment.
#
# What this creates:
#   - S3 backend for Terraform state
#   - ECR repository per service (31 services) + per library (1 base image)
#   - CodeBuild project per service (reads buildspec.aws.yaml from each repo)
#   - IAM role for CodeBuild with ECR push/pull + CloudWatch Logs permissions
#   - CloudWatch log group for build logs
#
# What this does NOT create (future phases):
#   - ECS cluster / Fargate task definitions (phase 2)
#   - VPC / subnets / security groups (phase 2)
#   - ALB / target groups (phase 2)
#   - Secrets Manager secrets (phase 2)
#   - Route53 / ACM certificates (phase 2)

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "uts-terraform-state-aws"
    key    = "unified-trading/prod/terraform.tfstate"
    region = "ap-northeast-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# ---------------------------------------------------------------------------
# S3 bucket for Terraform state (bootstrap — create manually or import)
# ---------------------------------------------------------------------------
# NOTE: This bucket must exist BEFORE `terraform init`. Create it manually:
#   aws s3api create-bucket \
#     --bucket uts-terraform-state-aws \
#     --region ap-northeast-1 \
#     --create-bucket-configuration LocationConstraint=ap-northeast-1
#   aws s3api put-bucket-versioning \
#     --bucket uts-terraform-state-aws \
#     --versioning-configuration Status=Enabled

# ---------------------------------------------------------------------------
# ECR Repositories — one per service + one per library base image
# ---------------------------------------------------------------------------

resource "aws_ecr_repository" "services" {
  for_each = toset(var.service_repos)

  name                 = each.value
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    ServiceName = each.value
    RepoType    = "service"
  }
}

resource "aws_ecr_repository" "libraries" {
  for_each = toset(var.library_repos)

  name                 = each.value
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    ServiceName = each.value
    RepoType    = "library"
  }
}

# ECR lifecycle policy — keep last 10 tagged images + delete untagged after 7 days
resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Remove untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 20 tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "latest", "staging", "main"]
          countType     = "imageCountMoreThan"
          countNumber   = 20
        }
        action = {
          type = "expire"
        }
      },
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "libraries" {
  for_each   = aws_ecr_repository.libraries
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Remove untagged images after 14 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 14
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 30 library images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 30
        }
        action = {
          type = "expire"
        }
      },
    ]
  })
}

# ---------------------------------------------------------------------------
# IAM Role for CodeBuild
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "codebuild_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild" {
  name               = "${var.project_name}-codebuild-role"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume_role.json

  tags = {
    Purpose = "CodeBuild service role for all UTS builds"
  }
}

# ECR permissions: pull base images + push built images
data "aws_iam_policy_document" "codebuild_ecr" {
  statement {
    sid    = "ECRAuth"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ECRPullPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:CreateRepository",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [
      "arn:aws:ecr:${var.aws_region}:${var.aws_account_id}:repository/*",
    ]
  }
}

resource "aws_iam_role_policy" "codebuild_ecr" {
  name   = "${var.project_name}-codebuild-ecr"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.codebuild_ecr.json
}

# CloudWatch Logs permissions
data "aws_iam_policy_document" "codebuild_logs" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/codebuild/${var.project_name}/*",
      "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/codebuild/${var.project_name}/*:*",
    ]
  }
}

resource "aws_iam_role_policy" "codebuild_logs" {
  name   = "${var.project_name}-codebuild-logs"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.codebuild_logs.json
}

# S3 permissions (for CodeBuild cache and artifacts)
data "aws_iam_policy_document" "codebuild_s3" {
  statement {
    sid    = "S3CacheAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:GetBucketAcl",
      "s3:GetBucketLocation",
    ]
    resources = [
      "arn:aws:s3:::${var.project_name}-codebuild-cache",
      "arn:aws:s3:::${var.project_name}-codebuild-cache/*",
    ]
  }
}

resource "aws_iam_role_policy" "codebuild_s3" {
  name   = "${var.project_name}-codebuild-s3"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.codebuild_s3.json
}

# ---------------------------------------------------------------------------
# CloudWatch Log Group for CodeBuild
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "codebuild" {
  name              = "/codebuild/${var.project_name}"
  retention_in_days = 30

  tags = {
    Purpose = "CodeBuild build logs for all UTS services"
  }
}

# ---------------------------------------------------------------------------
# S3 bucket for CodeBuild cache
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "codebuild_cache" {
  bucket = "${var.project_name}-codebuild-cache"

  tags = {
    Purpose = "CodeBuild pip/docker cache for UTS builds"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "codebuild_cache" {
  bucket = aws_s3_bucket.codebuild_cache.id

  rule {
    id     = "expire-old-cache"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "codebuild_cache" {
  bucket = aws_s3_bucket.codebuild_cache.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "codebuild_cache" {
  bucket = aws_s3_bucket.codebuild_cache.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------------------------------------------------------------------------
# CodeBuild Projects — one per service
# ---------------------------------------------------------------------------
# Each project references buildspec.aws.yaml in the repo root.
# Source is GitHub (IggyIkenna org). Webhook triggers on push to main.

resource "aws_codebuild_project" "services" {
  for_each = toset(var.service_repos)

  name         = "${var.project_name}-${each.value}"
  description  = "Build and push ${each.value} Docker image to ECR"
  service_role = aws_iam_role.codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = var.codebuild_compute_type
    image                       = var.codebuild_image
    type                        = "LINUX_CONTAINER"
    privileged_mode             = true # Required for docker-in-docker
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = var.aws_account_id
    }

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "SERVICE_NAME"
      value = each.value
    }

    environment_variable {
      name  = "REGISTRY_REPO"
      value = "unified-trading-system"
    }

    environment_variable {
      name  = "IMAGE_TAG"
      value = "latest"
    }
  }

  source {
    type            = "GITHUB"
    location        = "https://github.com/IggyIkenna/${each.value}.git"
    buildspec       = "buildspec.aws.yaml"
    git_clone_depth = 1

    git_submodules_config {
      fetch_submodules = false
    }
  }

  source_version = "main"

  cache {
    type     = "S3"
    location = "${aws_s3_bucket.codebuild_cache.bucket}/${each.value}"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = aws_cloudwatch_log_group.codebuild.name
      stream_name = each.value
    }
  }

  build_timeout = 30 # minutes

  tags = {
    ServiceName = each.value
  }
}

# CodeBuild project for library base image
resource "aws_codebuild_project" "libraries" {
  for_each = toset(var.library_repos)

  name         = "${var.project_name}-${each.value}"
  description  = "Build and push ${each.value} base image to ECR"
  service_role = aws_iam_role.codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = var.codebuild_compute_type
    image                       = var.codebuild_image
    type                        = "LINUX_CONTAINER"
    privileged_mode             = true
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = var.aws_account_id
    }

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }
  }

  source {
    type            = "GITHUB"
    location        = "https://github.com/IggyIkenna/${each.value}.git"
    buildspec       = "buildspec.aws.yaml"
    git_clone_depth = 1

    git_submodules_config {
      fetch_submodules = false
    }
  }

  source_version = "main"

  cache {
    type     = "S3"
    location = "${aws_s3_bucket.codebuild_cache.bucket}/${each.value}"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = aws_cloudwatch_log_group.codebuild.name
      stream_name = each.value
    }
  }

  build_timeout = 45 # libraries take longer

  tags = {
    ServiceName = each.value
    RepoType    = "library"
  }
}

# ---------------------------------------------------------------------------
# GitHub webhook for CodeBuild (optional — requires GitHub OAuth connection)
# ---------------------------------------------------------------------------
# NOTE: CodeBuild GitHub webhooks require a one-time OAuth connection.
# After `terraform apply`, connect GitHub via the AWS Console:
#   CodeBuild > Account Settings > Source provider > GitHub > Connect
# Then uncomment and apply the webhook resources below.

# resource "aws_codebuild_webhook" "services" {
#   for_each     = aws_codebuild_project.services
#   project_name = each.value.name
#
#   build_type = "BUILD"
#
#   filter_group {
#     filter {
#       type    = "EVENT"
#       pattern = "PUSH"
#     }
#     filter {
#       type    = "HEAD_REF"
#       pattern = "^refs/heads/main$"
#     }
#   }
# }
