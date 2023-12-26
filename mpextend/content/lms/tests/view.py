#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for content models and related application tests
"""

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls(self):
        self.l("Testing package urls")

        self.login_root()
        self.app_root_urls_test('lms')

        if self.test_level:
            self.login_root( 30 )
            self.app_root_urls_test('lms')

