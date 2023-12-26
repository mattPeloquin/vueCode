#--- Vueocity platform, Copyright 2021 Vueocity LLC
"""
    mpuser extensions
"""

from mpframework.common.app import mpAppConfig


class ContentExtendAppConfig( mpAppConfig ):
    name = 'mpextend.user.mpuser'
    label = 'mpuser_extend'

default_app_config = 'mpextend.user.mpuser.ContentExtendAppConfig'
