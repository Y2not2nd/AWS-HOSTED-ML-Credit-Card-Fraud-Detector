resource "aws_iam_policy" "ebs_csi" {
  name   = "AmazonEBSCSIDriverPolicy"
  policy = file("${path.module}/policies/ebs-csi-policy.json")
}

resource "aws_iam_role" "ebs_csi_irsa" {
  name = "AmazonEKS_EBS_CSI_DriverRole"

  assume_role_policy = data.aws_iam_policy_document.ebs_csi_assume.json
}

data "aws_iam_policy_document" "ebs_csi_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider}:sub"
      values   = ["system:serviceaccount:kube-system:ebs-csi-controller-sa"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ebs_attach" {
  role       = aws_iam_role.ebs_csi_irsa.name
  policy_arn = aws_iam_policy.ebs_csi.arn
}

resource "aws_eks_addon" "ebs_csi" {
  cluster_name             = module.eks.cluster_name
  addon_name               = "aws-ebs-csi-driver"
  service_account_role_arn = aws_iam_role.ebs_csi_irsa.arn
}

resource "aws_eks_addon" "cloudwatch" {
  cluster_name = module.eks.cluster_name
  addon_name   = "amazon-cloudwatch-observability"
}
