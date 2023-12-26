#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Setup variables and state shared across all Vueoicty root modules
#

# Global constants used across all vueocity erragrunt and terraform files
locals {

    region = "us-west-2"

    }

# Create .tf variable declarations for module input variables
# setup in locals (above) or the main.tfvars file (see next section below)
generate "variables" {
    path      = "variables.terragrunt.tf"
    if_exists = "overwrite_terragrunt"
    contents  = <<EOF
      variable "region" {}
      variable "ami" {}
      variable "profiles" {}
    EOF
    }

# Load shared variables (from locals or main.tfvars) with each terraform command
terraform {
    extra_arguments "conditional_vars" {
        commands = [ "init",
            "plan", "apply", "destroy",
            "import", "push", "refresh",
            ]

        # Pass along any local values in this file to terraform
        # Note the prefix is necessary for Terraform to place in 'var'
        # Wasn't really a better way to do this at the moment
        env_vars = {
            TF_VAR_region = local.region
            }

        # Setup custom variable file loading
        # Not a fan of Terraform's unobvious loading of environment variables
        # and tfvars files, so using explicit conventions here.
        required_var_files = [
            "main.tfvars",
            ]
        # If needed can also read .tfvars files from parent folders if
        # they are not needed in this file
        optional_var_files = [
            ]
        }
    }

# Backend remote state bucket shared across accounts
remote_state {
    backend = "s3"
    generate = {
        # Terraform looks for a file starting with "backend."
        path      = "backend.terragrunt.tf"
        if_exists = "overwrite_terragrunt"
        }
    config = {
        region         = local.region
        profile        = "vueops"
        bucket         = "vueocity-terraform"
        key            = "${ path_relative_to_include() }/terraform.tfstate"
        dynamodb_table = "vueocity-terraform"
        }
    }

# Provider required versions
generate "versions" {
    path      = "versions.terragrunt.tf"
    if_exists = "overwrite_terragrunt"
    contents  = <<EOF
      terraform {
        required_providers {
          aws = {
            source  = "hashicorp/aws"
            version = "~> 3.2"
            }
          }
        }
    EOF
    }
