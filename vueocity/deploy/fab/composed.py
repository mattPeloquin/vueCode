#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Vueocity-specific tasks
"""

from mpframework.deploy.fab.decorators import mptask
from mpframework.deploy.fab.decorators import prod_warn
from mpframework.deploy.fab.composed import refresh

from .autoscale import a
from .djutils import show_full
from .utils import runaws


PROD_PROFILES = [
    ('prod-osk', ''),
    ('prod-boh', ''),
    ('prod-ft', ''),
    ('prod' , 'A')
    ]


@mptask
@prod_warn
def refresh_prod( c, profile='', tag='', iam='', force=False,
        server=False, rev='', quick=False ):
    """
    Refresh all ASG prod servers (ASG or -server)
    Target all by default, but option for one profile.
    Option to do ASG refresh (default) or directly run refresh
    on the servers (with rev and quick options).
    """
    profiles = [(profile, tag)] if profile else PROD_PROFILES
    for profile, tag in profiles:
        print( "REFRESHING %s%s" % ( profile, tag ) )
        try:
            if server:
                # Run local autoscale command to populate v1env with
                # the current profile hosts, then refresh each
                a( c, profile, tag )
                refresh( c, rev=rev, quick=quick )
            else:
                # Run AWS command locally to start refresh
                _start_asg_refresh( c, profile, tag, iam )
        except Exception as e:
            if not force:
                print("ERROR STOPPED REFRESH")
                print( e )
                break

def _start_asg_refresh( c, profile, tag, iam ):
    """
    Run AWS CLI locally to start refreshing instances of autoscale group.
    """
    name = '{}{}'.format( profile, tag )
    return runaws( c, [ 'aws autoscaling start-instance-refresh',
                '--auto-scaling-group-name {}'.format( name ) ],
            iam=iam, local=True )

@mptask
def show_prod( c, **kwargs ):
    """
    Show info on production servers
    """
    for profile, tag in PROD_PROFILES:
        a( c, profile, tag )
        show_full( c )
