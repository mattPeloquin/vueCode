#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Tests for vuecam account
#

provider "aws" {
    profile = "vuecam"
    region  = var.region
    }

/*
    Comment out modules to test subsets
*/

module "network" {
    source = "../../../../mpframework/deploy/terraform/network"
    }

module "files" {
    source = "../../../../mpframework/deploy/terraform/files"
    }

module "databases" {
    source = "../../../../mpframework/deploy/terraform/databases"
    }

module "other" {
    source = "../../../../mpframework/deploy/terraform/other"
    }

module "processing" {
    source = "../../../../mpframework/deploy/terraform/processing"
    ami = var.ami
    profiles = var.profiles
    }
