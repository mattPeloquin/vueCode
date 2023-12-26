#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logging Debug Support
"""
from django.conf import settings

from ..utils.strings import safe_unicode
from .utils import get_logger
from .utils import find_caller
from .utils import find_obj
from .utils import pretty_print


def mp_debug( logger_name, msg, *args, **kwargs ):
    """
    MPF debug and sub-debug logging calls

    Since calls to debug are wrapped, need to add support for getting
    verbose log information from the place the log was actually made

    Will not be called if debug options are not on; decisions about
    whether to avoid overhead of calling are made before calling
    """
    try:
        logger = get_logger( logger_name )

        user_name = ""
        # HACK - If a request object is available, add info
        try:
            request = find_obj('request')
            if request:
                user_name = "%s " % ( request.mpipname )
        except Exception as e:
            print( e )

        # Add extra context info to fixup where orig logging call was made
        try:
            ( file_path, line_num, func_name ) = find_caller('log.py')
            call_info = {
                # Only 'mp.debug' logging uses these tags, which are defined in mpverbose
                'mpd-path': file_path,
                'mpd-line': line_num,
                'mpd-func': func_name,
                'mpd-user': user_name,
                }
            kwargs.update({ 'extra': call_info })
        except Exception as e:
            pass

        # Pretty display data items by expanding arguments here instead of in logger
        msg_text = str( msg )
        if args:
            pretty_args = []
            for arg in args:
                try:
                    arg = pretty_print( arg )

                    if not isinstance( arg, float ):
                        arg = str( arg )

                    pretty_args.append( arg )

                except Exception as e:
                    pretty_args.append( "DEBUG_ARG_EXC(%s -> %s)" % ( arg, e ) )

            msg_text = ( msg % tuple( pretty_args ) )

        # Make the logging call
        logger.debug( msg_text, **kwargs )

        # Return the text in case it will be shown elsewhere
        return msg_text

    except Exception as e:
        error = "DEBUG_LOG_ERROR {} -> {}, {}".format(
                    safe_unicode(e), safe_unicode(msg), safe_unicode(args) )
        get_logger('mp').info( error )
        #import traceback
        #traceback.print_stack()


#--------------------------------------------------------------------

def set_subdebug( module ):
    """
    When the sub logging methods are added, they are always called;
    whether they are logged is controlled by the logger settings for each
    """
    debug_on = module['_debug_on']

    # Use closure to create delegation functions for calling different loggers
    def _create_sub_debug_call( logger_name ):
        def _sub_debug_call( msg, *args, **kwargs ):
            if debug_on:
                return mp_debug( logger_name, msg, *args, **kwargs )
        return _sub_debug_call

    # Add logging method to the module
    for logger_name in sub_loggers():
        name = logger_name.split('.')[1]
        module[ name ] = _create_sub_debug_call( logger_name )

"""
    Create specialized debug loggers for better debug filtering
    Each item in list below will be made into a log.xxx module function
"""
_SUB_LOGGERS = (
        'mp.timing',
        'mp.timing2',
        'mp.timing3',
        'mp.cache',
        'mp.cache2',
        'mp.cache3',
        'mp.db',
        'mp.db2',
        'mp.db3',
        'mp.detail',
        'mp.detail2',
        'mp.detail3',
        'mp.aws',
        )
def sub_loggers():
    return _SUB_LOGGERS

"""
    Sub logging option management

    Sub logging options can be set through settings and through the
    global options mechanism
"""

# The first element in the tuples below is the log option name, the second
# is the shortened name used in the MP_LOG_SUB setting
sub_log_names = (
    ('log_timing', 'timing'),
    ('log_cache', 'cache'),
    ('log_db', 'db'),
    ('log_detail', 'detail'),
    ('log_external', 'external'),
    )

def is_sub_log_in_settings( name ):
    """
    Is a sub logging category selected in startup settings?
    If called before settings are available, return true
    """
    return bool( name in settings.MP_LOG_SUB or settings.MP_LOG_ALL )

