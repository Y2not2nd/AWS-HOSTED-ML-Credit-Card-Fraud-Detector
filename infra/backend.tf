terraform {
  backend "s3" {
    bucket         = "yas-ml-tf-state"
    key            = "eks/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "yas-ml-tf-locks"
    encrypt        = true
  }
}
