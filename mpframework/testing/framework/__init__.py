#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpFramework specializations of Django automtated test support
"""

from django.conf import settings

from mpframework.common import log

from .testcase.model import ModelTestCase
from .testcase.view import ViewTestCase


class mpTestingException( Exception ):
    """
    Exception for use only with testing pathways
    Allows events such as redirects to be flagged as errors that will
    stop testing, whereas they could continue on in normal operation
    """
    pass


def requires_normal_db( fn ):
    """
    Decorator for test cases that cannot use the in-memory Django
    sqllite test DB; needed for any tests that involve threading
    """
    if not settings.MP_TEST_USE_NORMAL_DB:
        log.info("| Skipping test, needs on-disk DB: %s", fn.__name__)
        return lambda *args: True
    else:
        return fn

