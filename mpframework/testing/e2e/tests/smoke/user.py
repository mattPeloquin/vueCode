#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    High-level tests to test user functionality
"""

from mpframework.testing.e2e.tests.base import SystemTestCase


@SystemTestCase.register
class UserSmokeTests( SystemTestCase ):

    def test_visitor( self ):
        self.l("Testing Visitors")
        self.logout()
        self.go_home()
        self.try_content( access=False )

    def test_root( self ):
        self.l("Testing root user")
        self.login_user('root@mp.com')
        self.try_content()

    def test_new( self ):
        self.l("Testing new user")
        self.create_user('new@user.com')
        self.try_content( access=False )

    def try_content( self, access=True ):
        self.wait_point()
        self.get_content_text('A Test Collection').click()
        item = self.get_class('es_code_PPT-S20')
        item.click()
        self.wait_point()
        if access:
            self.sln.back()
        else:
            self.escape()
            self.wait_point()
            item.click()
