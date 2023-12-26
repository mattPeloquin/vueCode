#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    AWS Autoscale fabric tasks

    This approach can only scale so far, will be replaced with container
    orchestration when needed.
"""

from mpframework.common.deploy.paths import autoscale_ip_file_path
from mpframework.deploy.fab.v1env import v1env
from mpframework.deploy.fab.env import pl
from mpframework.deploy.fab.env import p
from mpframework.deploy.fab.env import set_env
from mpframework.deploy.fab.utils import rundj
from mpframework.deploy.fab.decorators import mptask


@mptask( skip_setup=True, local_only=True, reset=True )
def a( c, profile, tag='' ):
    """
    Run for ASG: fab a profile cmd1 cmd2

    Runs commands against dynamic IPs of a given configuration's autoscale instances.
    There is a race condition between getting the IPs and running commands;
    since commands are idempotent and new autoscale instances will run their
    own updates, it is fine for the things this command will be used for.
    """
    c.run('echo ====== Autoscale for {} ======'.format(profile))
    p( c, profile )
    set_env( MP_PROFILE_TAG=str(tag) )
    set_env( MP_AWS_REMOTE_ONLY='True' )
    v1env.hosts = _get_hosts( c, v1env.profile, tag )

def _get_hosts( c, profile, tag ):
    """
    HACK - run DJ command to write IPs for this cluster to file, and then
    read those IPs from the file (easiest way to pass the info)
    """
    hosts = []
    try:
        rundj( c, 'aws_autoscale --ips', *_add_commands( tag ) )

        ip_file = autoscale_ip_file_path( profile, tag )
        print( "Getting IPs from: %s " % ip_file )
        with open( ip_file ) as ip_file:
            ips = eval( ip_file.read() )
            hosts = [ ip for ip in ips if ip ]
        print( "IPs: %s " % hosts )

    except Exception as e:
        raise Exception("Error getting ip values: %s" % e)
    return hosts

def _add_commands( tag='' ):
    rv = ()
    if tag:
        rv += ( ' --tag %s' % tag ,)
    return rv
