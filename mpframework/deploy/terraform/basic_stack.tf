#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Example of how to compose MPF modules into a simple dev stack.
#   You would normally build out several stacks with the modules. For example.
#   Vueocity uses these modules with terragrunt to compose stacks
#   for dev, test, and production.
#

terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "~> 3.2"
            }
        }
    }

provider "aws" {
    region  = var.region
    # If an AWS CLI profile is setup:
    profile = "TBD"
    # Or use AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment vars
    # Or directly include IAM credentials or other prferred mechanism
    #access_key = "my-access-key"
    #secret_key = "my-secret-key"
    }

module "network" {
    source = "./network"
    }

module "files" {
    source = "./files"
    }

module "databases" {
    source = "./databases"
    }

module "other" {
    source = "./other"
    }

module "processing" {
    source = "./processing"
    ami = "YOUR_AWMI"
    profiles = ["dev"]
    }
