#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support name/value setup of logging settings
"""

from django.conf import settings


def log_setting_initial_values():
    """
    Return tuple of all logging settings
    """
    rv = [
        ('logging_debug', settings.MP_LOG_LEVEL_DEBUG_MIN ),
        ('logging_info', settings.MP_LOG_LEVEL_INFO_MIN ),
        ('logging_verbose', settings.MP_LOG_OPTIONS.get('VERBOSE') ),
        ('logging_values', False ),
        ]

    # Add sub_log names and whether the settings are in startup
    from .debug import sub_log_names
    from .debug import is_sub_log_in_settings
    rv += [ ( option_name, is_sub_log_in_settings( settings_name ) )
                for option_name, settings_name in sub_log_names
                ]

    return rv
