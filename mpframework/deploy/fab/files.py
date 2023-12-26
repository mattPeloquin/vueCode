#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Management/manipulation of files on servers
"""
import os

from mpframework.common.deploy.paths import work_path

from .v1env import v1env
from .decorators import mptask
from .decorators import server
from .utils import runcmd
from .utils import home_folder
from .utils import local_path_join


#--------------------------------------------------------------------
# Support for pushing over files directly vs. doing HG update
# Handy when bench testing deployment issues

@mptask
@server
def push_files( c, file_path ):
    """Push files and folders from dev to servers"""

    # Make sure slashes are forward, which works with windows and
    # prevents potential silent fail on linux side
    from mpframework.common.utils.paths import path_clean
    file_path = path_clean( file_path )

    # HACK - Fixup any venv push, for dev experiments only
    if file_path.startswith('.venv'):
        remote_path = file_path.replace( '/lib/', '/lib/python3.9/')
    else:
        remote_path = file_path
    remote_path = home_folder( os.path.dirname(remote_path) )

    result = c.put( file_path, remote=remote_path )
    print( result.remote )

@mptask
@server
def pull_files( c, file_path, sudo=False ):
    """Pull files and folders from servers to local work"""
    from mpframework.common.utils.file import create_local_folder
    remote_path = home_folder( file_path )
    local_folder = local_path_join( work_path(), v1env.host )
    create_local_folder( local_folder )
    result = c.get( remote_path, local=local_folder, use_sudo=sudo )
    print( result.local )

@mptask
@server
def pull_logs( c ):
    """Get server log files (placed in local work)"""
    pull_files( c, 'uwsgi/*.log' )
    pull_files( c, '/var/log/nginx/*.log' )
    pull_files( c, '/var/log/cloud-init.log', sudo=True )


#--------------------------------------------------------------------
# Show utilities to bring output from files back to terminal

@mptask
@server
def show_bootlog( c ):
    """Show bootlog for the given server"""

    print("\n======> cat /var/log/cloud-init-output.log\n")
    runcmd( c, ['cat /var/log/cloud-init-output.log'], sudo=True, warn=True )

    print("\n======> grep failures /var/log/cloud-init.log\n")
    runcmd( c, ['grep failures /var/log/cloud-init.log'], sudo=True, warn=True )
