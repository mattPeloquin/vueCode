#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account app implements licenses tied to users through
    individual and group accounts.
"""

from mpframework.common.app import mpAppConfig


class AccountAppConfig( mpAppConfig ):
    name = 'mpextend.product.account'
    label = 'account'

    def mp_ready( self ):
        from .receivers import handle_mpuser_post_save
        from .receivers import handle_mpuser_invalidate
        from .receivers import handle_mpuser_health_check

default_app_config = 'mpextend.product.account.AccountAppConfig'
