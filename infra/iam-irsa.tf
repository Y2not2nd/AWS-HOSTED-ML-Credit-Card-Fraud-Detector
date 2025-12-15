resource "aws_iam_role" "airflow_worker_irsa" {
  name = "airflow-worker-irsa"

  assume_role_policy = file("${path.module}/policies/airflow-worker-trust.json")
}

resource "aws_iam_policy" "airflow_s3_read" {
  name   = "airflow-ml-s3-read"
  policy = file("${path.module}/policies/airflow-ml-s3-read.json")
}

resource "aws_iam_role_policy_attachment" "airflow_attach" {
  role       = aws_iam_role.airflow_worker_irsa.name
  policy_arn = aws_iam_policy.airflow_s3_read.arn
}

resource "aws_iam_role" "mlflow_irsa" {
  name = "mlflow-irsa"

  assume_role_policy = file("${path.module}/policies/mlflow-trust.json")
}

resource "aws_iam_policy" "mlflow_s3_rw" {
  name   = "mlflow-s3-write"
  policy = file("${path.module}/policies/mlflow-s3-write.json")
}

resource "aws_iam_role_policy_attachment" "mlflow_attach" {
  role       = aws_iam_role.mlflow_irsa.name
  policy_arn = aws_iam_policy.mlflow_s3_rw.arn
}

resource "aws_iam_role" "inference_green_irsa" {
  name = "credit-fraud-inference-green-irsa"

  assume_role_policy = file("${path.module}/policies/credit-fraud-inference-green-trust.json")
}

resource "aws_iam_policy" "inference_s3_read" {
  name   = "credit-fraud-inference-green-s3-read"
  policy = file("${path.module}/policies/credit-fraud-inference-green-s3-read.json")
}

resource "aws_iam_role_policy_attachment" "inference_attach" {
  role       = aws_iam_role.inference_green_irsa.name
  policy_arn = aws_iam_policy.inference_s3_read.arn
}

resource "aws_iam_role" "promotion_irsa" {
  name = "promotion-irsa-role"

  assume_role_policy = file("${path.module}/policies/promotion-trust-policy.json")
}

resource "aws_iam_policy" "promotion_s3_rw" {
  name   = "promotion-s3-policy"
  policy = file("${path.module}/policies/promotion-s3-policy.json")
}

resource "aws_iam_role_policy_attachment" "promotion_attach" {
  role       = aws_iam_role.promotion_irsa.name
  policy_arn = aws_iam_policy.promotion_s3_rw.arn
}
