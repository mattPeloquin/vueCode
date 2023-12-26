#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Platform and root management

    The platforms defined by a root configuration bootstrap the
    profile configuration system (by selecting which platforms to
    read configuration from).

    NO MPF IMPORTS OR DEPENDENCIES IN THIS FILE
    It is used in initial configuration of MPF import paths
"""
import os

from . import clean_env_get
from .paths import home_path


def root_name( platform_str=None ):
    """
    By convention, the last name in root platforms is the name of
    the root instance, which is the last platform
    """
    return all_platforms( platform_str )[-1]

def specialization_platforms( platform_str=None ):
    """
    Specialization platforms are any extension platforms and a
    root platform added to mpframework.
    """
    return all_platforms( platform_str )[1:]

def all_platforms( platform_str=None ):
    """
    Return list of platform names

      - If platform_str string is empty, try to get name from MP_PLATFORMS,
        or try to load all extension platforms if blank.

      - If there is only one platform name and it doesn't start with 'mp'
        look in topmost module for set of extension platforms.

    NOTE - Server shell scripts won't read this, so server environments
    need to be setup with full MP_PLATFORMS name, which can be done via
        'fab server-setenv'
    """
    if platform_str is None:
        platform_str = clean_env_get('MP_PLATFORMS')
    if _all_platforms.get( platform_str ):
        return _all_platforms[ platform_str ]

    names = platform_str.split()

    # HACK - Default case for testing, if blank string passed
    # LOAD ALL SUBFOLDERS
    if not names:
        # Add any mp folders first, and then go through remaining
        for folder in next( os.walk( home_path() ) )[1]:
            if folder.startswith('mp') and folder not in names:
                names.append( folder )
        for folder in next( os.walk( home_path() ) )[1]:
            if not folder.startswith(('.','_')) and folder not in names:
                names.append( folder )

    # If platforms have a non-mp folder, it is non-mp root, so must load
    # required platforms from root __init__.py module
    elif len(names) == 1 and not names[0].startswith('mp'):
        root_name = names[0]
        try:
            exec( "from {} import MP_PLATFORMS as platform_str".format(root_name) )
            names = platform_str.split()
        except ImportError:
            print("ERROR importing platform - check name: %s\n" % (root_name))
            raise

    # HACK - If folder doesn't have a deploy package it isn't valid
    rv = ['mpframework']
    for name in names:
        if name not in rv:
            try:
                exec( "from {} import deploy".format( name ) )
                rv.append( name )
            except Exception as e:
                #print("Ignoring platform: %s -> %s" % (name, e))
                pass

    _all_platforms[ platform_str ] = rv
    return rv

_all_platforms = {}