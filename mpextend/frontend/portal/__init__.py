#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extended portal functionality
"""

from mpframework.common.app import mpAppConfig


class ProtalExtendAppConfig( mpAppConfig ):
    name = 'mpextend.frontend.portal'
    label = 'portal_extend'

default_app_config = 'mpextend.frontend.portal.ProtalExtendAppConfig'
