#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF shell scripts and shell commands
    Some tasks also have alternative behavior for local dev
    HACK - some hard-coded paths to well-known process locations

    This file both wraps deploy .sh files and makes shell calls from Python.
    It assumes default MPF deployments, which includes nginx and uwsgi
    running on the server, configured based on settings profiles.
"""
from time import sleep

from mpframework.common.deploy import UWSGI_SPOOLER_PRE_SHUTDOWN
from mpframework.common.deploy import UWSGI_WORKER_PRE_SHUTDOWN
from mpframework.common.deploy.paths import home_path
from mpframework.common.deploy.paths import work_path

from .v1env import v1env
from .decorators import *
from .utils import *

UWSGI_SHUTDOWN_WAIT = 30  # HACK - max time to wait for shutdown


@mptask
def no_sudo( c ):
    """Prevent chained commands from being run with sudo"""
    v1env.mp_sudo_ok = False

@mptask
def no_prod_warn( c ):
    """Prevent chained commands from prompting prod warning"""
    v1env.prod_warn = False

"""--------------------------------------------------------------------
    Server start/stop

    Server restart is done by completely stopping both uwsgi and nginx.
    Reloading is not used because it is not needed since server lifetime
    and connections are managed through ELB, and since managing the
    use of environment configuration is simpler with full restarts.
"""

@mptask
@code_current
def start( c ):
    """Start server processes"""
    runscript( c, 'start.sh' )

@mptask
@skip_dev
def stop( c, hard=False, kill=False, force=False ):
    """
    Shutdown server processes
    Includes options to force and cleanup
    Nginx is closed immediately, so assumption is incoming requests have stopped.
    Unless forced, uwsgi should do a graceful shutdown that finishes tasks.
    """
    force = force or hard
    _uwsgi_fifo = uwsgi_folder('master.fifo')
    _uwsgi_socket = uwsgi_folder('uwsgi.sock')

    if not kill:
        if not hard:
            pre_shutdown( c )
        # Normally tell nginx to quit, so it will wait on uwsgi
        runcmd( c, [ 'nginx -s {}'.format('stop' if force else 'quit' ) ],
                sudo=True, warn=True )
        # Only try orderly shutdown of uWSGI if it appears to be running
        if uwsgi_master_running( c ):
            runcmd( c, [ 'echo {} > {}'.format( 'Q' if force else 'q', _uwsgi_fifo ) ],
                    sudo=True, warn=True )
            if not hard:
                print("\nWaiting for uwsgi to shutdown...")
                checks = 0
                while checks < UWSGI_SHUTDOWN_WAIT:
                    if not uwsgi_master_running( c ):
                        print("Shutdown is complete!")
                        break
                    sleep( 1 )
                    checks += 1

    # Always tidy up, just in case
    runcmd( c, [ 'killall -9 nginx' ], sudo=True, warn=True )
    runcmd( c, [ 'killall -9 uwsgi' ], sudo=True, warn=True )
    runcmd( c, [ 'rm {}'.format( _uwsgi_fifo ) ], sudo=True, warn=True )
    runcmd( c, [ 'rm {}'.format( _uwsgi_socket ) ], sudo=True, warn=True )
    if kill:
        runcmd( c, [ 'killall -9 rsyslogd' ], sudo=True, warn=True )

def pre_shutdown( c, delay=2 ):
    """
    Signal server that it will be shut down soon.
    HACK - uWsgi singals can be slow, so add delay for them to take
    """
    if uwsgi_master_running( c ):
        _uwsgi_socket = uwsgi_folder('uwsgi.sock')
        runcmd( c, [ 'uwsgi --signal {},{}'.format( _uwsgi_socket,
                UWSGI_WORKER_PRE_SHUTDOWN ) ], warn=True )
        sleep( delay )
        runcmd( c, [ 'uwsgi --signal {},{}'.format( _uwsgi_socket,
                UWSGI_SPOOLER_PRE_SHUTDOWN ) ], warn=True )
        sleep( delay )

def uwsgi_master_running( c ):
    return exists( c, uwsgi_folder('uwsgi.sock') )

#--------------------------------------------------------------------
# Server config and setup (for dev and prod)
# All update tasks should be idempotent

@mptask
@server
@prod_warn
def update_code( c, rev=None, force=False ):
    """
    Update code: fab update-code [ -r codeRev --force ]
    """
    # To use automated code pull, must add root version of update code
    run_root_extension( c, 'update_code' , rev=rev, force=force )

@mptask
@prod_warn
def clean( c ):
    """
    Clean up temp and derived files (resets DB in local)
    """
    if on_server():
        runscript( c, 'clean.sh', warn=True )
        update_dirs( c )
    else:
        # Local dev machine clean
        # HACK -- since local DB is file, include refresh of DB here
        from .djutils import db_sync, db_load
        rm_dir_contents( work_path() )
        rm_pyc( home_path() )
        db_sync( c )
        db_load( c )

@mptask
@prod_warn
def update_server( c, full=False ):
    """
    Update server outside pip (Linux, nginx, etc.)
    Unlike install_server, changes here can be added to existing images.
    """
    runcmd( c, [ 'yum -y update {}'.format( '' if full else '--security' ) ],
            sudo=True, warn=True )

    # Support root-specific updates
    run_root_extension( c, 'update_server', full )

@mptask
@prod_warn
def update_pip( c ):
    """
    Update current pip requirements for current virtual environment.
    """
    runcmd( c, [ 'pip install --upgrade pip' ] )
    runcmd( c, [ 'pip install --upgrade setuptools' ] )
    runcmd( c, [ 'pip install --upgrade wheel' ] )

    # Always install requirements needed on both dev and server
    runcmd( c, [ 'pip install --upgrade -r',
            framework_folder( 'deploy', 'pip_shared.txt') ] )

    # Server requirements, including uWSGI
    if on_server():
        runcmd( c, [ 'pip install --upgrade -r',
                framework_folder( 'deploy', 'pip_server.txt' ) ] )

    # Dev install requirements
    if not prod_profile( c ) or mpd_profile( c ):
        runcmd( c, [ 'pip install --upgrade -r',
                framework_folder( 'deploy', 'pip_dev.txt' ) ] )

    # Support root-specific updates
    run_root_extension( c, 'update_pip' )

@mptask
@server
@prod_warn
def server_setenv( c, home='', profile='', tag='', rev='', platforms='' ):
    """
    server_setenv [home profile tag rev platform]
    View and set the server environment
    """
    platforms = platforms or ' '.join( v1env.mp_platforms )

    if any([ profile, home, rev, platforms,  ]):
        print( "\nWill set the following:\n"
               "   MP_HOME            = %s\n"
               "   MP_PROFILE         = %s\n"
               "   MP_PROFILE_TAG     = %s\n"
               "   MP_CODE_REV        = %s\n"
               "   MP_PLATFORMS       = %s\n"
               % (profile, home, tag, rev, platforms) )
        print( "Affects FUTURE process starts\n" )

    runscript( c, 'setenv.sh', home, profile, tag, rev, platforms, sudo=True )

@mptask
@skip_dev
def update_dirs( c ):
    """Create and set permissions on server dirs"""
    print("\nRunning update dirs and permissions scripts...")
    runscript( c, 'update_dirs.sh', sudo=True, warn=True )
    runscript( c, 'update_perms.sh', sudo=True, warn=True )

@mptask
@server
def install_server( c ):
    """
    INITIAL update of server environment, baked into AMI.
    """
    runscript( c, 'install_server.sh' )

#--------------------------------------------------------------------
# Utilities

@mptask
def shell_cmd( c, command ):
    """Run command: fab shell_cmd "ls nginx" """
    return runcmd( c, [command] )

@mptask
@server
def shell_open( c ):
    """Open a shell to a server"""
    c.run( '/bin/bash', pty=True )

@mptask
@server
def show_disk( c ):
    """Show disk space on server(s)"""
    # List disk volumes and total sizes
    runcmd( c, ['df'] )
    # Show top level folders that have MB or GB size
    runcmd( c, ['du -ch -d 1 $MP_HOME/.[^.]* $MP_HOME/* | grep [0-9][GM]'], warn=True )

@mptask
@server
def show_mem( c ):
    """Show memory usage per process"""
    runcmd( c, ['top -b -n 1 -o %MEM'] )

#--------------------------------------------------------------------

def exists( c, path, sudo=False ):
    """
    Return True if given path exists on the current remote host.
    """
    out = runcmd( c, [ 'stat {}'.format( path ) ],
            sudo=sudo, warn=True, hide=True )
    return not out.failed
