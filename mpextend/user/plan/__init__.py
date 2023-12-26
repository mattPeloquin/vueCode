#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Plan app supports creating users plans for consuming content
"""

# Register user boostrap
from mpframework import mpf_function_group_register

def _plan_bootstrap():
    from .api import get_user_plans
    return [
        ( 'plans', get_user_plans ),
        ]

mpf_function_group_register( 'bootstrap_delta', _plan_bootstrap )


# Plan receivers
from mpframework.common.app import mpAppConfig

class PlanAppConfig( mpAppConfig ):
    name = 'mpextend.user.plan'
    label = 'plan'

    def mp_ready( self ):
        from .receivers import handle_apa_add_users

default_app_config = 'mpextend.user.plan.PlanAppConfig'
