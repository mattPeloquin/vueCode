#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal tests
"""

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_sitebuilder( self ):

        self.l("Sitebuilder staff")
        self.login_staff_high()
        self._staff_urls()

        if self.test_level:

            self.l("Sitebuilder Visitor")
            self.sandbox_init()
            self._staff_urls( fail=True )

            self.l("Sitebuilder User")
            self.login_user()
            self._staff_urls( fail=True )

    def _staff_urls( self, fail=False ):

        self.app_staff_urls_test( 'sitebuilder', fail=fail )
