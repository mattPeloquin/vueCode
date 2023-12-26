# Vueocity Terraform notes

Each folder here is a Terraform root module that matches 1:1
with each AWS deployment account.

mpFramework/deploy/terraform modules do the majority of the work.
Specific Vueocity profiles, config, and authentication is handled here.
Terragrunt is added to support DRY code outside of modules.

Profiles are currently used to manage IAM privileges.
FUTURE - switch to assigning ARN roles with Terragrunt

To run Terraform change to folder for the given account and execute commands using Terragrunt:

    cd vueocity/deploy/terraform/vuedev
    terragrunt init
    terragrunt plan
    terragrunt apply
    terragrunt destroy
