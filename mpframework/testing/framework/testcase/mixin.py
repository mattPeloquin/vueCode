#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Mixin used for all MPF base test cases
"""
from traceback import format_tb
from django.conf import settings
from django.test.utils import override_settings
from django.core.mail.message import make_msgid
from django.core.mail.backends.locmem import EmailBackend

from mpframework.common import log
from mpframework.common.logging.setup import logging_update
from mpframework.common.deploy.debug import trace_on
from mpframework.common.deploy.debug import trace_off
from mpframework.common.cache.clear import clear_local_buffer
from mpframework.common.cache.clear import clear_cache


class TestEmailBackend( EmailBackend ):
    """
    Call to socket.getfqdn() used in default locmem test email can be very
    slow sometimes (seconds for first email in each test case).
    Short-circuit here by setting a dummy message-id header
    """
    def send_messages( self, messages ):
        for message in messages:
            if 'message-id' not in message.extra_headers:
                message.extra_headers['Message-ID'] = make_msgid( domain='TEST_EMAIL' )
        return super().send_messages( messages )


class mpTestCaseMixin:
    """
    Behavior mixed in to Model, View, and Web test cases
    inherited from Python and Django unittest TestCases

    Need to use override_settings decorator to ensure settings in
    Django code such as DB logging, and also need to explicitly
    reset the settings to their config settings
    """

    # Override Debug setting, to counteract Djano's forcing to False
    DEBUG_SETTING = settings.DEBUG

    # Shared data used in tests
    fixtures = settings.MP_TEST_FIXTURES
    TEST_PWD = 'mptest'

    # Numeric setting to allow test cases to adjust breadth/depth
    test_level = settings.MP_TEST_LEVEL

    # Provide access in test case to clear caching -- should only
    # be used in special cases, as problems indicate invalidation issue
    @staticmethod
    def clear_local_buffer():
        return clear_local_buffer()

    """-------------------------------------------------------------------
        Misc
    """

    # Make logging short to encourage log lines vs. comments to
    # describe test flow

    @staticmethod
    def l( msg, *args ):
        log.info("| {}".format(msg), *args)

    @staticmethod
    def ld( msg, *args ):
        log.debug(">   {}".format(msg), *args)

    @staticmethod
    def ls( msg, *args ):
        log.detail3(">   {}".format(msg), *args)

    @staticmethod
    def lv( msg, *args ):
        log.debug_values(">   {}".format(msg), *args)

    # Convenience methods

    @staticmethod
    def condition_in_all( items, condition ):
        return all( bool(item()) == condition for item in items )

    @staticmethod
    def wait_for_threads( threshold=1 ):
        # Use when async tasks need to complete
        # HACK - assume 1 main thread is all that should be running
        import time
        import threading
        def _wait( msg ):
            log.info("| WAITING for threads {}".format( msg ) )
            time.sleep( 0.5 )
        while len( threading.enumerate() ) > threshold:
            _wait( len( threading.enumerate() ) )

    """-------------------------------------------------------------------
        Setup and Teardown
        Much of the additional behavior added is log management
    """

    @classmethod
    def setUpClass( cls ):
        super().setUpClass()

        # Preserve debug settings
        # This needs to be called after call to Django test base class to
        # reset the debug settings to what config settings are set to
        settings.DEBUG = cls.DEBUG_SETTING

        # During testing all caching happens in shared memory cache,
        # so this will clear everything
        clear_cache('default')

        cls.l("")
        cls.l(">>>  %s  <<<", cls.__name__)
        cls.l("Debug Mode: %s, Debug Log: %s",
                    settings.DEBUG, settings.MP_LOG_LEVEL_DEBUG_MIN)
        cls.l("Fixtures: %s", cls.fixtures)

    @classmethod
    def tearDownClass( cls ):
        super().tearDownClass()

    def setUp( self ):
        """
        Make logging and other mpFramework specific adjustments
        """
        super().setUp()

        _set_test_logging()
        test_name = self.id().split('.')
        self.l("")
        self.l(">>> %s -> %s", test_name[-1], '.'.join( test_name ) )
        self.l("")

        # Turn on tracing for the test code
        # Try to do this as late as possible to avoid noise from test framework
        if settings.MP_LOG_OPTIONS.get('CODE_TRACE'):
            trace_on()

    def tearDown( self ):
        """
        Turn off code tracking and detailed logging between test runs,
        in particular to avoid SQL from fixture load
        """
        trace_off()
        with logging_update( 0, False ) as logging:
            logging.update_all_sub()
        super().tearDown()

    def load_content_models( self ):
        """
        Run before tests that need Django's content models table fixed up
        """
        from mpframework.content.mpcontent.models import BaseItem
        for item in BaseItem.objects.filter():
            item.downcast_type

    def __call__( self, result=None ):
        """
        Support sub event and trace logging as it happens
        """
        if result:
            self._call_logging( result )
        super().__call__( result )

    def _call_logging( self, result ):
        """
        Fixup the result object used to run tests to support sending
        error information to the sub log as it happens.
        """
        if not getattr( result, 'logging_fixed_up', None ):
            from .. import mpTestingException

            def fixup( method_name ):
                orig = getattr( result, method_name )

                def new_fn( test, err ):
                    e_type, txt, trace = err
                    tl = format_tb(trace)
                    trace_str = ""

                    # Put traceback inline in logging if not testing exception
                    if settings.DEBUG and mpTestingException != e_type:
                        trace_str = "\n%s\n" % tl

                    self.l("\n%s\n\n%s: %s\n%s\n%s",
                           ">" * 50,
                           method_name, e_type,
                           txt,
                           trace_str )

                    orig( test, err )

                result.__dict__[ method_name ] = new_fn

            fixup('addError')
            fixup('addFailure')
            result.__dict__[ 'logging_fixed_up' ] = True


def _set_test_logging():
    """
    Set global logging to test parameters during test cases
    """
    log.set_log_level( settings.MP_LOG_LEVEL_INFO_MIN,
                settings.MP_LOG_LEVEL_DEBUG_MIN, values=False )

    # Read the sub-logging settings
    # HACK - This creates dependency on an ops module, but
    # worth it because ops knows how to read sub logging config settings
    from mpframework.foundation.ops.logging_setup import get_sub_logging_settings
    sublogging_on = get_sub_logging_settings()

    # Now update sub logging to use in test run based on config settings
    with logging_update( settings.MP_LOG_LEVEL_DEBUG_MIN,
                         settings.MP_LOG_OPTIONS.get('VERBOSE') ) as logging:

        # Some logging always on in file, on screen based on settings
        logging.timing( file_only = not sublogging_on['timing'] )
        logging.cache( file_only = not sublogging_on['cache'] )
        logging.db( file_only = not sublogging_on['db'] )

        # Other logging turned on in file/screen based on settings
        logging.external( on=sublogging_on['external'], file_only=False )
