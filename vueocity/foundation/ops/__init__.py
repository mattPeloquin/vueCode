#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Register as an extension of MPF ops
"""

from mpframework.common.app import mpAppConfig


class OpsVueocityAppConfig( mpAppConfig ):
    name = 'vueocity.foundation.ops'
    label = 'ops_vueocity'

default_app_config = 'vueocity.foundation.ops.OpsVueocityAppConfig'
