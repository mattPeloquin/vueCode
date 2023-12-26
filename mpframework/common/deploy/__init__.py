#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Utility functions related to run-time environment

    NO MPF IMPORTS/DEPENDENCIES IN THIS MODULE
    since it is used for initialization
"""

# Signals used for uwsgi management
UWSGI_WORKER_PRE_SHUTDOWN = 6
UWSGI_SPOOLER_PRE_SHUTDOWN = 66


def load_module_attr( name ):
    """
    Give the full import path for a module routine or
    element, import and return it or throw exception.
    """
    from importlib import import_module
    path, element = name.rsplit( '.', 1 )
    module = import_module( path )
    return getattr( module, element )

def clean_env_get( key, default='' ):
    """
    Get environment value, cleaning up quoted strings (problem in Windows).
    Returns None if key doesn't exist.
    """
    import os
    try:
        value = os.environ.get( key, default )
        return str( value ).lstrip(' "').rstrip(' "')
    except KeyError:
        pass

#--------------------------------------------------------------------
# Profile utilities that can be used when settings not available

def is_prod_profile( name ):
    """
    Test to determine if a profile name is for production; by
    convention if starts with 'prod'
    """
    return bool( name and name.startswith('prod') )

def is_mpd_profile( name ):
    """
    MPF has a few special-cases for dev/debug profiles
    """
    return bool( name and 'mpd' in name )
