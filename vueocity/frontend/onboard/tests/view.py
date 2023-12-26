#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Onboard view tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitor urls")
        self.sandbox_init()
        self._urls( fail=True )

        if self.test_level:
            self.l("Normal user")
            self.login_user()
            self._urls( fail=True )

            self.l("Staff users")
            self.login_owner()
            self._urls()

        self.l("Root user")
        self.login_root( 30 )
        self.get_url('/bh/rt/ob/onboard')
        self._urls()

    def _urls( self, fail=False ):

        self.get_url( reverse('easy_sandbox'), fail=fail )

        self.get_url( reverse('easy_portal') )
        self.get_url( reverse('easy_portal')+'?themeTest+theme+1' )
        self.get_url( reverse('easy_portal')+'?theme=12' )
        self.get_url( reverse('easy_portal')+'?frame=11' )
        self.get_url( reverse('easy_portal_all'), fail=fail )
        self.get_url( reverse('easy_portal_next_theme') )
        self.get_url( reverse('easy_portal_next_theme') )
        for _ in range( 12 if self.test_level else 2 ):
            self.get_url( reverse('easy_portal_random') )
