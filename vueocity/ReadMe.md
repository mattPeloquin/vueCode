
Vueocity SaaS
Copyright 2021 Vueocity LLC

This folder contains proprietary software for Vueocity's SaaS offering built on Vueocity's Mesa Platform Framework (MPF).

See [docs](docs/) for Vueocity internal overviews on:
 - [Architecture](docs/Architecture.md)
 - [AWS Setup](docs/AwsSetup.md)
 - [Dev Setup](docs/DevSetup.md)
 - [Coding](docs/Coding.md)
 - [Testing](docs/Testing.md)


Vueocity SaaS code is based on MPF mpframework and mpextend service groups, with the following extensions:

    deploy
        Vueocity-specific Terraform code
    foundation
        *ops - General vueocity-specific extensions
    frontend
        *portal - Includes layout, theme, and style templates
        onboard - Code for onboarding tenants
    static
        Static extensions specific to Vueocity
    templates
        Template extensions and the VueWeb marketing site
    testing
        Vueocity-specifc tests and fixtures
