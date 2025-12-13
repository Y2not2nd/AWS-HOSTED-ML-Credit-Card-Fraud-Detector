output "ecr_repository_url" {
  value = aws_ecr_repository.inference.repository_url
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}
