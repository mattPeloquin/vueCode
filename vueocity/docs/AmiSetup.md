# Vueocity AMI Setup

Notes for configuring Amazon Machine Images (AMIs) for MPF instances.

When the machine comes up it will expect AWS infrastructure in place as defined in its active MPF profile. See Terraform IaC for AWS infrastructure.

 - FUTURE -- Switch to containers and Graviton ARM

## Create and update MPF AMI

Create a clean AMI for MPF stack running NGNIX and uWSGI for prod, test, or dev:

0) Use vueop account to create AMI, and GIVE PERMISSIONS to other accounts.

    This only happens a few times a year, so doing manually in console (adding account numbers to AMI permissions in vueop account).

1) Create and update new instance that will serve as AMI snapshot

    1a) Setup instance

        Create Amazon Linux 2 HVM 64bit x86 instance.
            (last AL2 AMI# was ami-0721c9af7b9b75114)

        IAM, security group, key, can be changed later when launching
        instances from the AMI.
        STORAGE can only be made LARGER when launching from AMI,
        so set to 8GB (min AWS value).

        Use EC2 management console to launch instance.
        Set Security Group and IP so you can connect via ssh.
        Setup ".secrets/vueocity/vueops.pem" with keypair,
        On Windows update security on file to be only for the current
        user and marked read-only and hidden; Linux: chmod 400

    1b) Setup mercurial

        sudo yum -y install mercurial
        hg init

2) Update new instance REMOTELY using fab from dev workstation

    Get code and config on server with fabric commands from local machine.

    NOTE - Local machines must MATCH PLATFORMS for remote machines they call.
    In the typical case, local machine will default to "mpframework mpextend vueocity"
    platforms, which will then be reflected in defaults on server after code installed,
    since the default is to read platforms from sub folders.

    2a) Fill repository and update code

        fab -H _ip_ k vueops.pem  update-code

    2b) Setup default environment

        Set default root folder and profile the AMI will default to, which
        is the only env variable required to run setup scripts.
        Other setenv variables can be set here, but they are generally
        better set in cloud-init scripts or manually after launch.

            fab -H _ip_ k vueops.pem  server-setenv --home=/home/ec2-user

    2c) Setup server environment

        Install of latest server components that are outside pip, create
        new Python venv, and run first pip update:

        fab -H _ip_ k vueops.pem  install-server
        fab -H _ip_ k vueops.pem  update-server --full
        fab -H _ip_ k vueops.pem  update-pip

    Restart console to activate venv; fab calls can now be run directly on server.

3) Create the AMI

        Use console to create AMI image from the instance, which is in the vueops account.

        Use console to add permissions to the AMI for all accounts that need it.

        This AMI is ready to participate in EXISTING Autoscale groups.
        Profile and other config will be setup in the launch config bootstrap.

4) Updating an AMI to create specializations

        If CHANGING the profile or other env info the AMI was created with, run below
        either remotely or locally:

            fab update-code
            fab server-setenv --profile=_profile_

        Normally only need the items below:

            fab update-code
            fab update-server
            fab update-pip
            fab clean

## Launching MPF Servers

Normally create ONE AMI image as a production instance. This will ALSO be used for dev and test work; it is the same image, the profile just needs to be adjusted with server-setenv.

Bootstrapping:

    For Dev machines, although they can be set to bootstrap on creation, this is not normally baked into the AMI, so MPF needs to be started.

    For machines running in ASG, the cloud-int user data is set to run
    a bootstrap script as part of creation.

    Logs for cloud bootstrap are in:

    	/var/log/cloud-init.log
    	/var/log/cloud-init-output.log

Autoscale Cluster:

	For new autoscale clusters, DB, S3, etc. need to be set up the first time.

Prod mpd/dev/debug server:

    prod-mpd dev servers attach to same AWS resources as prod servers.
    These are configured through ELB target groups and launch templates in
    the same manner as production autoscale clusters.
    The well-known name prodmpd is used in DNS to point to prod-mpd ELB
    target and is also used for hack to set profile to prod-mpd

    To refresh the prod-mpd cluster with current tip:

        fab -H prodmpd.vueocity.com refresh -q

Stand-alone dev Server:

    If other server targets are not configured from the launch bootstrap,
    use the following to complete bootstrap:

        fab -H _ip_ server-setenv --provfile=dev --rev=tip
        fab -H _ip_ refresh -f

    Setup AWS resources to fit dev profile

## Build/Test Server with virtual desktop

1) Create 64-bit Ubuntu instance

    Log in via SSH with key pair, user is "ubuntu"

2) Get environment up and running

sudo apt-get -y update
sudo apt-get -y install ubuntu-desktop
sudo apt-get -y install vnc4server

## Cloud-init notes

The cloud-init system takes "user data" of various formats to handle system startup. Cloud-init is part of Ubuntu, but also included in Amazon Linux.

    The file is:   /var/lib/cloud/data/user-data.txt
    Logging is in: /var/log/cloud-init.log

To make the cloud-init user script occur on every reboot, need to update

    /etc/init.d/cloud-init-user-scripts  to change "once-per-instance" to "always":

This could also work in Linux startup file:  /etc/rc.local
but get better logging and more flexibility by putting it in user data.
