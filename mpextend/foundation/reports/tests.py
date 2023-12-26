#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Reporting tests

    Accessing invalid reports can return 200, so need to look at
    some of the returned metadata to see if report "failed"
"""

import time

from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls( self ):
        self.load_content_models()

        if self.test_level:
            self.l("Visitor reporting")
            self.sandbox_init()
            self._ga_urls( hard_fail=True )
            self._staff_urls( hard_fail=True )
            self.l("User reporting")
            self.login_user()
            self._ga_urls( hard_fail=True )
            self._staff_urls( hard_fail=True )

        self.l("GA reporting")
        self.login_groupadmin()
        self._ga_urls()
        self._staff_urls( hard_fail=True )

        if self.test_level:
            self.l("Owner reports")
            self.login_owner()
            self._staff_urls()
            self._ga_urls()
            self._ga_urls( id=30, hard_fail=True )

        self.l("Low priv staff reports")
        self.login_staff_low()
        self._staff_urls()
        self._ga_urls()
        if self.test_level:

            self._ga_urls( id=30, hard_fail=True )

            self.l("High priv staff reports")
            self.login_staff_high()
            self._staff_urls()
            self._ga_urls()

            self.l("Root reports")
            self.login_root()
            self._staff_urls()
            self._ga_urls()

            self.l("Root sandbox reports")
            self.login_root( 30 )
            self._ga_urls( id=30 )
            self._staff_urls()

        self.wait_for_threads()

    def _test_report( self, name, fail, hard_fail, success, *args, **kwargs ):
        values = self.fetch_get( reverse( name, args=args, kwargs=kwargs ),
                               fail=hard_fail, success_text=success )
        if fail and values:
            raise Exception("Report should not have started")
        elif not hard_fail and not fail and not values:
            raise Exception("Report failed to start")

    def _ga_urls( self, id=20, fail=False, hard_fail=False ):

        def _test_ga( name, success='ga@acme.com' ):
            self._test_report( name, fail, hard_fail, success, ga_id=id )

        _test_ga('ga_summary_csv')
        _test_ga('ga_purchases_csv')
        _test_ga('ga_content_top_csv')
        _test_ga('ga_content_csv')

    def _staff_urls( self, fail=False, hard_fail=False ):

        def _test_staff( name, start=None, success='user@acme.com' ):
            args = [start] if start else []
            self._test_report( name, fail, hard_fail, success, *args )

        _test_staff('users_summary_csv')
        _test_staff('users_content_top_csv')
        _test_staff('users_content_csv')
        _test_staff( 'users_licenses_csv', None, success='nogroup@acme.com' )

        _test_staff( 'users_summary_csv', 1 )
        _test_staff( 'users_content_csv', 3 )
        _test_staff( 'users_summary_csv', 2345 )
