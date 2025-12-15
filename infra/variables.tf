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

variable "frontend_domain_name" {
  description = "Fully qualified domain name for the frontend (e.g. app.example.com)"
  type        = string
}

variable "frontend_domain_zone" {
  description = "Route53 hosted zone domain (e.g. example.com)"
  type        = string
}

