resource "aws_ecr_repository" "inference" {
  name = var.ecr_repo_name

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Project = "YAS-ML"
    Service = "Inference"
  }
}
 