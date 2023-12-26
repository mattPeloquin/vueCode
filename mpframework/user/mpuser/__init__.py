#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extensions to Django users
"""

from mpframework.common.app import mpAppConfig


class mpUserException( Exception ):
    """
    Raise for invalid user tenancy or permissions
    """
    pass


class mpUserAppConfig( mpAppConfig ):
    name = 'mpframework.user.mpuser'
    label = 'mpuser'

    def mp_ready( self ):
        from .receivers.login_success import handle_user_logged_in
        from .receivers.login_fail import handle_user_login_failed
        from .receivers.logout import handle_user_logged_out

default_app_config = 'mpframework.user.mpuser.mpUserAppConfig'
