#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Vueocity shell extensions
"""

from mpframework.deploy.fab.v1env import v1env
from mpframework.deploy.fab.utils import *


def vueocity_update_code( c, **kwargs ):
    """
    Vueocity update code from hg
    FUTURE - Remove code pull from deploy, either copy from location
    or use fully baked containers.
    """

    # Force the pull (to force branches)
    force = '-f' if kwargs.get('force') else ''
    host = 'vue.xp-dev.com'
    repo = 'hg/VueMono1'
    username = 'vueocity'
    pwd = 'ebn32i5o7y2'
    runcmd( c, [ 'hg pull {} https://{}:{}@{}/{}'.format(
                force, username, pwd, host, repo ) ] )

    # Get revision from argument, TARGET's environment setting, or profile name
    # If not specified use tip for debug profiles, release for all others
    rev = kwargs.get('rev')
    if not rev:
        rev = env_value( c, 'MP_CODE_REV' )
        if not rev:
            rev = v1env.profile
    if rev:
        output = runcmd( c, [ 'hg log -r "\'{}\'"'.format( rev ) ], warn=True )
        if not output or output.stdout.startswith('abort'):
            rev = 'default' if 'mpd' in rev else 'release'
    else:
        rev = 'default'

    runcmd( c, [ 'hg update --clean "\'{}\'"'.format( rev ) ] )

    # Make sure shell scripts have execute set, windows checkins can mess up
    runcmd( c, [ 'chmod -R ug+x /home/ec2-user/mpframework/deploy/shell' ],
            sudo=True )

def vueocity_update_server( c, full ):
    """
    Vueocity specific Updates outside pip (Linux, nginx, etc.)
    """
    if full:

        # Install latest agent and start AWS monitoring with latest config
        runcmd( c, [ 'mkdir aws ; cd aws ;',
                'wget -c https://s3.amazonaws.com/amazoncloudwatch-agent/linux/amd64/'
                    'latest/AmazonCloudWatchAgent.zip ;',
                'unzip -o AmazonCloudWatchAgent.zip -d cloudwatch',
                ], warn=True )
        runcmd( c, [ 'cd aws/cloudwatch ;',
                './install.sh ;',
                '/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl',
                    '-a fetch-config -m ec2 -s',
                    '-c file:/home/ec2-user/vueocity/deploy/aws/cloudwatch/agent_config.json',
                ], sudo=True, warn=True )

        # Papertrail setup for TLS key
        runcmd( c, [
                'wget -c -O /etc/papertrail-bundle.pem',
                    'https://papertrailapp.com/tools/papertrail-bundle.pem',
                ], sudo=True, warn=True )

        # Dev items
        if not prod_profile( c ) or mpd_profile( c ):
            # Redis CLI
            runcmd( c, [ 'wget http://download.redis.io/redis-stable.tar.gz ;',
                    'tar xvzf redis-stable.tar.gz ;'
                    'rm redis-stable.tar.gz ;',
                    'mv redis-stable redis ; cd redis ;'
                    'make',
                    ], warn=True )

def vueocity_update_pip( c ):
    """
    Add Vueocity specific pip items
    """

    # Dev install requirements
    if not prod_profile( c ) or mpd_profile( c ):
        runcmd( c, [ 'pip install --upgrade -r',
                home_folder( 'vueocity', 'deploy', 'pip_dev.txt' ) ] )
