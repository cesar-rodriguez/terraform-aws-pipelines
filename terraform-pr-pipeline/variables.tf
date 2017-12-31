variable "aws_region" {
  description = "AWS region where resources are provisioned"
}

variable "aws_profile" {
  description = "AWS credentials profile to use"
}

variable "project_name" {
  description = "All resources will be prepended with this name"
}

variable "github_api_url" {
  description = "API URL for GitHub"
  default     = "https://api.github.com"
}

/*
variable "github_pac" {
  description = "GitHub Personal Access Token"
}
*/

variable "github_repo_name" {
  description = "Name of the repository to track pull requests in org/repo format (e.g. cesar-rodriguez/test-repo)"
}
