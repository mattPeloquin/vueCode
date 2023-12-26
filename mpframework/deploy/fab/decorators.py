#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Fabric Task Decorators
"""
import wrapt
from functools import partial
from invoke import Exit
from fabric import task
from fabric import SerialGroup

from mpframework.common.deploy import clean_env_get
from mpframework.common.deploy.paths import home_path
from mpframework.common.deploy.platforms import root_name

from .v1env import v1env
from .utils import runcmd
from .utils import on_server
from .utils import mpd_profile
from .utils import prod_profile


def mptask( func=None, skip_setup=False, local_only=False,
            reset=False, root=None, optional=None ):
    """
    MPF Task decorator
    Replaces fabric task decorator to set up MPF tasks with
    profile environment settings.
    """
    if func is None:
        return partial( mptask, skip_setup=skip_setup,
                    local_only=local_only, reset=reset, root=root )

    @wrapt.decorator
    def wrapper( fn, _instance, args, kwargs ):
        c = args[0]
        host = getattr( c, 'host', None )

        # Support task resetting hosts for multiple runs
        if reset:
            _reset()

        # Setup environment for the task
        if not skip_setup and not v1env.env_setup:
            _setup_env( root )
            if host:
                _setup_host( c )

        # Run task for each host member (must be IPs)
        if not local_only and not host and v1env.hosts:
            for hostc in SerialGroup( *v1env.hosts ):
                _setup_host( hostc )
                fn( hostc, *args[1:], **kwargs )
        # Or just run the task
        else:
            return fn( *args, **kwargs )

    optional = optional if optional else []

    return task( wrapper( func ), optional=optional )

def _setup_env( root ):
    """
    Set root and profile environment for local and remote commands.
    """
    root_name = root if root else ( v1env.root_name or _get_root() )
    if not root_name:
        raise Exit("\n\nA root must be defined")
    v1env.root_name = root_name

    # Use local profile if one is not provided
    if not v1env.profile:
        v1env.profile = clean_env_get('MP_PROFILE')

    v1env.env_setup = True

def _get_root():
    """
    The root name can be set in current fabric command, the environment,
    or default to the current root platform.
    """
    rv = clean_env_get('MP_FAB_REMOTE_ROOT')
    if not rv:
        platforms = v1env.mp_platforms
        if platforms:
            rv = platforms[-1]
    if not rv:
        rv = root_name()
    return rv

def _reset():
    v1env.hosts = []
    v1env.is_remote = False

def _setup_host( c ):
    """
    Configure remote connection info for current and chained commands.
    """
    v1env.is_remote = True
    c.user = v1env.user

    # HACK - set prod-mpd for local tasks as a convenience
    if c.host.startswith('prodmpd'):
        v1env.profile = 'prod-mpd'

    # Set path to local key file
    if not v1env.keyfile:
        v1env.keyfile = 'prod.pem' if prod_profile( c ) else 'dev.pem'
    v1env.keyfile_path = [ home_path('.secrets', v1env.root_name, v1env.keyfile) ]
    print(">>> Remote task: %s -- %s %s %s" % (
            c.host, v1env.profile, v1env.root_name, v1env.keyfile ))

    # Configure the connection
    c.connect_kwargs.update({
       'key_filename': v1env.keyfile_path,
        })

#--------------------------------------------------------------------
# Other decorators

@wrapt.decorator
def server( fn, _instance, args, kwargs ):
    if on_server():
        return fn( *args, **kwargs )
    raise Exit("\n ***  This task can only be run against servers  ***\n")

@wrapt.decorator
def code_current( fn, _instance, args, kwargs ):
    """
    Add the current code revision into the environment, which is used to
    for some MP_PLAYPEN namespaces (e.g., static file versions, dev caching)
    """
    if not v1env.mp_env.get('MP_CODE_CURRENT'):
        from .env import set_env
        c = args[0]
        output = ''
        try:
            # TBD - support transition from Hg to Git
            output = runcmd( c, ['hg id -n'] )
        except Exception as e:
            try:
                output = runcmd( c, ['git describe --always'] )
            except Exception as e:
                print("Could not get code tag", e)
        tag = output and str(output.stdout).strip(' +\n')
        set_env( MP_CODE_CURRENT=tag )
    return fn( *args, **kwargs )

@wrapt.decorator
def runs_once( fn, _instance, args, kwargs ):
    """
    Implement a Fabric V1 runs_once equivalent
    """
    if not getattr( fn, '_mp_ran', None ):
        fn._mp_ran = True
        return fn( *args, **kwargs )

@wrapt.decorator
def skip_dev( fn, _instance, args, kwargs ):
    """
    Don't run this command in a local dev environment
    Similar to the server decorator, but is more graceful in
    allowing composition with commands that can run locally
    """
    if on_server():
        return fn( *args, **kwargs )
    else:
        print( "\nSkipping task due to dev environment" )

@wrapt.decorator
def prod_warn( fn, _instance, args, kwargs ):
    """
    Protect commands that should be used carefully in production
    """
    def show_warning():
        c = args[0]
        return ( prod_profile( c ) and not mpd_profile( c ) and
                    v1env.prod_warn )
    # If prod profile and override hasn't been set already,
    # ask for human approval and add override value
    if show_warning():
        check = input("\nProduction profile, ARE YOU SURE? ")
        if check == 'HELL YA':
            v1env.prod_warn = False
    if not show_warning():
        return fn( *args, **kwargs )
    raise Exit("Task aborted by user")

@wrapt.decorator
def dev_only( fn, _instance, args, kwargs ):
    """
    Protect commands that should never be run against production
    """
    c = args[0]
    if prod_profile( c ):
        print("\n\n ***  Task cannot run against prod profile  ***\n")
    else:
        return fn( *args, **kwargs)

@wrapt.decorator
def elapsed_time( fn, _instance, args, kwargs ):
    """
    Time the task and add message at the end
    """
    from mpframework.common.utils import ElapsedTime
    timer = ElapsedTime()
    # Wrap task call to catch any exception, including ctrl-c
    try:
        return fn( *args, **kwargs )
    except Exception:
        import sys
        print("FAB EXCEPTION: %s => %s" % (fn.__name__, sys.exc_info()[0]))
        raise
    finally:
        print("\nTotal run time: %s" % timer.elapsed().total_seconds())
