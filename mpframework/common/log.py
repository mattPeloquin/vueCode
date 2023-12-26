#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logging/Error reporting

    For mpFramework, the term 'logging' relates to debug, info, or error messages
    instrumenting system code to enable tracing, debugging, and error response --
    NOT programmatic capturing of user events, system monitoring, audit trails, etc.
    Put another way -- if it is a text message for a human to read, it should
    be done through this mechanism; if it is a piece of data intended to be
    consumed by software, it should not.

    Non-debug logging provides levels of operational info, troubleshooting, and
    warnings about problems or potential attacks. Debug supports development
    activities and production troubleshooting when needed, with more overhead.

    Logging is built on the Python logging framework, but is used differently
    than typical Python logging. There is one global logger vs. per-module
    loggers. This global logging is filtered via various settings
    and logging calls. Essentially logging filtering focuses more on
    types of messages vs. messages from particular modules or package trees.

    See .logging.setup for more details.

    Logging is intended to scale from dev workstation support to high-volume
    server clusters support using rsyslog and external aggregator.
"""
import os
import sys
import traceback
from django.conf import settings

from .logging.debug import set_subdebug
from .logging.debug import mp_debug
from .logging.utils import get_logger


"""----------------------------------------------------------------------
    Main logging methods
"""

# General information logging provides visibility into system operation
# with levels of detail based on info_level setting

def info( msg, *args, **kwargs ):
    _info( msg, 1, *args, **kwargs )
def info2( msg, *args, **kwargs ):
    _info( msg, 2, *args, **kwargs )
def info3( msg, *args, **kwargs ):
    _info( msg, 3, *args, **kwargs )
def info4( msg, *args, **kwargs ):
    _info( msg, 4, *args, **kwargs )
def info_mail( msg, *args, **kwargs ):
    info( msg, *args, logger='mp.info_mail', **kwargs )

def _info( msg, level, *args, **kwargs ):
    # Use debug logger for info if debug is on
    if _debug_on and _debug_on + 1 >= level:
        logger = kwargs.pop( 'logger', 'mp' )
        mp_debug( logger, msg, *args, **kwargs )
    elif _info_on >= level:
        _logger( kwargs ).info( msg, *args, **kwargs )

def _logger( kwargs ):
    logger_name = kwargs.pop( 'logger', 'mp' )
    return get_logger( logger_name )

# Warning - important recoverable events, bad data, external action
# Error - potentially unrecoverable, programming errors or bad external events
# Exception - use current exception object for programming errors

def warning( msg, *args, **kwargs ):
    _logger( kwargs ).warning( msg, *args, **kwargs )

def error( msg, *args, **kwargs ):
    _logger( kwargs ).error( msg, *args, **kwargs )

def exception( msg, *args, **kwargs ):
    prefix = kwargs.pop( 'prefix', "EXCEPTION " )
    if settings.MP_TESTING:
        prefix = "> " + prefix
    _logger( kwargs ).exception( prefix + msg, *args, **kwargs )

def warning_quiet( msg, *args, **kwargs ):
    warning( msg, *args, logger='mp.no_mail', **kwargs )
def error_quiet( msg, *args, **kwargs ):
    error( msg, *args, logger='mp.no_mail', **kwargs )
def exception_quiet( msg, *args, **kwargs ):
    exception( msg, *args, logger='mp.no_mail', **kwargs )

# General debug logging, see sub-logging for more detailed items

def debug( msg, *args, **kwargs ):
    if _debug_on: return mp_debug( 'mp.debug', msg, *args, **kwargs )

def debug2( msg, *args, **kwargs ):
    if _debug_on: return mp_debug( 'mp.debug2', msg, *args, **kwargs )

def debug3( msg, *args, **kwargs ):
    if _debug_on: return mp_debug( 'mp.debug3', msg, *args, **kwargs )

def info_stack( depth=8, skip=2, exc=None ):
    lines = []
    if not exc:
        _type, exc, _tb = sys.exc_info()
    if exc:
        if not settings.MP_TESTING:
            info("=== EXCEPTION DUMP: %s ===\n", type(exc))
            lines = traceback.format_tb( exc.__traceback__ )
    else:
        info("=== STACK LOG (skip=%s, depth=%s) ===\n", skip, depth)
        lines = traceback.format_stack()[ -(depth+skip):-skip ]
    for line in lines:
        info( line )

def debug_stack( depth=12, skip=2, exc=None ):
    if _debug_on:
        info_stack( depth, skip, exc )

def debug_values( msg, *args, **kwargs ):
    # Use to dump values into log, especially for items with side effects
    # from turning the item into a string
    if _debug_on and _values_on:
        return mp_debug( 'mp.debug', msg, *args, **kwargs )


"""---------------------------------------------------------------------
    Logging level

    Python logging normally processes each call and decides if/how to route.
    The amount of processing to support a logging statement can be noticeable,
    particularly if creating the string from an object is expensive
    (e.g., Django querysets will hit the DB when converted to strings).

    debug_on is checked before calling any debug logging, so can be set
    off to disable debug logging processing and string conversion.
    Use comma args instead of % or format in setting up debug strings
    to delay processing for converting values into strings.

    Then the debug_on flag can prevent most processing. It can also be checked
    explicitly in code to turn debug logging almost into noops if needed.

    Some items in the argument list may need to be evaluated, in which case
    use an 'if' clause to check debug_on.
"""

# Global flags
_info_on = 0   # Checks to avoid processing if info_level is 0
_debug_on = 0   # Allow checks to avoid expensive processing in non-debug
_values_on = False  # Check for expensive or side-effect value logging

def info_on():
    return max( _debug_on + 1 if _debug_on else 0, _info_on )
def debug_on():
    return _debug_on
def values_on():
    return _values_on

def set_log_level( info_level=None, debug_level=None, values=False ):
    """
    To minimize overhead of debug log calls in production
    disable debug methods if logging is turned off
    """
    global _info_on, _debug_on, _values_on

    info_level = info_level or int(
                os.environ.get( 'MP_LOG_LEVEL_INFO_MIN', 2 ) )
    debug_level = debug_level or int(
                os.environ.get( 'MP_LOG_LEVEL_DEBUG_MIN', 0 ) )

    _info_on = info_level or debug_level
    _debug_on = debug_level
    _values_on = values

    set_subdebug( globals() )

    # Do initial logging dict config if not done already
    from .logging.setup import set_logging_dict
    set_logging_dict( debug_level )
    debug("LOGGING SET: info=%s debug=%s", info_on(), debug_on() )

# Initial logging setup, prior to loading settings
set_log_level()
