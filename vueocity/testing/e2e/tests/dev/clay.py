#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Clay test sandbox
"""

from mpframework.testing.e2e import stories
from mpframework.testing.e2e.tests.base import SystemTestCase
from mpframework.testing.e2e.blocks import collections
from mpframework.testing.e2e.blocks import content

@SystemTestCase.register
class ClayTests( SystemTestCase ):


    def test_1( self ):
        self.owner.login()

