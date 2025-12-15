resource "kubernetes_service_account" "airflow_worker" {
  metadata {
    name      = "airflow-worker"
    namespace = "airflow"

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.airflow_worker_irsa.arn
    }
  }
}

resource "kubernetes_service_account" "mlflow" {
  metadata {
    name      = "mlflow"
    namespace = "mlflow"

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.mlflow_irsa.arn
    }
  }
}

resource "kubernetes_service_account" "inference_green" {
  metadata {
    name      = "credit-fraud-inference-green-sa"
    namespace = "ml-inference"

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.inference_green_irsa.arn
    }
  }
}

resource "kubernetes_service_account" "promotion" {
  metadata {
    name      = "model-promotion-sa"
    namespace = "ml-inference"

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.promotion_irsa.arn
    }
  }
}
