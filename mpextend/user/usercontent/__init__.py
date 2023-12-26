#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User-content application
"""

# Register user boostraps - the bootstrap calls are cached, which
# is how timewin is managed
from mpframework import mpf_function_group_register

def _user_timewin():
    from .api.bootstrap import user_tops
    from .api.bootstrap import user_items
    return [
        ( 'trees_user', user_tops ),
        ( 'items_user', user_items ),
        ]
mpf_function_group_register( 'bootstrap_user_timewin', _user_timewin )

def _user_delta():
    from .api.bootstrap import user_tops
    from .api.bootstrap import user_items
    return [
        ( 'trees_user_delta', user_tops ),
        ( 'items_user_delta', user_items ),
        ]
mpf_function_group_register( 'bootstrap_user_delta', _user_delta )
