#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Register as an extension of sitebuilder app
"""

from mpframework.common.app import mpAppConfig


class SitebuilderExtendAppConfig( mpAppConfig ):
    name = 'mpextend.frontend.sitebuilder'
    label = 'sitebuilder_extend'

default_app_config = 'mpextend.frontend.sitebuilder.SitebuilderExtendAppConfig'
