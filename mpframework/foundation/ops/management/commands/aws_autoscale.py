#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Autoscale command

    HACK - used to get IPs for autoscale groups
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from mpframework.common import log
from mpframework.common.deploy.paths import autoscale_ip_file_path
from mpframework.common.aws.autoscale import get_autoscale
from mpframework.common.aws.autoscale import log_asg_info


class Command( BaseCommand ):

    # Can't access DB directly from remote machine, so don't want app model validation
    requires_model_validation = False

    help = 'AWS autoscale cluster utils'
    detailed_info = False

    def add_arguments( self, parser ):
        parser.add_argument( '--tag', default='' )
        parser.add_argument( '--ips', action='store_true',
            help="Get list of current AS cluster IPs")

    def handle( self, *args, **options ):
        """
        The name of the autoscale cluster is the profile name plus and
        optional additional name passed in here
        """
        #if not settings.MP_CLOUD:
            #raise CommandError("\nMust use this command with an AWS profile")
        try:
            tag = options.get('tag', '')
            if options.get('ips'):
                self._put_ips( tag )
            else:
                self._list_info( True )
        except Exception:
            log.exception("aws_autoscale command")
            raise

    def _put_ips( self, tag ):
        """
        Writes current ASG instance IPs into a local temp file.

        HACK - this is solely for use by fabric autoscale command, which
        is designed to be chained with other commands to affect the current
        autoscale group.

        HACK SCALE - this has race conditions related to new servers being created
        that won't get picked up in the command. Shouldn't matter for the
        most common use case, which is updating from hg, since any new
        instances will be doing that themselves.
        """
        log.info("Get Autoscale ips for: %s%s", settings.MP_PROFILE, tag)
        file_path = autoscale_ip_file_path( settings.MP_PROFILE, tag )
        log.info("Putting Autoscale ips in: %s", file_path)
        ips = str( get_autoscale( settings.MP_PROFILE, tag ).get_public_ips() )

        log.info("    %s", ips)
        with open( file_path, 'w' ) as ip_file:
            ip_file.write( ips )

    def _list_info( self ):
        """
        List all AS groups on AWS for this root
        """
        log.info("Current Autoscale Groups:")
        log_asg_info( self.detailed_info )
