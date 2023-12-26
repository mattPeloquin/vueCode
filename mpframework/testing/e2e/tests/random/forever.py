#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Main random test script that pulls together all random pieces
"""
import random

from mpframework.testing.e2e.actions import *
from mpframework.testing.e2e.tests.base import SystemTestCase


@SystemTestCase.register
class ForeverRandomTests( SystemTestCase, ContentActions ):

    def test_forever( self ):

        # Only run embedded items once
        self.NUM_RUNS = 1

        while True:

            # Do a random action
            action = random.choice( self.actions )
            getattr( self, action )()
