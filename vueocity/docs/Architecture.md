
MPF Architecture
================

MPF architecture and design knowledge is captured in:

 - Code comments
 - Self-evident design from code
 - [Overview]( TBD \Overview.md), this file, ReadMe files
 - Tribal knowledge

## Architecture Goals

    1) Industrial SaaS -- secure, scalable, responsive UX, robust, available
    2) Cost effective -- parsimonious cloud use, small code size, automated devops
    3) Flexible design/code -- configurable, extensible, easily refactored, licensable

## Technology

 - AWS cloud services (some abstraction, but no plan to port elsewhere)
        Prefer cloud service vs. packages on a server
        Assume 1 region, Cloudfront for global, until more multi-region available
 - Backend uses EC2 servers with ELB auto-scale and SQS tasks
        Python 3 and Django ecosystem for web services APIs and some web screens
        Will migrate from CPython to PyPy when needed
        Will move to containers when needed
 - HTML5/JS UI for all mouse/touch desktop/device platforms (no native mobile)
        Main user portal is single page app that inflates views from data
        Other screens per-request hybrids; many staff screens use Django admin

## Guiding Principals

 - Well-seamed monolith with apps and "service groups" (see below)
 - Partitionable multitennant with global reach as provided by cloud services
 - Multi-layered security in ops, design, and code
 - Limit processing in requests, move work to async queued tasks
 - High-leverage automated testing (custom data-driven unit, e2e, and load frameworks)
 - Hybrid API front-end portal separate from server-driven admin pages
 - Automated, flexible dev/test/prod deploy; easy move to full IaC and CI/CD
 - Custom infrastructure (e.g., caching, config) maximizes reuse and efficiency
 - Code may be licensed in all or part, for separate operations or extension
 - Internationalization for user content now, possibly platform later
 - MVP and speed to market create technical debt - acknowledge, document, manage
 - Minimize
    costs -- operation and scaling (both cloud and human)
    effort -- development, testing, deployment, operations, AND support
    code size -- cloud services, open source, DRY, scrub requirements, refactor constantly
 - Self-Healing or at least graceful failure to data errors
 - Logging ensures visibility and that bad events are known
 - Telemetry focused on AWS metrics and app features; add custom as needed

### Layering

Most processing in Django server code for middle-tier scalability:

    1) Database and Persistence
        S3 stores all uploaded files
        SQL DB (Aurora mySQL) with Django ORM
        DyanmoDB for higher-volume user event tracking

    2) Application Server
        Run Django on uwsgi behind nginx
        Specialized caching with timeout and invalidation (no simple table, page, etc. caching)
        One server role for all needs; if need to scale, can break out admin, tasks, etc.

    3) Web Server
        nginx proxy for application server; limited nginx micro-caching of some requests
        Cloudfront to S3 for static content, Cloudfront to nginx origin for some content
            nginx can serve directly as security option, but limits global support
        Store uploaded content on S3 after upload to local nginx server
        Run on app server for time being, but can split tiers if needed

    4) ELB
        Load balancing, SSL termination, and management of servers with Target Groups
        Most processing is non-sticky sessions
        Short-term sticky sessions are config option to optimize per-server caching

    5) Browser
        Main Portal is a MVVM one-page app using Backbone/Knockout
        Other areas Django per-page reload
        RESTish APIs in all areas as needed

### Service Groups

Django apps are used as granular modules for specific domain responsibilities. These apps are further organized into service groups via design guidelines and conventions. The goal is service groups could be quickly converted to stand-alone services.

Between service groups, code should only communicate with formal API layers or via asynchoronus tasks. For backend makes these as direct calls, but could be converted to web service calls.

Within service groups, apps should be designed to limit interaction with other apps, but may import and call directly.

Django signals should only be used within service groups, and only to support extensions of code beyond MPF (e.g., mpExtend) within a group. Otherwise prefer direct calls.

Coupling to watch out for:
 - DB  - open question if full DB isolation worth it
 - Context processors
 - Template dependencies
 - Assumptions when passing request object


### Caching

Caching is multi-layered and focuses on optimizing reading of expensive data-driven configuration.

As described in the overview, caching optimizations are added from the browser down to per-request memoization.

There are three broad categories of caching:

Web - Caching of HTTP request responses generated by MPF, which use CacheControl and default settings, includes:
    Nginx
    CloudFront
    Browser

MPF Shared - MPF use of Redis for distributed value. Much of this leverages the multi-tier invalidation system that includes support for time window differences, including:
    Finalized data (particularly bootstrap JSON, with timewin deltas)
    Partial calcs and various expensive values
    Full Django models (user and sandbox objects)
    Loaded template files
    Rendered template fragments

MPF Localized
    Per-server buffering of shared cache calls
    Per-process buffering of configuration information
    Per-request stashing/memoization of values

### Scaling

Main scaling concern is load from increasing active users. Content and other items are more bounded, but may have UI risks.

AWS, auto-scale servers, caching, vertical DB scaling


### Database

Store metadata in relational DB using Django ORM:

 - Minimize SQL DB processing; heavy caching, no custom SQL code, simple model relationships,
   push processing into Python code for simplicity and scalability
 - Use read replica when possible. Put off partitioning/sharding to keep operations
   and coding simple -- design models to support partitioning if needed.
 - Define schema based on Admin/performance needs; use blob/yaml data for many details
 - Many area will need to support retiring vs. deleted.
 - Use no-sql for high-volume areas such as user-generated events or any other
   data that may be useful for time series analysis.
 - Optimize bulk access of data where needed (Django .values() instead of creating models)

Using separate SQL DBs for app service groupings is a future possibility. Would have the benefit of enforcing modular data interfaces between apps and provide for partitioning DB load. However, extra complexity (relationships across DBs, aggregation) was not considered worth it while the database schema is evolving. It should be kept in mind as a secondary consideration during app design.

## Portal Transformation

When content data is collected and sent from Django models to the Portal it is blended with user data. Thus although JS Portal models look similar to Python Django models, they represent specific instances of content for that user.


## Settings, Profiles and Playpens

Profiles bring together a group of configuration settings, stored in yaml config files.
Profile Types group profiles together (via yaml config file naming conventions) and add a small amount of specialized behavior. There are two profile types:
●       dev – Used for development and most testing
●       prod – Used for production and production-related testing
The difference between dev and prod execution is in configurations data, particularly adding more security rigor in prod. There is VERY LITTLE code that changes behavior based on profile type (the main code difference is prod has checks to ensure development tools can’t accidentally disrupt a production environment).
Profile Sandboxes create an environment for system instance. These are defined by profile settings that control use of resources; in particular whether the sandbox is shared by a server cluster or is for one server so can use the server IP address to designate itself (i.e., IP number is added to S3 folder names, DB names, memcache keys, etc.). This allows for easy development and testing of functionality in individual sandboxes.
prod servers that are part of the same profile always share a set of AWS resources. Different prod profiles can share resources (e.g., the debug production server accesses the same DB as the main production servers).
One set of dev AWS resources is manually set up and maintained for all dev instances. prod AWS resources may be set up manually or dynamically created. This approach strikes a balance between easy/low-cost dev environment support and robust, highly automated production/test support.
Django and Environment Settings
Django has a built-in framework for defining immutable settings at server startup – changing these settings requires a server restart. Some settings modify Django and third-party modules, while many others feature tuning and configuration. The complete set of settings can be seen on the debug page.


## Delivering file/stream bytes

Normally all files are delivered via CDN:

 - The majority of files will come from public and protected Cloudfront distributions

 - Static JS/CSS from Google, MaxCDN, and Cloudflare may be loaded directly. Other CDNs are not used due to rare issues with them being blocked by corporate firewalls.

 - Some special cases may deliver files through Nginx app servers.

## Logging vs. Events vs. Telemetry

Logging text strings are read by a human to determine what is happening in the system. These are used extensively, particularly in debug.

Events are MPF-defined actions that support configurable response (e.g., sending email).

Telemetry is MPF-defined data emitted for analysis (for AWS CloudWatch).

## Other Notes

As needed, evolve platform incrementally into more explicit services model, using different technologies if they fit better.

The currently plan is to migrate the portal JS application to Vue.js and incorporate webpack.

Django was picked for ORM, web app, and data admin strengths. It has a number of constraints related to its roots as a news-site tool, which may prove an issue longer-term. Other platforms considered:

    Ruby / Rails
    Scala / Play
    Python / web2py
    Python / Pyramid (Pylons)
    Java and .NET approaches would require more code/complexity:
     - Java has tons of web framework ecosystems
     - .NET is essentially a single well-defined and robustly supported ecosystem
    PHP -- lots of possible frameworks
