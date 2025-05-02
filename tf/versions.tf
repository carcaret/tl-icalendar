terraform {
  required_providers {
    archive = {
      source = "hashicorp/archive"
    }
    aws = {
      source = "hashicorp/aws"
      shared_credentials_file = "/Users/carcaret/IdeaProjects/tl-icalendar/.aws/credentials"
    }
  }

  backend "s3" {
    bucket  = "carcaret-terraform-state"
    key     = "tl-icalendar/terraform.tfstate"
    region  = "eu-central-1"
    shared_credentials_file = "/Users/carcaret/IdeaProjects/tl-icalendar/.aws/credentials"
  }

  required_version = ">= 0.13"
}

provider "aws" {
  region                  = "eu-central-1"
}