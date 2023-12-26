#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Placeholder for working on creating new tests
"""

from mpframework.testing.e2e import stories
from mpframework.testing.e2e.tests.base import SystemTestCase
from mpframework.testing.e2e.stories import content
from mpframework.testing.e2e.blocks import ContentBlock


@SystemTestCase.register
class DevTests( SystemTestCase ):

    def test_1( self ):
        self.owner.login()

        content.new_content_and_collections(self, 3)

