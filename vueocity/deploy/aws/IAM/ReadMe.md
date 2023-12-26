
# CLI and Terraform access

Local dev machines should be configured to run AWS CLI tools with IAM profiles based on roles:

    1) Obtain AWS credentials for one or more roles

    2) Copy "config" and "credentials" file to ".aws" folder under user root
        Linux: ~/.aws
        Windows: C:\Users\_username_\.aws)

    3) Update the key/secret in "credentials" and any roles in "config"

        The "credentials" file holds secret key that allows for an AWS connection, so care needs to be taken to limit privleges on what the key can do, and to protect the "credentials" file.

    4) Then pass role name by:

            --profile option on aws command

            setting AWS_PROFILE environment variable to the profile.

    5) Terraform uses the profiles in "config", which are referenced in the aws provider block.
