#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Custom Test Runner
"""
from importlib import import_module
from django.test.runner import DiscoverRunner


class TestRunner( DiscoverRunner ):

    def __init__( self, **kwargs ):
        kwargs.update({
             'failfast': True,
             'interactive': False,
             'keepdb': False,
             'debug_mode': False,
             'debug_sql': False,
             })
        super().__init__( **kwargs )

    def run_tests( self, tests, extra_tests=None, **kwargs ):
        """
        Support better error reporting and catch cases where a test was
        added that doesn't actually exist.
        """
        try:
            # Force import of module to detect/report import errors
            path, _ = tests[0].rsplit( '.', 1 )
            import_module( path )

            num_failed = super().run_tests( tests, extra_tests, **kwargs )

            if num_failed:
                print("FAILURES: %s -> %s" % (num_failed, tests) )
            return num_failed
        except Exception as e:
            print("TEST RUN EXCEPTION: %s" % e)
            raise
