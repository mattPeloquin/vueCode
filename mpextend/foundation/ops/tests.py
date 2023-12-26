#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops extension tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitor urls")
        self.sandbox_init()
        self._portal_urls( False )

        self.l("User urls")
        self.login_user()
        self._portal_urls()

        self.l("Staff Ops URLs")
        self.login_staff()
        self._portal_urls()

        self.l("Root Ops URLs")
        self.login_root()
        self._portal_urls()

    def _portal_urls( self, login=True ):

        self.get_url( reverse('sandbox_robots'), success_text='Disallow' )
        self.get_url( reverse('sandbox_sitemap'), success_text='schemas' )
        self.get_url( reverse('sandbox_pwa_manifest'), success_text='icons' )
        self.get_url( reverse('sandbox_service_worker'), success_text='activate' )
