#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Update Linux server config from django settings for non-MPF
    items like rsyslog, somaxconn, max files, etc.

    NEEDS TO RUN WITH ROOT PRIVILEGE
    CONTAINS HARDCODED AWS Linux REFERENCES
"""
import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand

from mpframework.common import log
from mpframework.common.deploy.paths import home_path
from mpframework.common.deploy.paths import deploy_path

from ..utils import template_file_write
from .config_framework import NGINX_LOG_LOCATION


# Writes rsyslog config file that is loaded at the end of
# the default config at: /etc/rsyslog.conf
RSYSLOG_CONFIG_FILE = '/etc/rsyslog.d/95-mpframework.conf'
_rsyslog_context = {
    'path_home': home_path(),
    'path_nginx_log': NGINX_LOG_LOCATION,
    'ip': settings.MP_IP_PRIVATE,
    'profile': settings.MP_PROFILE_FULL,
    'syslog': settings.MP_ROOT['SYSLOG'],
    }


class Command( BaseCommand ):
    args = ""
    help = "Linux server config"

    # The DB may not be created or accessible
    requires_model_validation = False

    def handle( self, *args, **options ):

        # Set max files for kernel and user
        max_files = settings.MP_SERVER.get('MAX_FILES')
        if max_files:
            log.info("Setting kernel and user max files:  %s", max_files)
            # Kernel addition to sysctl with reload
            subprocess.call([ 'sudo', 'bash', '-c',
                    'echo fs.file-max = {} > '
                    '/etc/sysctl.d/60-mpframework.conf'.format(max_files) ])
            subprocess.call([ 'sudo', 'sysctl', '--system' ])
            # User update
            subprocess.call([ 'sudo', 'bash', '-c',
                    "echo '* soft nofile {}' > "
                    "/etc/security/limits.d/60-mpframework.conf".format(max_files) ])
            subprocess.call([ 'sudo', 'bash', '-c',
                    "echo '* hard nofile {}' >> "
                    "/etc/security/limits.d/60-mpframework.conf".format(max_files) ])

        # Set kernel max backlog to fit uwsgi listen config
        max_conn = settings.MP_UWSGI.get('LISTEN_MAX')
        if max_conn:
            log.info("Setting somaxconn to:  %s", max_conn)
            subprocess.call([ 'sudo', 'bash', '-c',
                    'echo {} > /proc/sys/net/core/somaxconn'.format(max_conn) ])

        # rsyslog
        log_file = template_file_write( deploy_path('shell'), 'rsyslog', 'tmpl',
                    RSYSLOG_CONFIG_FILE, _rsyslog_context )
        log.info("rsyslog config file:  %s", log_file)
