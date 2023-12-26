#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Vueocity portal extensions
"""

from mpframework.common.app import mpAppConfig


class PortalVueocityAppConfig( mpAppConfig ):
    name = 'vueocity.frontend.portal'
    label = 'portal_vueocity'

default_app_config = 'vueocity.frontend.portal.PortalVueocityAppConfig'
