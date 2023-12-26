#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Wrap fixture loading to use mpFramework config settings

    This is only intended for test scenarios, bootstrapping a new DB
    and loading data from migration/operations does not use this
"""
from django.conf import settings
from django.core.management.commands.loaddata import Command as LoaddataCommand

from mpframework.common import log


class Command( LoaddataCommand ):
    """
    Add current DB name from settings into the shell command
    """
    help = 'Runs Django loaddata with fixtures dervied from mpFramework settings'

    # This may not be possible if DB created/accessible remotely
    requires_model_validation = False

    def handle( self, *fixtures, **options ):
        # This should only be used for testing, production loading is separate
        if settings.MP_PROFILE_IS_PROD and settings.MP_CLOUD:
            log.warning("CANNOT LOAD FIXTURE DATA for a production DB")
            return

        log.info("Loading fixtures:\n   %s", "\n   ".join([f for f in fixtures]))
        log.info("From:\n   %s", "\n   ".join([f for f in settings.FIXTURE_DIRS]))
        try:
            super().handle( *fixtures, **options )

        except Exception:
            log.exception("Exception in db_load")
            raise

    def run_from_argv( self, argv ):
        """
        Override default loaddata to setup fixtures from config settings
        if none were provided
        """
        if len( argv ) < 3:
            argv.extend([ fixture + ".yaml" for fixture in settings.MP_TEST_FIXTURES ])

        super().run_from_argv( argv )
