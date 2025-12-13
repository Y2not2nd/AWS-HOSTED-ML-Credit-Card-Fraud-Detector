locals {
  github_oidc_url   = "https://token.actions.githubusercontent.com"
  github_repo_full  = "${var.github_org}/${var.github_repo}"
  github_sub_ref    = "repo:${local.github_repo_full}:ref:${var.github_ref}"
}

data "tls_certificate" "github_actions" {
  url = local.github_oidc_url
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = local.github_oidc_url
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [
    data.tls_certificate.github_actions.certificates[0].sha1_fingerprint
  ]
}

data "aws_iam_policy_document" "github_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.github_sub_ref]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "ml-platform-github-actions"
  assume_role_policy = data.aws_iam_policy_document.github_assume_role.json
}

resource "aws_iam_role_policy_attachment" "github_admin" {
  role       = aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
