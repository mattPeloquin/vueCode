#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User tracking view tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitor urls")
        self.sandbox_init()
        self._urls( True )
        self._staff_urls( True )

        self.l("User urls")
        self.login_user()
        self._urls()
        self._staff_urls( True )

        self.l("Staff urls")
        self.login_staff_low()
        self._urls()
        self._staff_urls()

        # Tracking API -- assume one login above
        tracking = self.fetch_get( reverse('api_tracking_active_users') )
        for ut in tracking['user_trackings']:
            if ut['name'].startswith('User20'):
                self.assertTrue( ut['logins'] == 1 )

    def _urls( self, fail=False ):

        self.get_url( reverse('profile_history'), fail=fail )

        self.fetch_post('/api/user/ui_state',
                      {'ui_state': '{"dummy_json": "ui_state TEST"}'}, fail=fail )
        self.fetch_post('/api/user/ui_state', {'ui_state': 'BAD'}, fail=fail )
        self.fetch_post('/api/user/ui_state', {'root': 'password'}, fail=fail )

    def _staff_urls( self, fail=False ):

        self.get_url( reverse('user_dashboard'), fail=fail )
