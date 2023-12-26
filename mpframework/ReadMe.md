# Vueocity Mesa Platform Framework (MPF)

Scalable, configurable, extensible multitenant content platform.

This folder contains the MPF base layer, which provides a subset of Vueocity functionality for secure contant platforms. Vueocity's SaaS platform extends this code.

## Code overview

MPF separates concerns into service groups that encapsulate Django apps and front-end code.

Service groups are currently packaged as a well-seamed monolith, combining a monolith's lower overhead with microservice separation. Service groups share a database and are deployed together, but have clean boundaries for future separation into stand-alone microservices:

    - Interaction across service group boundaries is through APIs or message queues.
    - Within service groups apps may interact with function calls, signals, and model DB joins.

MPF code is also organized with 3 licensing levels:

    A) mpframework - MPF core, open source
    B) mpextend - MPF extensions, may be licensed
    C) "root platform" - Vueocity SaaS or private instances

Each of these is a monorepo with all service group and shared code. "root platform" includes hosting configurations and any custom extensions or additions.

### Code Map

Each monorepo is organized around Django apps inside service group folders. Service groups and apps for mpframework are shown below:

    content
        mpcontent       App for MPF protected content types
    foundation
        ops             Shared code/tools packaged in app
        tenant          Multitenant framework
    frontend
        sitebuilder     Site customization framework
        portal          Present content in single page JS web portal
    user
        mpuser          Extensions of Django user

Each Django app folder contains backend and frontend code as below:

    admin        Staff admin pages
    api          Views specific to web service API endpoints
    bots         Self-perpetuating task bots
    models       Django models (ORM and core business logic)
    static       Browser JS code specific to app
    templates    Templates specific to app
    tests        Model and view unit-tests
    utils        Supporting code chared across the app
    views        Views for non-admin web pages

Other top-level folders hold shared code not specific to Django apps:

    common       Django extensions and backend code shared across apps
    deploy       Build, IaC and devops
    settings     Config options in yaml profiles, Django URLs
    static       Front-end code and resources shared across apps
    templates    Django templates common across apps
    testing      Testing frameworks, fixtures, and E2E tests

## Vueocity Setup

MPF is a Python web stack designed to scale across Linux servers or containers. It uses AWS services for DB, storage, caching, message queue, etc.

### Local stack

To run locally on Windows, Linux, or macOS without AWS services see deploy\ReadMe.md

### AWS stack

See Terraform code under deploy\terraform

# License

Copyright (c) 2021 Vueocity, LLC
mframework code is released under the MIT License.

mpframework uses commercial services, open source packages, and open source code with MIT-compatible licensing. Dependencies are identified using the following conventions:

     a) Service, binary, and build-only dependencies are not identified explicitly, but are implied by use (e.g., AWS, Linux, Django). These items are not in mpframework revision control.

     b) Code built with mpframework is included in revision control in well marked locations and retains license notices.

     c) Code derived from open source has license notices.
