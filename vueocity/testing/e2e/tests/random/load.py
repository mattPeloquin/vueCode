# --- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Instead of completely random actions, focuses on looping
    through more focused sets of tasks
"""
from django.conf import settings

from mpframework.testing.e2e.actions import *
from mpframework.testing.e2e.tests.base import SystemTestCase


NUM_RUNS = int( settings.MP_TEST_RUNS ) if settings.MP_TEST_RUNS else 10


@SystemTestCase.register
class LoadRandomTests( SystemTestCase, ContentActions ):

    def test_products( self ):

        self.NUM_RUNS = NUM_RUNS

        # TBD

