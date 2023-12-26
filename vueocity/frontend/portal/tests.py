#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Vueocity portal tests
"""

from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitor portal urls")
        self.sandbox_init()
        self._portal_urls()

        if self.test_level:
            self.l("User portal urls")
            self.login_user()
            self._portal_urls()

            self.l("Staff portal urls (Sitebuilder staff can portal admin)")
            self.login_owner()
            self._portal_urls()

    def _portal_urls( self ):

        self.l("Test portal frames")
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 1010 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 1020 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 1030 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 1031 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 1040 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 1041 }) )
