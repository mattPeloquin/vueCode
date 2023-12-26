#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sitebuilder tests
"""

from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitor urls")
        self.sandbox_init()
        self._staff_urls( True )

        self.l("User urls")
        self.login_user()
        self._staff_urls( True )

        self.l("Staff urls")
        self.login_staff_low()
        self._staff_urls()
        self.login_staff_high()
        self._staff_urls( high=True )


    def _staff_urls( self, fail=False, high=False ):

        self.get_url( reverse('content_tree_links'), fail=fail )
        self.get_url( reverse('content_item_links'), fail=fail )
        self.get_url( reverse('coupon_links'), fail=fail )
        self.get_url( reverse('sku_links'), fail=fail )
        self.get_url( reverse('content_apis'), fail=fail )
        # FUTURE self.get_url( reverse('manage_cnames'), fail=(fail or not high) )
