#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    ELB command

    Support for managing application ELBs and target groups
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from mpframework.common import log
from mpframework.common.aws import elb


class Command( BaseCommand ):

    # Can't access DB directly from remote machine, so no app model validation
    requires_model_validation = False

    help = 'Manage AWS ELBs'
    detailed_info = False

    def add_arguments( self, parser ):
        parser.add_argument( '--add', action='store_true',
            help="Remove this server from it's target group")
        parser.add_argument( '--remove', action='store_true',
            help="Add this server from it's target group")

    def handle( self, *args, **options ):
        """
        """
        if not settings.MP_CLOUD:
            raise CommandError("\nMust use this command on cloud server")
        try:
            if options.get('add'):
                self._add( *args )
            elif options.get('remove'):
                self._remove( *args )
            else:
                self.detailed_info = True
        except Exception:
            log.exception("aws_elb command")
            raise

    def _add( self, *args ):
        """
        """
        elb.add_instance()

    def _remove( self, *args ):
        """
        """
        elb.remove_instance()
