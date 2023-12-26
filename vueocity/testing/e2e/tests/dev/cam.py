#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Cam test sandbox
"""

from mpframework.testing.e2e import stories
from mpframework.testing.e2e.tests.base import SystemTestCase

from mpframework.testing.e2e.blocks import ContentBlock


@SystemTestCase.register
class CamTests( SystemTestCase ):

    def test_1( self ):
        self.owner.login()

        cb = ContentBlock( self )
        cb.go_edit()

