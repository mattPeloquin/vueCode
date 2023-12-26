#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extended content models and functionality
"""

from mpframework.common.app import mpAppConfig


class ContentExtendAppConfig( mpAppConfig ):
    name = 'mpextend.content.mpcontent'
    label = 'mpcontent_extend'

default_app_config = 'mpextend.content.mpcontent.ContentExtendAppConfig'
