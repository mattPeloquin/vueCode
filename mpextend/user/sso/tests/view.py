#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    SSO API tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh


class ViewTests( ViewTestCase ):

    def test_urls(self):

        self.l("Vistor content")
        self.sandbox_init()
        self._user_urls( access=False, ready=False )

        self.l("User access of user content")
        self.login_user()
        self._user_urls( access=False )

        if self.test_level:
            self.login_nogroup()
            self._user_urls( access=False )
            self.login_notready()
            self._user_urls( access=False, ready=False )

        self.l("Staff access")
        self.login_staff_low()
        self.app_staff_urls_test('sso')
        self._staff_urls()

        if self.test_level:
            self.l("Root access of user content")
            self.login_root()
            self.app_staff_urls_test('sso')
            self.app_root_urls_test('sso')
            self._user_urls()

    def _user_urls( self, access=True, ready=True ):

        rv = self.fetch_get( reverse('api_item_access'), {'id': ''}, fail=True )
        self.assertFalse( rv )


    def _staff_urls( self ):

        self.fetch_post( bh('/api/uc/update_version'), {'item_id': 1101} )
