#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Fabric utility methods
"""
import os
import sys
import shutil
import subprocess

from mpframework.common.deploy import clean_env_get
from mpframework.common.deploy import load_module_attr
from mpframework.common.deploy import is_prod_profile
from mpframework.common.deploy import is_mpd_profile
from mpframework.common.deploy.paths import home_path
from mpframework.common.deploy.platforms import specialization_platforms

from .v1env import v1env


"""-------------------------------------------------------------------
    Target Folders

    Extend env.paths utils by providing root for path based on server/local
    Uses "xxx_folder" suffix vs. the "xxx_path" suffix
"""

def home_folder( *args ):
    if on_server():
        return target_path_join( 'home', 'ec2-user', *args,
                                    **{ 'absolute': True } )
    return home_path( *args )

def nginx_folder( *args ):
    return home_folder( 'nginx', *args )
def uwsgi_folder( *args ):
    return home_folder( 'uwsgi', *args )

def framework_folder( *args ):
    return home_folder( 'mpframework', *args )


"""-------------------------------------------------------------------
    Environment utilities

    Setup the fab environment parameters for running a task
    based on MPF settings/conventions
"""

def env_value( c, name ):
    """
    Get the name from local or remote environment depending on
    where the current command is being run
    """
    if v1env.is_remote:
        rv = c.run( 'echo $' + name, hide=True ).stdout.strip()
    else:
        rv = clean_env_get( name )
    if rv:
        print( "EnvVar: %s = %s  %s" % (
                    name, rv, 'remote' if v1env.is_remote else '') )
        return rv

def run_root_extension( c, fn_name, *args, **kwargs ):
    """
    Load and run root extensions to fab commands.
    """
    for name in specialization_platforms():
        try:
            full_name = '{0}.deploy.fab.extensions.{0}_{1}'.format( name, fn_name )
            fn = load_module_attr( full_name )
            fn( c, *args, **kwargs )
        except Exception as e:
            #print( "Did not load %s for %s" % ( fn_name, name ) )
            pass

def prod_profile( c ):
    """
    Check if a production profile is involved in the command
    and caches the result.
    Considers BOTH local profile and the remote target profile.
    """
    if not v1env.profile:
        v1env.profile = env_value( c, 'MP_PROFILE' )
    return is_prod_profile( v1env.profile )

def mpd_profile( c ):
    # Same as prod_profile, for dev
    if not v1env.profile:
        v1env.profile = env_value( c, 'MP_PROFILE' )
    return is_mpd_profile( v1env.profile )

def on_windows():
    return sys.platform.startswith('win')

def on_mac():
    return sys.platform.startswith('darwin')

def on_server():
    # Assume a Linux dev environment would be a 'server'
    return v1env.is_remote or not (on_windows() or on_mac())


#-------------------------------------------------------------------
# Wrappers for shell execution

def runcmd( c, command_list, *args, **kwargs ):
    """
    Wrapper to run shell command either remote or locally.

    Arguments for the command are made into a string, first
    from args and then kwargs.
    Returns the success code from local or remote invoke.

    Sudo commands are passed in sudo kwarg instead of baked into the
    command list to allow the use_sudo() flag to override.

    Special kwarg names for directives are popped off (e.g., sudo)
    Remaining kwargs values are displayed as 'k=v' string
    To allow option flags to be passed after arguments
    if value is blank only it is displayed, e.g.,
    "fab test -xyz"  converts to  "manage.py test --xyz"
    """
    pty = kwargs.pop('pty', False)
    sudo = kwargs.pop('sudo', False)
    local = kwargs.pop('local', False)
    echo = kwargs.pop('echo', False)
    hide = kwargs.pop('hide', False)
    warn = kwargs.pop('warn', False)
    activate = kwargs.pop('activate', False)
    outstream = kwargs.pop('out_stream', None)
    timeout = kwargs.pop('timeout', False)

    # Args are added to command line in the order received
    if len( args ) > 0:
        command_list.extend([ str(arg) for arg in args if arg is not None ])

    # If any kwargs remain after popping off special case keywords,
    # assume it is passed in from command line.
    # If value is blank, just display the key
    for key, val in kwargs.items():
        cmdline = str( key ) if not val else "{}={}".format( key, val )
        command_list.append( cmdline )

    # Fabric V2 SSH connections load bashrc (instread of bash_profile like V1)
    # If needed, add activate venv for every command
    if v1env.is_remote and ( activate or v1env.add_venv_activate ):
        command_list.insert( 0, '. .venv/bin/activate &&')

    # Build up wrapper for the command, so it can be run in sudo, timing, etc.
    command_wrapper = ''
    if timeout:
        command_wrapper = 'timeout --preserve-status {}'.format( timeout )
    if sudo and v1env.mp_sudo_ok:
        # Wrap entire command in sudo bash to ensure sudo applied to all elements
        # Use -E to preserve environment variable, such as server_setenv
        command_wrapper = 'sudo -E {}'.format( command_wrapper )
    if command_wrapper:
        # Wrap entire command to ensure wrappers applied to all elements
        command_list.insert( 0, '{} bash -c "'.format( command_wrapper ) )
        command_list.append( '"' )

    command_str = ' '.join( command_list )

    cmdargs = {
        'pty': pty or v1env.is_remote,
        'echo': echo,
        'hide': 'both' if hide is True else hide,
        'warn': warn,
        'out_stream': outstream,
        }

    print("----------------------------------------------")
    print( command_str )

    #for key, value in vars(v1env).items():
    #    v1env.fab_log and print(" > %s: %s" % (key, value))
    v1env.fab_log and print("------ Connection values -------")
    v1env.fab_log and print( str(c) )

    # Run command on remove server
    if not local and v1env.is_remote:
        # Setup environment variables that will be added to the command line, which
        # include any items setup with the e() decorator and platform/profile settings
        env_vars = v1env.mp_env.copy()
        env_vars.update( { 'MP_PROFILE': v1env.profile} if v1env.profile else {} )
        env_vars.update( { 'MP_PLATFORMS': ' '.join(v1env.mp_platforms) } if
                v1env.mp_platforms else {} )

        # Any strings sent to environment with spaces must be wrapped in quotes,
        # so just wrap everything
        for key, value in env_vars.items():
            env_vars[ key ] = '"{}"'.format( value )
            v1env.fab_log and print(" > %s: %s" % (key, value))

        # The inline_ssh_env option ensures Fabric sends the environment
        # updates to the remote ssh session
        c.config.inline_ssh_env = True
        rv = c.run( command_str, env=env_vars, **cmdargs )

    # Run command locally
    else:
        rv = c.run( command_str, replace_env=False, **cmdargs )

    return rv

def runscript( c, script_file, *args, **kwargs ):
    """
    Wrap calling script files, including optional sudo execution
    *args are passed as arguments for the script
    """
    command = [ 'bash', framework_folder( 'deploy', 'shell', script_file ) ]
    # Quote all arguments to ensure quotes in args are passed to shell
    # Also convert empty items into '' so shell gets arguments in order
    if len(args) > 0:
        args = ["'{}'".format(arg) if arg else "''" for arg in args]
    return runcmd( c, command, *args, **kwargs )

def rundj( c, *args, **kwargs ):
    """
    Run a django management command.
    Provides an easy location to ensure use of .venv when
    command is executed remotely.
    """
    prefix = kwargs.pop( 'prefix', '' )
    python_args = kwargs.pop( 'python_args', '-Wa' if v1env.warnings else '' )
    python = 'python3.9' if v1env.is_remote else sys.executable
    command = '{} {} {} -m manage'.format(
                prefix, python, python_args )

    # Run windows commands outside of invoke, as it does not correctly work
    # with the Windows shell since pty is not available for it yet.
    if not v1env.is_remote and on_windows():
        argv = [ a for a in command.split(' ') if a ]
        for arg in args:
            argv.extend([ a for a in arg.split(' ') if a ])
        for key, value in kwargs:
            argv.append('{} {}'.format( key, value ))
        print("WinSubProcess>", argv)
        return subprocess.call( argv )

    # Otherwise pass along to invoke
    else:
        if 'sudo' in kwargs:
            kwargs['activate'] = True
        return runcmd( c, [command], *args, **kwargs )

#-------------------------------------------------------------------
# Path Fixups

def target_path_join( *args, **kwargs ):
    return path_join( *args, **kwargs )

def local_path_join( *args, **kwargs ):
    return path_join( *args, local=True, **kwargs )

def path_join( *args, **kwargs ):
    local = kwargs.get('local')
    folder = kwargs.get('folder')
    absolute = kwargs.get('absolute')

    use_posix = not on_windows() if local else on_server()

    if use_posix:
        import posixpath as path
    else:
        import ntpath as path

    # Make a root, by slash prefix
    if absolute:
        args = (path.sep,) + args

    rv = path.join( *args )

    # Force a folder, by slash suffix
    # Can't pass the trailing slash to path, because it won't join
    # as it sees a root folder
    if folder:
        rv += path.sep

    return rv

#-------------------------------------------------------------------
# Remove file system items

def rm_dir( path ):
    shutil.rmtree( path, ignore_errors=True )

def rm_dir_contents( path ):
    for root, dirs, files in os.walk( path, topdown=False ):
        for name in files:
            try:
                os.remove( os.path.join(root, name) )
            except Exception:
                pass
        for name in dirs:
            os.rmdir( os.path.join(root, name) )

def rm_pyc( path ):
    for name in os.listdir(path):
        name_path = target_path_join( path, name )
        if name[-3:] == 'pyc':
            os.remove( name_path )
        elif os.path.isdir( name_path ):
            rm_pyc( name_path )
