#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpUser view tests
"""
from django.urls import reverse
from django.conf import settings

from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh


class ViewTests( ViewTestCase ):
    """
    Because testing for login screen redirection is used to detect
    some view failures, user urls cannot use the app_urls_test
    introspection, because it includes the login screen.
    """

    def test_urls(self):

        self.l("Visitors")
        self.sandbox_init()
        self._user_urls( fail=True )
        self._staff_urls( fail=True )
        self.get_url( '/', login_redirect=True )
        if self.test_level:
            self.sandbox_init( 30, reset=True )
            self._user_urls()
            self._staff_urls( fail=True )

        self.l("Normal user")
        self.login_user()
        self._user_urls()
        if self.test_level:
            self._staff_urls( fail=True )

            self.redirect( settings.LOGOUT_URL )
            self.sandbox_init( reset=True )

            self.login_user( 22 )
            self._user_urls()

            self.l("Users with elevated privileges")
            self.login_groupadmin()
            self._user_urls()
            self._staff_urls( fail=True )

        self.l("Staff users")
        self.login_owner()
        self._staff_urls()
        self._user_urls()
        if self.test_level:
            self._staff_urls()
            self.login_owner( id=12, sandbox_id=30 )
            self._staff_urls()
            self._user_urls()

            self.l("Root users")
            self.login_root()
            self._staff_urls()
            self._user_urls()
            self.login_root( 30 )
            self._staff_urls()
            self._user_urls()

    def _staff_urls( self, fail=False ):

        self.app_staff_urls_test( 'mpuser', fail=fail )
        self.app_staff_urls_test( 'mpcustomer', fail=fail )

    def _user_urls( self, fail=False ):
        self.get_url('/user/login')

        self.ld("Links that require user session")

        self.get_url( reverse( 'user_verify',
                kwargs={ 'user_id_b64': 'BAD', 'extra_b64': 'BAD', 'token': 123 } ),
                success_text='link is no longer valid')

        self.app_urls_test( 'user/catalog' )
        self.app_urls_test( 'user/create' )
        self.app_urls_test( 'user/profile' )
        self.app_urls_test( 'user/security' )
        self.app_urls_test( 'user/pwd' )
        self.app_urls_test( 'user/accept_terms' )

        self.get_url( reverse( 'pwd_reset_confirm',
                kwargs={ 'user_id_b64': 'abc', 'token': '123' } ),
                success_text='link has already been used')

        self.post_url( 'user/profile',
                data={ 'first_name': 'NewName' },
                success_text='NewName', fail=fail )
        self.post_url( 'user/security',
                data={ 'update_username': True, 'email': 'new@email.com' },
                success_text='new@email.com', fail=fail )

        set_mode = reverse('api_user_delivery_mode')
        self.fetch_post( set_mode, {'delivery_mode': 'toggle'}, fail=fail )
        self.fetch_post( set_mode, {'delivery_mode': 'comp-query'}, fail=fail )
        self.fetch_post( set_mode, {'delivery_mode': ''}, fail=fail )
        self.fetch_post( set_mode, {'delivery_mode': 'toggle'}, fail=fail )
        self.fetch_post( set_mode, {'delivery_mode': 'BAD'}, fail=fail )
        self.fetch_post( set_mode, {'root': 'password'}, fail=fail )
