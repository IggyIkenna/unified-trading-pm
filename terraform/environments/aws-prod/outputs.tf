# Outputs for AWS production environment

output "ecr_registry_url" {
  description = "ECR registry URL prefix (account.dkr.ecr.region.amazonaws.com)"
  value       = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

output "ecr_service_repos" {
  description = "Map of service name to ECR repository URL"
  value = {
    for name, repo in aws_ecr_repository.services :
    name => repo.repository_url
  }
}

output "ecr_library_repos" {
  description = "Map of library name to ECR repository URL"
  value = {
    for name, repo in aws_ecr_repository.libraries :
    name => repo.repository_url
  }
}

output "codebuild_role_arn" {
  description = "ARN of the IAM role used by all CodeBuild projects"
  value       = aws_iam_role.codebuild.arn
}

output "codebuild_project_names" {
  description = "Map of service name to CodeBuild project name"
  value = {
    for name, project in aws_codebuild_project.services :
    name => project.name
  }
}

output "codebuild_cache_bucket" {
  description = "S3 bucket used for CodeBuild cache"
  value       = aws_s3_bucket.codebuild_cache.bucket
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for all CodeBuild builds"
  value       = aws_cloudwatch_log_group.codebuild.name
}
