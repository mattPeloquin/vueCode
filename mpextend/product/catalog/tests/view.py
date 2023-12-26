#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Catalog view tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls(self):

        self.l("Visitor urls")
        self.sandbox_init()
        self._urls( fail=True )

        self.l("User catalog screens")
        self.login_user()
        self._urls()

        self.l("Staff catalog screens")
        self.login_owner()
        self.app_staff_urls_test('catalog')
        self._urls()

        if self.test_level:

            self.l("High and low staff")
            self.login_staff_high()
            self.app_staff_urls_test('catalog')
            self._urls()
            self.login_staff_low()
            self.app_staff_urls_test('catalog')
            self._urls()

            self.l("Root user")
            self.login_root( 30 )
            self.app_staff_urls_test('catalog')
            self.app_root_urls_test('catalog')
            self._urls()
            self.login_root()
            self.app_root_urls_test('catalog')
            self._urls()

    def _urls( self, fail=False ):

        self.get_url( reverse('profile_coupon'), fail=fail )

        rv = self.fetch_get('/api/catalog/pa_info/10', fail=fail )
        not fail and self.assertTrue( 'BuyPA_10' in rv['pa_info'] )

        rv = self.fetch_get('/api/catalog/coupon_info/Free', fail=fail )
        not fail and self.assertTrue( 'Free' in rv['coupon'] )
        rv = self.fetch_get('/api/catalog/coupon_info/DiscountPA_10', fail=fail )
        not fail and self.assertTrue( 'Half-price' in rv['coupon'] )
