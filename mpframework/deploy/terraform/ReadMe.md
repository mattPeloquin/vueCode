# MPF Terraform setup

Modules for configuring MPF stack on AWS.

These modules are intended for composition by root platform Terraform configuration
that defines profiles and manages backend state.

basic_stack.tf is an example root module that sets up a simple stack.

Account and IAM structure is declared in the aws provider in the root module, which Terraform then makes available to downstream modules. IAM credentials must be setup manually and configured for the root module.
