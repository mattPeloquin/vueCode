#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Config Python logging for mpFramework use, by defining handlers for
    logging types and levels. These are all available vs. default
    approach of loading specific loggers in each file.

    This file both sets up default logging and suports dynamic
    configuration by swapping out the entire logging_dict.

    NOTE -- This is loaded and logging_dict called at startup before Django
    settings are completely set up, so some settings are special-cased.
"""
import os
from logging.config import dictConfig
from contextlib import contextmanager
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .filters import SqlFilter
from .debug import sub_loggers


def set_logging_dict( debug_level=0, verbose=None ):
    # Convenience for initializing logging
    dictConfig(
        logging_dict( debug_level=debug_level, verbose=verbose )
        )

"""-----------------------------------------------------------------
    Logging Format

    For non-framework logging use normal Python logging values; for
    MPF logging, use XXX_MP replacements since logging
    calls are wrapped amd additional information is provided.
"""

_PROCID = '%(process)s:%(threadName)s'

# Syslog logging uses tag at start of string that is consumed
# Also add color - ANSI color values (32, 34, etc.)
_FORMAT_SYSLOG = 'uwsgi: \x1b[32m{} {} \x1b[32m{}'
_FORMAT_SYSLOG_MSG = '\x1b[37m%(message)s'

# Console and file formatting
_FORMAT_CONSOLE = '{}{}  %(message)s  {} (s%(asctime)s)'

# Verbose tracing for where call came from
_TRACE = '%(pathname)s:%(lineno)s %(funcName)s() %(levelname)s'

# Debug-only tracing for who generated the call
_MPUSER = '%(mpd-user)s'
_TRACE_MP = '%(mpd-path)s:%(mpd-line)s %(mpd-func)s() %(levelname)s'

# These module variables keep track of state that is eventually loaded
# from config settings, but are also needed for preinit
_verbose = False
_as_app = False
_syslog = None
_log_path = None

# file_mpd file handler adds verbose logging to file including
# process and thread info. Normally this isn't needed for local
# debug logging, and the log file handler isn't used on server
# because console logging is used with uwsgi
#MPD_FILE = 'file_mpd'
MPD_FILE = 'file'


def logging_dict( debug_level=1, verbose=None, sub_on=False,
                  as_app=None, syslog=None, logfile_path=None ):
    """
    Factory method that creates default logging dict with an adjustable
    level so Python DEBUG vs. INFO can be set across all loggers.
    Default is to start logging at DEBUG or INFO level, and then do
    set_logging after settings/options are known.
    """

    # Map MPF debug on/off to Python logging levels
    # MPF logging never goes below Python's INFO level, but management
    # of external logging may use different values
    level = 'DEBUG' if debug_level else 'INFO'

    # If values are provided, override current module settings
    global _verbose, _as_app, _syslog, _log_path
    _verbose = _verbose if verbose is None else verbose
    _as_app = _as_app if as_app is None else as_app
    _log_path = _log_path if logfile_path is None else logfile_path
    _syslog = _syslog if syslog is None else syslog

    # Setup console, file, and direct remote handlers
    console_handler = 'null' if _as_app and _syslog else _console()
    file_handler = MPD_FILE if _log_path else 'null'
    syslog_handler = 'syslog_def' if _syslog else 'null'

    # Setup items that are not available during logging preinit
    _sql_filter = { '()': SqlFilter } if _as_app else {}

    # Restart logfile
    if _log_path:
        try:
            if( not settings.MP_TESTING and
                    settings.MP_LOG_OPTIONS.get('LOCALFILE_RESET') ):
                os.remove( _log_path )
        except Exception:
            pass

    fabric_level = 'DEBUG' if os.environ.get('MP_FAB_DEBUG') else 'ERROR'

    #-----------------------------------------------------------------
    # Default Logging settings

    rv = {
        'version': 1,
        'disable_existing_loggers': True,

        'formatters': {

            # Normal non-verbose logging is geared towards local development
            'normal': {
                'format': '%(message)s',
                },
            'spaced': {
                'format': '%(message)s\n',
                },

            # Verbose logging used in production to debug server
            # ONLY handlers for mp_debug() in log.py can use mpverbose
            'verbose': {
                'format': _FORMAT_CONSOLE.format( '', _PROCID, _TRACE ),
                },
            'mpverbose': {
                'format': _FORMAT_CONSOLE.format( _MPUSER, _PROCID, _TRACE_MP ),
                },

            # For SQL trace output
            'mpsql': {
                'format': '(%(duration).3f) %(sql)s',
                },

            # Root handler; to debug logging that falls into root
            'root': { 'format': 'LOG(%(name)s) -- %(message)s', },
            },

        'filters': {
            # Make Django SQL more legible, see SqlFilter class
            'sql': _sql_filter,
            },

        # Set handlers to lowest logging level they'd usually support
        'handlers': {
            # Catch alls
            'null': { 'level': 'DEBUG', 'class': 'logging.NullHandler', },
            'root': { 'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'root',
                },
            # Use MPF email logger
            'email_info': {
                'level': level,
                'class': 'mpframework.common.logging.handlers.mpEmailInfoHandler',
                },
            'email_warning': {
                'level': 'WARNING',
                'class': 'mpframework.common.logging.handlers.mpEmailErrorHandler',
                },
            'email_direct': {
                'level': 'WARNING',
                'class': 'mpframework.common.logging.handlers.mpEmailErrorDirectHandler',
                },
            # Console logging is used both for interactive dev work, and to stream into
            # production logging files
            'console': { 'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'normal',
                },
            'console_spaced': { 'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'spaced',
                },
            'console_verbose': { 'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
                },
            'console_mpverbose': { 'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'mpverbose',
                },
            'console_sql': { 'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'filters': ['sql'],
                'formatter': 'mpsql',
                },

            },

        # Root logger catches any logging not defined under known namespaces
        # This is used primarily to debug logging itself, i.e., logging
        # should not propagate through to the root logger
        'root': {
            'handlers': [ 'root', file_handler, syslog_handler, 'email_warning' ],
            'level': level,
            },

        # Logger namespace as loaded by getLogger()
        'loggers': {

            # Fabric debug logging support
            'invoke': {
                'handlers': [ console_handler, file_handler, syslog_handler ],
                'level': fabric_level, 'propagate': False,
                },

            # MPF logging
            'mp': {
                'handlers': [ console_handler, file_handler, syslog_handler, 'email_warning' ],
                'level': level, 'propagate': False,
                },
            'mp.no_mail': {
                'handlers': [ console_handler, file_handler, syslog_handler ],
                'level': level, 'propagate': False,
                },
            'mp.info_mail': {
                'handlers': [ console_handler, file_handler, syslog_handler , 'email_info' ],
                'level': level, 'propagate': False,
                },
            'mp.direct_mail': {
                'handlers': [ console_handler, file_handler, syslog_handler, 'email_direct' ],
                'level': level, 'propagate': False,
                },

            },
        }

    #-----------------------------------------------------------------
    # Syslog is main mechanism for production logging for uwsgi
    if _syslog:

        rv['formatters']['syslog_def'] = {
            'format': _FORMAT_SYSLOG.format( _PROCID, _FORMAT_SYSLOG_MSG,
                                             _TRACE if _verbose else '' ),
            }
        rv['formatters']['syslog_mpd'] = {
            'format': _FORMAT_SYSLOG.format( _PROCID, _FORMAT_SYSLOG_MSG,
                                             _TRACE_MP if _verbose else '' ),
            }
        rv['formatters']['syslog_sql'] = {
            'format': _FORMAT_SYSLOG.format( _PROCID, '(%(duration).3f) %(sql)s',
                                             '' ),
            }

        syslog_handler = {
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',
            'level': 'DEBUG',
            'facility': 'local7',
            }
        rv['handlers']['syslog_def'] = syslog_handler.copy()
        rv['handlers']['syslog_def'].update({
            'formatter': 'syslog_def',
            })
        rv['handlers']['syslog_mpd'] = syslog_handler.copy()
        rv['handlers']['syslog_mpd'].update({
            'formatter': 'syslog_mpd',
            })
        rv['handlers']['syslog_sql'] = syslog_handler.copy()
        rv['handlers']['syslog_sql'].update({
            'filters': ['sql'],
            'formatter': 'syslog_sql',
            })

    #-----------------------------------------------------------------
    # Initial debug logging settings

    # Setup debug loggers -- start them as disabled
    debug_logger_names = [ 'mp.debug', 'mp.debug2', 'mp.debug3' ]
    debug_logger_names.extend( sub_loggers() )
    for logger_name in debug_logger_names:
        rv['loggers'][ logger_name ] = {
                            'handlers': ['null'],
                            'level': 'DEBUG',
                            'propagate': False,
                            }

    # Setup initial handlers
    debug_log_updater = _DebugLoggersDictUpdate( debug_level, rv['loggers'] )
    debug_log_updater.update_all_sub( on=sub_on )

    #-----------------------------------------------------------------
    # File Handlers

    if _log_path:
        rv['handlers']['file'] = {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'normal',
            'filename': _log_path,
            'mode': 'a',
            }
        rv['handlers']['file_mpd'] = {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'mpverbose',
            'filename': _log_path,
            'mode': 'a',
            }
        rv['handlers']['file_sql'] = {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filters': ['sql'],
            'formatter': 'normal',
            'filename': _log_path,
            'mode': 'a',
            }

    return rv


"""-----------------------------------------------------------------------
    Dynamic updating of logging
    Turn MPF logging AND external logging on and off.

    This is always run to update the logging settings at startup.
    After initialization, adjusts Python logging config values.
    NOTE -- settings.LOGGING dict is NOT changed after startup
"""

@contextmanager
def logging_update( level, verbose ):
    """
    Context manager for changing logging settings (from dialog and startup)
    Uses _DebugLoggersDictUpdate to manage logging dict handlers,
    and then updates Python logging once all updates are complete
    """

    # Get new dict based on default settings, with level changed
    new_logging_dict = logging_dict( debug_level=level, verbose=verbose )

    # Make changes to loggers within context
    updater = _DebugLoggersDictUpdate( level, new_logging_dict['loggers'] )
    yield updater

    # Update Python logging dict
    dictConfig( new_logging_dict )

class _DebugLoggersDictUpdate:

    def __init__( self, level, loggers ):
        self.debug_level = level
        self.loggers = loggers
        self.debug()

    def update_all_sub( self, on=True, **kwargs ):
        self.timing( on, **kwargs )
        self.cache( on, **kwargs )
        self.db( on, **kwargs )
        self.detail( on, **kwargs )
        self.external( on, **kwargs )

    def debug( self, on=True, **kwargs ):
        self._on_handler([
                ('mp.debug',  1, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.debug2', 2, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.debug3', 3, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('django', 1, on, '', 'WARNING', _console(), 'file', 'syslog_def'),
                ('django.security', 3, on, '', 'ERROR', _console(), 'file', 'syslog_def'),
                ('django.template', 2, on, 'WARNING', 'ERROR', _console(), 'file', 'syslog_def'),
                ('django.template', 4, on, '', 'ERROR', _console(), 'file', 'syslog_def'),
                ('django.request', 2, on, 'WARNING', 'ERROR', _console(), 'file', 'syslog_def'),
                ('django.request', 3, on, '', 'ERROR', _console(), 'file', 'syslog_def'),
                ], **kwargs)

    def timing( self, on=True, **kwargs ):
        self._on_handler([
                ('mp.timing', 1, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.timing2', 2, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.timing3', 3, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ], **kwargs)

    def cache( self, on=True, **kwargs ):
        self._on_handler([
                ('mp.cache',  1, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.cache2', 2, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.cache3', 3, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ], **kwargs)

    def db( self, on=True, **kwargs ):
        self._on_handler([
                ('django.db.backends', 1, on, '', 'WARNING', 'console_sql', 'file_sql', 'syslog_sql'),
                ('mp.db', 1, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.db2', 2, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.db3', 3, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ], **kwargs)

    def detail( self, on=True, **kwargs ):
        self._on_handler([
                ('mp.detail', 1, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.detail2', 2, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('mp.detail3', 3, on, '', '', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ], **kwargs)

    def external( self, on=True, **kwargs ):
        self._on_handler([
                ('mp.aws', 1, on, '', 'WARNING', _console_mpd(), MPD_FILE, 'syslog_mpd'),
                ('py',      1, on, '', 'WARNING', _console(), 'file', 'syslog_def'),
                ('selenium.webdriver.remote.remote_connection', 1, on, '', '',
                                            'console_spaced', 'file', 'syslog_def'),
                ('urllib3', 1, on, '', 'WARNING', _console(), 'file', 'syslog_def'),
                ('boto3', 1, on, '', 'WARNING', _console(), 'file', 'syslog_def'),
                ('botocore', 1, on, '', 'WARNING', _console(), 'file', 'syslog_def'),
                ('nose', 1, on, '', '', _console(), 'file', 'syslog_def'),
                ('paramiko',  1, on, '', '', _console(), 'file', 'syslog_def'),
                ('s3transfer',  1, on, '', '', _console(), 'file', 'syslog_def'),
                ], **kwargs)

    def _on_handler( self, handlers, file_only=False ):
        """
        Update the logger handlers based on options
        """
        for( logging_name, debug_level, on, level_on, level_off,
                console, file_handler, remote ) in handlers:

            # Setup logger if not in defaults
            if not self.loggers.get( logging_name ):
                self.loggers[ logging_name ] = { 'handlers': [],
                     'level': 'INFO', 'propagate': False }

            level = self.loggers[ logging_name ]['level']

            # Setup the potential handlers
            file_handler = file_handler if _file_enabled() else 'null'
            console_handler = 'null' if file_only or (_as_app and _syslog) else console
            syslog_handler = 'null' if file_only or not _syslog else remote
            handlers = [ console_handler, file_handler, syslog_handler ]

            # If debug on, use handlers with debug level
            if on and self.debug_level >= debug_level:
                level = level_on or 'DEBUG'

            # If debug off, either use handlers off level, or remove all handlers
            else:
                if level_off:
                    level = level_off
                    if level in [ 'WARNING', 'ERROR' ]:
                        handlers.append('email_warning')
                else:
                    handlers = ['null']

            self.loggers[ logging_name ]['level'] = level
            self.loggers[ logging_name ]['handlers'] = handlers


#--------------------------------------------------------------------
# Implementation

def _file_enabled():
    # Only provide file handler if available
    try:
        if settings.configured:
            return 'file' in settings.LOGGING.get('handlers', {})
    except ImproperlyConfigured:
        pass

def _file():
    # Support check of availability in logging setup for non-framework loggers
    return 'file' if _file_enabled() else 'null'


# Select whether to provide verbose logging
# The running as app is to prevent verbose logging when using fabric commands
def _console():
    return 'console_verbose' if _verbose and _as_app else 'console'
def _console_mpd():
    return 'console_mpverbose' if _verbose and _as_app else 'console'

