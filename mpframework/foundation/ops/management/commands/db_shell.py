#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django's DB shell with more error reporting
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections


class Command( BaseCommand ):
    help = "Opens command line shell for DB (default or named in settings)"

    requires_system_checks = False

    def add_arguments( self, parser ):
        parser.add_argument(
            '--db', action='store', dest='db', default=DEFAULT_DB_ALIAS,
            help='DB onto which to open shell',
        )

    def handle( self, *args, **options ):
        connection = connections[ options['db'] ]
        try:
            connection.client.runshell( args )
        except OSError as e:
            raise CommandError( 'Error opening connection: %r ' % e )
