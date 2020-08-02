provider "aws" {
  region  = var.region
  shared_credentials_file = "/Users/carcaret/IdeaProjects/tl-icalendar/.aws/credentials"
}

terraform {
  required_version = ">= 0.12.0"

  backend "s3" {
    bucket  = "carcaret-terraform-state"
    key     = "tl-icalendar/terraform.tfstate"
    region  = "eu-central-1"
    shared_credentials_file = "/Users/carcaret/IdeaProjects/tl-icalendar/.aws/credentials"
  }
}
