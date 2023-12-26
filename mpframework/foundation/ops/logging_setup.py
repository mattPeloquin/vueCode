#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Set logging from polling thread
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common import sys_options
from mpframework.common.db import db_connection_retry
from mpframework.common.logging.setup import logging_update
from mpframework.common.logging.debug import sub_log_names
from mpframework.common.logging.debug import is_sub_log_in_settings


def get_sub_logging_settings():
    """
    Return a dict with option names for each sub logger along
    with the current on/off value

    Current value can be set either by initial settings or via
    the system debug option settings

    This is used below, and to setup test logging
    """
    logging_on = {}

    # Setup initial logging options
    # If running as app, get logging settings from DB, otherwise get from settings
    for option_name, setting_name in sub_log_names:
        logging_on[ setting_name ] = True
        if settings.MP_IS_RUNNING_APP:
            logging_on[ setting_name ] = getattr( sys_options, option_name )()
        else:
            logging_on[ setting_name ] = is_sub_log_in_settings( setting_name )

    return logging_on


@db_connection_retry
def set_logging():
    """
    Called from update_process thread
    """

    # The settings.MP_LOG_XXX values for a server don't change after
    # it is started, but can override the settings after start
    debug_level = max( sys_options.logging_debug(),
                        settings.MP_LOG_LEVEL_DEBUG_MIN )
    info_level = max( sys_options.logging_info(),
                        settings.MP_LOG_LEVEL_INFO_MIN )
    verbose = sys_options.logging_verbose()
    values = sys_options.logging_values()

    log.set_log_level( info_level, debug_level, values )

    # Turn on specific debug settings
    if debug_level:
        logging_on = get_sub_logging_settings()
        with logging_update( debug_level, verbose ) as logging:
            logging.timing( on=logging_on['timing'] )
            logging.db( on=logging_on['db'] )
            logging.cache( on=logging_on['cache'] )
            logging.external( on=logging_on['external'] )
