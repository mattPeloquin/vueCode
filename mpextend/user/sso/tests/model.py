#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for user content models and related application tests
"""

from mpframework.testing.framework import ModelTestCase



class ModelTests( ModelTestCase ):

    def test_sso( self ):
        """
        TBD sso
        """
        user = self.login_user()

