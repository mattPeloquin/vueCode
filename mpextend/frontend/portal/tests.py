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
        self._portal_urls( access=False )
        self._login_urls()

        self.l("User portal urls")
        self.login_user()
        self._portal_urls()
        self._login_urls()

        if self.test_level:
            self.l("Staff portal urls (Sitebuilder staff can portal admin)")
            self.login_owner()
            self._portal_urls()
            self._login_urls()

            self.l("Sandbox 30 portal")
            self.sandbox_init( 30, reset=True )
            self.login_user()
            self._portal_urls()
            self._login_urls()

    def _portal_urls( self, access=True ):

        self.l("Test access links")
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'sku', 'evalue': 'BuyPA_10' }) )
        if access:
            apas = self.fetch_get( reverse('api_access_apas') )
            self.assertFalse( 'BuyPA_10' in apas )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'sku', 'evalue': 'FreePA_11' }) )
        if access:
            apas = self.fetch_get( reverse('api_access_apas') )
            self.assertTrue( 'FreePA_11' in apas )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'coupon', 'evalue': 'DiscountPA_10' }) )
        if access:
            apas = self.fetch_get( reverse('api_access_apas') )
            self.assertFalse( 'BuyPA_10' in apas )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'coupon', 'evalue': 'FreePA_10' }) )
        if access:
            apas = self.fetch_get( reverse('api_access_apas') )
            self.assertTrue( 'BuyPA_10' in apas )

        self.l("Portal extra links")
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'sku', 'evalue': 'BAD' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'account', 'evalue': 'BAD' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'content', 'evalue': 1001 }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'content', 'evalue': 'TESTTAG' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'content', 'evalue': 'BAD' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'coupon', 'evalue': '12' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'coupon', 'evalue': 'Free1' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'coupon', 'evalue': 'BAD' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'BAD', 'evalue': 'DATA' }) )
        self.get_url( reverse('portal_extra', kwargs={ 'ename': 'BAD', 'evalue': None }) )

        self.l("Portal page links")
        self.get_url( reverse('portal_content', kwargs={ 'content_slug': 1001 }) )
        self.get_url( reverse('portal_content', kwargs={ 'content_slug': 'testTAG' }) )
        self.get_url( reverse('portal_content', kwargs={ 'content_slug': 'BAD' }) )

        self.l("Test portal frames")
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 100 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 110 }) )
        self.get_url( reverse('portal_frame', kwargs={ 'frame_id': 111 }) )
        self.get_url( reverse('portal_content_frame', kwargs={ 'frame_id': 100, 'content_slug': 'testTAG' }) )
        self.get_url( reverse('portal_content_frame', kwargs={ 'frame_id': 110, 'content_slug': 'TESTTAG' }) )
        self.get_url( reverse('portal_content_frame', kwargs={ 'frame_id': 100, 'content_slug': 'BAD' }) )

        self.l("Test portal themes")
        self.get_url( reverse('portal_theme', kwargs={ 'theme_id': 100 }) )
        self.get_url( reverse('portal_theme', kwargs={ 'theme_id': 101 }) )
        self.get_url( reverse('portal_content_theme', kwargs={ 'theme_id': 100, 'content_slug': 'testTAG' }) )
        self.get_url( reverse('portal_content_theme', kwargs={ 'theme_id': 101, 'content_slug': 'TESTTAG' }) )
        self.get_url( reverse('portal_content_theme', kwargs={ 'theme_id': 101, 'content_slug': 'BAD' }) )

    def _login_urls( self ):

        self.get_url( reverse('login_sku', kwargs={ 'sku': 'BADTEST_123' }) )
        self.get_url( reverse('login_sku', kwargs={ 'sku': '' }) )
        self.get_url( reverse('login_coupon', kwargs={ 'coupon_slug': 'BADTEST_123' }) )
        self.get_url( reverse('login_coupon', kwargs={ 'coupon_slug': '' }) )
        self.get_url( reverse('login_content', kwargs={ 'content_slug': 'BADTEST_123' }) )
        self.get_url( reverse('login_content', kwargs={ 'content_slug': '' }) )

        # These redirect to portal if logged in
        # Success text for sandbox 20 only works if logged out
        self.get_url( reverse('login_sku', kwargs={ 'sku': 'ExpiredSku'}),
                success_text='Test for expiring', fail=True )
        self.get_url( reverse('login_coupon', kwargs={ 'coupon_slug': 'ExpiredCoupon'}),
                success_text='Test for expiring', fail=True )

        self.get_url( reverse('login_sku', kwargs={ 'sku': 'FreePA_11'}),
                success_text='Free access' )
        self.get_url( reverse('login_coupon', kwargs={ 'coupon_slug': 12 }),
                success_text='Half-price' )
        self.get_url( reverse('login_content', kwargs={ 'content_slug': 'TESTTAG'}),
                success_text='Container for content developers' )
