variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "YAS-ML-EKS"
}

variable "ecr_repo_name" {
  description = "ECR repository name"
  type        = string
  default     = "yas-ml-inference"
}

variable "github_org" {
  description = "GitHub organisation or username"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name only, without org"
  type        = string
}

variable "github_ref" {
  description = "Git reference allowed to assume role"
  type        = string
  default     = "refs/heads/main"
}
