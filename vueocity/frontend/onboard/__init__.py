#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Onboard app
    Supports automated creation of new providers.
"""
from django.conf import settings


def onboard_session_key( token ):
    return 'PROVIDER_ONBOARD_{}'.format( token )

def onboard_levels():
    return settings.MP_ROOT_ONBOARD_LEVELS
