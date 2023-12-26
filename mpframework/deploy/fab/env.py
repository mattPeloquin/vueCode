#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Functions and tasks that set up environment for
    chained tasks that come after them.
"""
import os

from mpframework.common.deploy.platforms import all_platforms

from .v1env import v1env
from .decorators import mptask


@mptask( skip_setup=True )
def p( _c, profile ):
    """
    Override MP_PROFILE: fab p dev cmd1 cmd2
    """
    v1env.profile = profile
    set_env( MP_PROFILE=profile )

@mptask
def pl( _c, platforms ):
    """
    Override MP_PLATFORMS: fab pl "xxx yyy" cmd1 cmd2
    """
    v1env.mp_platforms = all_platforms( platforms )
    set_env( MP_PLATFORMS=" ".join( v1env.mp_platforms ) )

@mptask( skip_setup=True )
def k( _c, keyfile ):
    """
    Use a specific keyfile (instead of profile prefix)
    """
    v1env.keyfile = keyfile

@mptask( skip_setup=True )
def d( _c, debug='True' ):
    """
    Use debugging: fab d cmd1
    """
    set_env( DEBUG=debug )

@mptask( skip_setup=True )
def l( _c, info='2', debug='1', sl1='', sl2='', sl3='', fabric=False ):
    """
    Set logging level: fab l -i 2 -d 1 -s db --sl2 cache --fabric
    """
    set_env( MP_LOG_LEVEL_INFO_MIN=info )
    subs = [ sub for sub in [ sl1, sl2, sl3 ] if sub ]
    debug = '1' if subs else debug
    set_env( MP_LOG_LEVEL_DEBUG_MIN=debug )
    set_env( MP_LOG_SUB=str(subs) )
    if debug:
        set_env( MP_FAB_LOG='True' )
        v1env.fab_log = True
    if fabric:
        set_env( MP_FAB_DEBUG='True' )
        from mpframework.common import log
        log.set_log_level()

@mptask( skip_setup=True )
def w( _c ):
    """
    Turn on Python warnings (local only)
    """
    v1env.warnings = True

@mptask( skip_setup=True )
def r( _c, root_name ):
    """
    Override the root platform name
    """
    v1env.root_name = root_name

@mptask
def e( _c, name, value ):
    """
    Add env variables: fab e NAME VALUE cmd1 cmd2
    """
    set_env(**{ name: str(value) })

def set_env( **kwargs ):
    """
    Set environment variable for this run.
    The variable is added BOTH to local os.environ AND to mp_env,
    which is used to set environment for remote commands.
    """
    v1env.mp_env.update( kwargs )
    os.environ.update( kwargs )
