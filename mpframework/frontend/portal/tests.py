#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extended portal tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitor portal urls")
        self.sandbox_init()
        self._portal_urls( False )
        if self.test_level:
            self._staff_urls( fail=True )

        self.l("User portal urls")
        self.login_user()
        self._portal_urls()
        self._staff_urls( fail=True )

        self.login_groupadmin()
        if self.test_level:
            self._portal_urls()
            self._staff_urls( fail=True )
            self.app_root_urls_test('portal', fail=True)

            self.login_user( 22 )
            self._portal_urls()

        self.l("Staff portal urls (Sitebuilder staff can portal admin)")

        self.login_owner()
        self._portal_urls()
        self._staff_urls()
        if self.test_level:
            self.app_root_urls_test('portal', fail=True)
            self.app_root_urls_test('account', fail=True)

            self.login_staff_low()
            self._portal_urls()
            self._staff_urls()

            self.login_staff_high()
            self._portal_urls()
            self._staff_urls()

            self.l("Root portal urls")
            self.login_root()
            self._portal_urls()
            self._staff_urls()
            self.app_root_urls_test('portal')

            self.l("Root different sandbox portal urls")
            self.login_root( 30 )
            self._portal_urls()
            self._staff_urls()
            self.app_root_urls_test('portal')
            self.app_root_urls_test('account')

        self.l("Sandbox 30 portal")
        self.sandbox_init( 30, reset=True )
        self._portal_urls( False )
        self.login_user()
        self.login_user()
        self._portal_urls()
        self._staff_urls( fail=True )


    def _staff_urls( self, fail=False ):

        # Admin screens
        self.app_staff_urls_test( 'portal', fail=fail )

    def _portal_urls( self, login=True ):

        self.get_url('/')
        self.get_url('/portal')
        self.get_url('/portal/')
        self.get_url('/portal/no_link.here')
        self.get_url('/portal/no_link.here/thisContentDoesNotExist')
        self.get_url( reverse('portal_view') )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 10 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 11 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 666 }) )
        self.get_url( reverse('portal_theme', kwargs={ 'theme_id': 11 }) )
        self.get_url( reverse('portal_theme', kwargs={ 'theme_id': 12 }) )
        self.get_url( reverse('portal_theme', kwargs={ 'theme_id': 666 }) )

        # Bootstrapping API - key is only used for browser caching
        self.fetch_get( reverse('edge_bootstrap_content',
                        kwargs={ 'no_host_id': self.current_sandbox.pk }) )
        self.fetch_get( reverse('bootstrap_content') )
        self.fetch_get( reverse('bootstrap_delta') )
        self.fetch_get( reverse('bootstrap_user'), fail=not login )
        self.fetch_get( reverse('bootstrap_nocache'), fail=not login )
        url = { 'cache_url': 'DUMMY_KEY' }
        self.fetch_get( reverse('bootstrap_content', kwargs=url) )
        self.fetch_get( reverse('bootstrap_user', kwargs=url), fail=not login )

        # Portal changing
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 10 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 11 }) )
