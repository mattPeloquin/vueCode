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
        self._urls()

        self.l("Staff urls")
        self.login_staff_low()
        self._urls()


    def _urls( self, fail=False ):

        rv = self.fetch_get( reverse( 'api_payment_start',
                    kwargs={'apa_id': 20} ), fail=fail )
        if not fail:
            self.assertTrue( 'stripe_connect' in rv )
            self.assertTrue( '20' in rv )

        self.get_url( reverse( 'payment_start', kwargs={'apa_id': 20} ), fail=fail )

        self.get_url( reverse( 'payment_error', args=('paypal_nvp',) ), fail=fail )
        self.get_url( reverse( 'payment_cancel', args=('paypal_nvp',) ), fail=fail )
        self.get_url( reverse( 'payment_finish', args=('paypal_nvp',) ), fail=fail )

        self.get_url( reverse( 'payment_error', args=('stripe_connect',) ), fail=fail )
        self.get_url( reverse( 'payment_cancel', args=('stripe_connect',) ), fail=fail )
        self.get_url( reverse( 'payment_finish', args=('stripe_connect',) ), fail=fail )

        self.get_url( reverse( 'payment_error', args=('BAD',) ), fail=True )
        self.get_url( reverse( 'payment_cancel', args=('BAD',) ), fail=True )
        self.get_url( reverse( 'payment_finish', args=('BAD',) ), fail=True )
