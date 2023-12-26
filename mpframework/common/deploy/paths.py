#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Path functions related setting up run-time environment

    NO MPF IMPORTS OR DEPENDENCIES IN THIS FILE
    It is used in initial configuration of import paths
"""
import os


#--------------------------------------------------------------------
# Fixed System paths

# HACK - calculated as relative from executing in mpframework folder
_home_path = os.path.abspath( os.path.join( os.path.dirname(__file__), '..', '..', '..' ))

def home_path( *args ):
    """
    Folder MPF lives in, normally the default user home folder.
    Returns root or additional paths added from args
    """
    return os.path.join( _home_path, *args )

def work_path( *args ):
    """
    Local folder used for server-specific work
    """
    return home_path( '.work', *args )

def autoscale_ip_file_path( profile, tag ):
    """
    HACK - used to pass IP values for autoscale groups between commands
    """
    return work_path( '{}{}.autoscale_ips'.format( profile, tag ) )

def mpframework_path( *args ):
    return home_path( 'mpframework', *args )

def deploy_path( *args ):
    return mpframework_path( 'deploy', *args )


"""-------------------------------------------------------------------
    Location for temp files like caching, sockets, upload, etc.
    Previously ephemeral storage was used for the temp drives for
    greater performance, but AWS has moved away from ephemeral
    instance storage in smaller machines, so is not likely available.
"""
_ephemeral_path = '/mnt/ephemeral0'
_ephemeral_path_available = os.path.exists( _ephemeral_path )

def temp_path( *args ):
    if _ephemeral_path_available:
        return os.path.join( _ephemeral_path, *args )
    return home_path( *args )


#--------------------------------------------------------------------
# HACK -- assume six lives in the site-packages folder
# and use that location to get path to site-packages

import six
_site_packages_path = os.path.abspath( os.path.join( os.path.dirname(six.__file__) ))

def packages_path( *args ):
    """
    Folder location for python modules, usually site-packages in virutalenv

    This should only be used for necessary hacks, such as accessing
    django templates by full path to avoid template recursion problem
    """
    return os.path.join( _site_packages_path, *args )
