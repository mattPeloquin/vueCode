
Vueocity AWS Setup Notes
========================

Most AWS RESOURCE configuration is encoded in Terraform scripts.
Multiple accounts are used with IAM roles, which are setup manually.

# Accounts and IAM

Vueocity is setup using AWS organizations:

    vueorg - root org, only root users
    vueusers - Holds IAM users, groups, and policies for assuming roles
    vueback - Used for backups, has its own special user

    vueops - Tool state shared across accounts, SSH entry
    vueprod - Production environment
    vuedev, vuetest, vuexxx - dev sandboxes

The accounts in the second group have NO users or root account access, all access is through IAM roles assumed by IAM users in the vueusers account.

The root account is not used other than to do initial IAM setup and to do any root-only actions like disabling delete. It has a OrgAdmin group that has access to all accounts, but should only be used for root admin issues.

The roles users/APIs can assume are below. The vueusers account defines IAM groups with the same names as the roles. vueusers has STS policies that map each IAM group onto IAM roles. The roles must be created in each target account and the permissions for that role on that account defined. STS polices for each role in vueusers must include the account number for the target. Then users are added to vueusers account, and can take on roles depending on the IAM groups they belong to.

    VueAdmin - Full admin access for most accounts
    VueProd - Necessary permissions for deployment
    VueDev - Full admin on dev accounts, read-only on production
    VueRead - Read-only for all accounts where made available

    VueOrg - Role managed by the vueorg root account, used to setup vueusers and any issues in accounts that VueAdmin doesn't have rights to.

Access notes:

    Human IAM users use passwords to log into AWS
    FUTURE - use keys?

    Non-human accounts and groups are setup for access into resources via APIs.

    Role assigned to EC2 servers give the server policy rights to access AWS resources.
    FUTURE SECURE - a broad role is used for servers now, can tighten later

    MPF assumes 1 AWS access key will be used for all access to services.
    FUTURE SECURE - use more granularity in IAM access

    Signing certificates can be used to encrypt calls to AWS APIs, but all MPF calls occur within AWS virtual network, so not used.

To use 'fab a' a local machine must have an aws.yaml file in the .secrets folder.
TBD NOW SECURE - dependency on local aws.yaml file will be removed.

EC2 key pairs control SSH access to individual servers, for manual shells and MPF fabric commands.

    EC2 machines use AWS's document lookup for keypair info when using Boto to access AWS services.

    Key pairs are managed in EC2 control panel. Each server has one
    keypair. Private key must be available in:

        .secrets/vueocity/*keyname*.pem

# VPC / Regions / AZ

The MPF stack is not currently cross-region. Be careful to select the region you want when creating resources as most are per-region.

CloudFront is used for global content distribution, and requires a certificate to be added to the global US-East region (see below).

All AWS resources except CF and S3 are inside VPC.
External visibility is controlled by holes in firewall (Security Groups):
    ELB is visible publicly on 80 and 443
    EC2 instances open 22 for SSL from specific IPs

All of those resources should be configured to use multi-AZ (e.g., using clustered endpoints for RDS and Elasticache, not assuming anything about AZ with EC2 server setup, making sure permissions are configured).

FUTURE - Move EC2 instances into private VPC, using ELB in public VPC to connect to internet and NAT in private VPC to allow outgoing.

# Keys and SSL certificates

Production verified SSL certificates are used with:

  1) ELB for HTTPS support  (use ACM in region)
  2) Cloudfront for SNI aliases  (use ACM in Northeast)

Private keys are used with

  1) Cloudfront for signed URLs  (stored in AWS Secrets and Root)
  2) Access to EC2 servers  (stored in .secrets folder)


# Network Security Groups

AWS service calls will fail silently and are a pain to debug when
security groups are not set up correctly.

    Prod server security groups need incoming rules for:

        80    -- From ELB (which terminates SSL), main traffic path
        22    -- from DevOps IPs that can deploy

    RDS and Elasticache need:
        3306  -- from servers, for RDS
        6379  -- from servers, for Elasticache redis

    Other possibilities for dev/test:
        80    -- 54.224.0.0/11  (optional, for any Route53 healthcheck pings)
        443   -- ELB  (optional, if SSL is passed through)
        8000+ -- For any local dev serving

# EC2

See AmiSetup.txt for details on creating new AMIs.

EC2 servers handle all endpoint requests (behind ELBs) and do task processing. The same code is deployed on all servers. MPF profiles can define different roles, and ELB target groups are often used to direct certain traffic to certain groups.

There are many ways to launch EC2 servers that have evolved over time; MPF uses Launch Templates to define AMI, settings, and the cloud-init startup script in User Data.

All servers are run from autoscale groups. This allows for autoscaling, scheduling, easy management and updates of groups, assigning servers to ELB target groups and mixing normal/spot servers.

Groups of servers will be matched against ELB target groups and separated by profile, to allow separation of processing and code rev (e.g., FOH, BOH, FT).
Dev servers use the same launch templates, but are created manually as needed amd configured after launch.

    1) Create Launch template with key, security, monitoring. ASG and spot may have incompatible options, so make sure on-demand and spot instances can be created from the launch template.

        When setting up Launch Templates, use ARN/IDs for IAM and Security Groups, or errors will happen with different autoscale configs.

    2) Create ASG from Launch Template, which can be done from console (see below for cli updates)

# RDS

Using mySql running on Amazon RDS, either instances or Serverless.

    fab db-shell from an SSH session to AWS machine used to manage DB directly

DBs should be created with MPF db_migrate or db_sync command
if they don't already exist.

RDS instances must BELONG TO SAME SECURITY GROUP as servers that use them,
with port open for communication

    Using InnoDB backend (vs. MyISAM)
    Use DB Parameter Groups in the AWS console to make ini settings.

For Serverless, set the following manually:

 - Set Force scaling to on which will ensure an unintended long-running query can't prevent scale out.
 - Currently scale out is at 70% CPU, 90% connections - can't modify max_connections, which is set to 90 for 1 unit.

For RDS instances:

 - Can boost max_connections to better match the max number of uWSGI processes


For instances, start with 5 GB allocation since once storage is increased on an instance it cannot reduced. Increase allocation with command line:

 > rds-modify-db-instance acme --allocated-storage=20 --apply-immediately

# ELB

Create application load balancers with target groups manually. One or more ELBs may be used with Autoscale groups for targets. Adding/removing servers from target groups is scripted as part of Autoscale groups.
 - 80 and 443 open, both passing to 80, so SSL is terminated at ELB
 - Load certificates into 443 listener (ACM easiest)
 - Any aliasing of HTTPS CNAMEs is handled by external service, so only the root certificate is terminated at ELB listener
 - Create target groups to handle BOH, FOH, FT traffic
 - Stickiness may be used to leverage server local caching

# Elasticache

Create instances manually.
Like RDS, Elasticache needs to belong to SecurityGroup that servers can talk to
Will use Redis for everything

# S3

MPF uses a protected, public, and public-protected S3 bucket. Buckets have no public access.Uploads occur to buckets from EC2 and browser. Access is mainly through CloudFront, with some paths for MPF stack on EC2.

 - Cloudfront via OAI
 - VPC Endpoint for S3 (which makes it not visible to public IPs)
 - CORS access for direct upload

Accelerated transfer is used, primarily to support direct uploads, as
almost all download will be to Cloudfront.

Buckets are always versioned, with a policy to transition old versions into lower cost storage and eventually permanently delete them.

TBD - Create cross-account bucket backup
TBD - Enable MFA delete

S3 buckets must be created manually, while policy setup is scripted.

# CloudFront

Distributions are setup for public and protected endpoints. They use origins and behaviors tied S3 buckets and no-host ELB endpoints. Protected files use signed URLs.

A non-cached public endpoint can be used with prod-mpd dev servers for loading JS files that are not compressed/versioned.

FUTURE - Protected-public is for special compatibility mode where files are copied to S3

Default cloudfront URLs are supplanted with friendly URLs via SNI. This can cause problems in some office networks that don't support SNI, so MPF compatibility settings may switch to use default URLs.

CF is used for the error page of last resort; if requests cannot be served, they are redirected to CF distribution, which won't know what to do with the URL, so will display
a custom error page imply a temporary outage, it can be used both as a "down for maintenance" page, and for a user-friendly (and attack obfuscation) 404 page for bad requests into CF.

	General

		Alternate Domain Names:
          - Add friendly DNS CF name that the R53 name maps to
		  - Add domain names that will redirect for DNS secondary
		Custom SSL: Set to SNI

		SSL Certificate: Load the wildcard certificate to use with distribution
        ACM CERT FOR CF MUST BE REGISTERED IN North Virgina region.

		Logging: Log to separate S3 bucket

	Origins

        For both PUBLIC and PROTECTED distributions:
            - ELB origin for no-host requests
            - Static error file mpf-root origin to PUBLIC S3 _static/mpf-root folder
            - Default origin to corresponding S3 bucket

        S3 buckets locked down to OAI access, so:
    	    RestrictAccess = Yes
            Setup OAI (Origin Access Identity), assign to S3 bucket, and select
            FUTURE - use different OAIs for different behaviors/buckets

	Behaviors

        Both PUBLIC and PROTECTED distributions:
            - /nh/* path for no-host requests, to ELB origin
            - mpf-root path to public S3 for error files
            - Default origin to corresponding Origin

        To support CORS uploads to S3:
            - Add to the allowed and cached HTTP methods:
                OPTIONS
            - Cookies must be whitelisted with:
                access-control-request-headers
                access-control-request-method
                origin

        PROTECTED no-host and S3 downloads need to:
            - Set to HTTPS only
            - Add session_cookie_name to cookies added to cache, e.g.:
                vueocity*session
            - Forward query strings and white list:
                response-content-disposition    # for attachment downloads

	Error Pages
        - For file use mpf-root path in behavior to public S3 origin
        - Return 403 for bad URLS -> map to 404 error
        - Can have Route 53, due to DNS health failover route requests to CF which will generally fail with 404 (unless no-host)

# SES

Emails are sent via SMTP, which SES supports with an IAM user. It is easiest to
use the "Create SMTP Credentials" screen to create a user, and then use that
user's AWS access key and the one-time secret in special SES password form.
Those are placed into AWS secrets and passed to Django as SMTP user/pwd
for all sending.

DON'T CHANGE THE USER NAME, AS IT WILL REMOVE SENDING PRIVILEGES

DON'T USE PORT 25 -- throttling is massive, need to get AWS approval
http://docs.aws.amazon.com/ses/latest/DeveloperGuide/limits.html

To receive emails, SES requires verification of emails from domains for dev case, and a request for production support to send emails anywhere.

To send emails from addresses, SES email must be verified, which is
handled by MPF.

FUTRUE SCALE - THERE IS A 1000 identity limit on emails addresses that can be sent from, so if that doesn't change, a different email sending would be needed
if there are a large number of sanbox admin emails.

Notification of emails delivery/bounce can be setup via AWS GUI in SNS

# Route53

All manual configuration, point main urls at ELBs.

Add various support records for AWS and other vendors.

Use Elastic IPs as convenience for associating dev subdomain names with
specific dev servers.

# AWS Command-Line Interface (CLI)

Amazon has a set of command-line tools for interacting with services. Normally
these are NOT needed for MPF; actions are either scripted in MPF using Boto
or through GUI manually.

However, the CLI provides an alternate way to accomplish some tasks, and
a few tasks can only be done via the CLI

If a task needs to be done often, do not script through CLI, create framework
support through fab commands and/or MPF UI.

See the dev\AwsCli.txt file for for information.
