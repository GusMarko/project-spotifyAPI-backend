data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "mg-terraform-state-storage"
    key = "${var.key_path_networking_state}"
    region = "${var.aws_region}"
  }
}