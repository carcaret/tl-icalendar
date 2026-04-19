terraform {
  required_providers {
    archive = {
      source = "hashicorp/archive"
    }
    aws = {
      source = "hashicorp/aws"
    }
  }

  backend "s3" {
    bucket  = "carcaret-terraform-state"
    key     = "tl-icalendar/terraform.tfstate"
    region  = "eu-central-1"
  }

  required_version = ">= 1.11.4"
}

provider "aws" {
  region                  = "eu-central-1"
}