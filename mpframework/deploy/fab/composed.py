#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Composed fabric tasks, created from more granular tasks
"""
from time import sleep

from .env import p
from .decorators import mptask
from .decorators import prod_warn
from .decorators import dev_only
from .decorators import code_current
from .shell import *
from .djutils import *


ELB_DRAIN_WAIT = 6
DEFUALT_LOCAL = '0.0.0.0'


"""--------------------------------------------------------------------
    Server Refresh
    Non-destructive (to data) updates for both dev and prod
"""

@mptask
@prod_warn
def refresh( c, rev='', quick=False, hard=False, full=False, config=False ):
    """
    Server refresh: [rev quick hard full config]
    The core set of steps for various levels of config and update for
    all code/settings/config on the servers.
    Cloud-Init bootstrap calls with config=True to initialize
    newly launched instances, so doesn't do ELB add/remove.
    """
    config = full or config
    quick = not config and quick
    do_elb = full or not ( quick or config )

    if do_elb:
        aws_elb_remove( c )
        sleep( ELB_DRAIN_WAIT )

    stop( c, hard=hard )

    if not quick:
        clean( c )
    update_code( c, rev=rev )

    if not quick:
        update_server( c, full=config )
        update_dirs( c )
        if config:
            update_pip( c )

    server_config( c, full=config )
    static( c )

    start( c )
    if do_elb:
        aws_elb_add( c )

#--------------------------------------------------------------------
# Development run commands

@mptask
@dev_only
@code_current
def run( c, address='', single=False, port='80' ):
    """
    Local server: fab run [address single]
    """
    if ':' in address:
        address_str = address
    else:
        address_str = DEFUALT_LOCAL + ':' + port + address
    rundj( c, 'run_mpserver %s --noreload ' % (
                '--nothreading' if single else '' ,), address_str )

@mptask
def run_prod( c ):
    """Run prod dev server with JS compressed (port 80)"""
    p( c, 'local-prod')
    static( c )
    run( c )
