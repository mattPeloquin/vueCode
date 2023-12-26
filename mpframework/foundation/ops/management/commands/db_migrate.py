#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Non-destructive DB create/migrate Django command

    Django already creates DB for SQLite. To provide similar
    semantics for mySQL, wrapping migrate with a create DB call
"""
from django.conf import settings
from django.core.management.commands.migrate import Command as MigrateCommand

from mpframework.common import log
from mpframework.common.db.mysql import create_mysql_db


class Command( MigrateCommand ):
    """
    Add current DB name from settings into the shell command
    """
    help = 'Runs Django migrate, creating mySql DB if not already created'

    # The DB may not be created or accessible
    requires_model_validation = False

    def handle( self, *args, **options ):
        """
        Create DB if necessary (option defaults to 'default')
        Then delegate to Django migrate
        """
        db_name = options.get('database')

        try:
            db_info = settings.DATABASES[db_name]
        except KeyError:
            log.error("%s not in settings.DATABASES: %s", db_name, settings.DATABASES)
            raise

        if 'mysql' in db_info['ENGINE']:
            create_mysql_db( db_info )

        try:
            super().handle( *args, **options )

        except Exception:
            log.exception("Exception in db_migrate")
            raise
