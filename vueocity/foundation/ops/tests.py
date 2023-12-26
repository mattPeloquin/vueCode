#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Payment tests
"""

from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitor urls")
        self.sandbox_init()
        self._urls( fail=True )

        self.l("User urls")
        self.login_user()
        self._urls( fail=True )

        self.l("Staff urls")
        self.login_staff_high()
        self._urls( fail=True )

        self.l("Owner urls")
        self.login_owner()
        self._urls()

        self.l("Root urls")
        self.login_root()
        self._urls()
        self.get_url( reverse('ops_events') )

    def _urls( self, fail=False ):

        self.get_url( reverse('owner_billing'), fail=fail )
