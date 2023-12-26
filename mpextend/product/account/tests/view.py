#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account view tests
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh


class ViewTests( ViewTestCase ):

    def test_urls( self ):

        self.l("Visitors")
        self.sandbox_init()
        self._staff_urls( fail=True )
        self._ga_urls( fail=True )

        self.l("Normal users")
        self.login_user()
        self._staff_urls( fail=True )
        self._ga_urls( fail=True )

        self.l("GA user")
        self.login_groupadmin()
        self._staff_urls( fail=True )
        self._ga_urls( id='20' )

        self.l("Staff owner")
        self.login_owner()
        self._staff_urls()
        self._ga_urls()

        if self.test_level:

            self.login_nogroup()
            self._staff_urls( fail=True )
            self._ga_urls( fail=True )

            self.l("Low priv staff")
            self.login_staff_low()
            self._staff_urls()
            self._ga_urls()

            self.l("Other sandboxes")
            self.sandbox_init( 30, reset=True )
            self._staff_urls( fail=True )
            self._ga_urls( fail=True )

            self.l("Root user")
            self.login_root()
            self.app_root_urls_test('account')
            self._staff_urls()
            self._ga_urls()

    def _ga_urls( self, id='', fail=False ):

        def ga_url( area ):
            return reverse( 'ga_' + area, kwargs={ 'ga_id': id } )

        self.get_url( ga_url('overview'), fail=fail )
        self.get_url( ga_url('invite'), fail=fail )
        self.get_url( ga_url('users_summary'), fail=fail )
        self.get_url( ga_url('licenses'), fail=fail )
        self.get_url( ga_url('content'), fail=fail )
        self.get_url( ga_url('settings'), fail=fail )

    def _staff_urls( self, fail=False ):

        self.app_staff_urls_test( 'account', fail=fail )

        self.get_url( bh('/ad/account/apa/?free=all'), fail=fail )
        self.get_url( bh('/ad/account/apa/?free=free'), fail=fail )
        self.get_url( bh('/ad/account/apa/?free=freeall'), fail=fail )
        self.get_url( bh('/ad/account/apa/?free=purchase'), fail=fail )

        self.get_url( bh('/ad/account/apa/?ga=all'), fail=fail )
        self.get_url( bh('/ad/account/apa/?ga=0'), fail=fail )
        self.get_url( bh('/ad/account/apa/?ga=10'), fail=fail )

        self.get_url( bh('/ad/account/apa/?subscription=onetime'), fail=fail )
        self.get_url( bh('/ad/account/apa/?subscription=recurring'), fail=fail )
