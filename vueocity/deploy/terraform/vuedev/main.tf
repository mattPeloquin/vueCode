#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Deploy Vueocity dev stack
#

provider "aws" {
    profile = "vuedev"
    region  = var.region
    }

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
