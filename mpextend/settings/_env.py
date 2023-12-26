#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Load new mpExtend settings

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""

from mpframework.common.deploy.settings import get_ecs as ecs

# Extension configuration dicts
MP_CONTENT = ecs().load_value( 'MP_CONTENT', default={} )
MP_TRACKING = ecs().load_value('MP_TRACKING', default={} )
MP_PROXY = ecs().load_value( 'MP_PROXY', default={} )
MP_REPORT = ecs().load_value('MP_REPORT', default={} )
MP_EXTERNAL = ecs().load_value('MP_EXTERNAL', default={} )
