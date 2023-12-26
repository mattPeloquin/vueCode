#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Config file fixup for nginx and uwsgi
    Usually run in fabric commands before starting processes to
    setup config files from templates.

    CONTAINS HARDCODED CONFIG REFERENCES
"""
from random import randint
from django.conf import settings
from django.core.management.base import BaseCommand

from mpframework.common import log
from mpframework.common.utils import join_urls
from mpframework.common.deploy.paths import home_path
from mpframework.common.deploy.paths import temp_path
from mpframework.common.deploy.paths import work_path
from mpframework.common.deploy.paths import deploy_path

from ..utils import template_file_write


# Put nginx files in conventional location for easy use with logrotate
NGINX_LOG_LOCATION = '/var/log/nginx/'


class Command( BaseCommand ):
    args = ""
    help = "Write nginx and uwsgi config files"

    # The DB may not be created or accessible
    requires_model_validation = False

    def handle( self, *args, **options ):
        handle_nginx( *args, **options )
        handle_uwsgi( *args, **options )

"""---------------------------------------------------------------------
    uWsgi
"""

def handle_uwsgi( *args, **options ):
    uwsgi_file = template_file_write( deploy_path('uwsgi_config'), 'uwsgi',
                                        'tmpl', 'yaml', _uwsgi_context )
    log.info("\nWriting uWSGI config file:  %s", uwsgi_file)

# Setup context with UWSGI info, paths and settings settings needed to render
# and calculate values that can't be done in config templates
MP_UWSGI = settings.MP_UWSGI

total = MP_UWSGI['MAX_REQUESTS']
adj = randint( -int(MP_UWSGI['MAX_REQUESTS_RANDOM']),
                int(MP_UWSGI['MAX_REQUESTS_RANDOM']) )
total = max( MP_UWSGI['MAX_REQUESTS_MIN'], total + adj )
MP_UWSGI['MAX_REQUESTS'] = total

_uwsgi_context = {
    'path_home': home_path(),
    'path_uwsgi': home_path('uwsgi'),
    'DEBUG':  settings.DEBUG,
    'MP_UWSGI':  MP_UWSGI,
    }

"""---------------------------------------------------------------------
    Nginx
"""

def handle_nginx( *args, **options ):
    # Files generated here follow convention of a "config_xxx" prefix
    log.info("\nCreating nginx conf files:")
    _write_conf_files( nginx_context(), [
        "inc_main",
        "inc_proxy_protected",
        "inc_proxy_public",
        "inc_proxy",
        "inc_django",
        "inc_uwsgi",
        "inc_server",
        "inc_http",
        "dev",
        "prod",
        ])

def nginx_context():
    """
    Context used to create nginx config files
    """
    rv = {
        's': settings,

        # Convert tuples to strings
        'URL_NGINX_MAIN': '|'.join( settings.MP_URL_NGINX['MAIN'] ),
        'URL_NGINX_PUBLIC': '|'.join( settings.MP_URL_NGINX['PUBLIC_CACHE'] ),
        'URL_NGINX_ADMIN': '|'.join( settings.MP_URL_NGINX['ADMIN'] ),
        'URL_NGINX_ROOT_PASS': '|'.join( settings.MP_URL_NGINX['ROOT_PASS'] ),
        'PROTECTED_VIDEO_TYPES': '|'.join( settings.MP_FILE['VIDEO_TYPES'] ),
        'PROTECTED_NGINX_PASS_TYPES': '|'.join( settings.MP_PROTECTED['NGINX_PASS_TYPES'] ),

        # Path locations nginx needs to know
        'path_work': work_path(),
        'path_nginx': home_path('nginx'),
        'path_nginx_temp': temp_path('nginx'),
        'path_uwsgi': home_path('uwsgi'),

        # Path locations that are built in templates
        # Note platform order is reversed to make sure root checked first
        'path_root': '/home/ec2-user/',
        'path_playpen': work_path( settings.MP_PLAYPEN ),
        'path_public_static': work_path( settings.MP_PUBLIC_STATIC_FOLDER ),
        'error_log': _error_log,
        'access_log': _access_log,
        'garbage_log': _garbage_log,
        'health_log': _health_log,
        }

    # Servers that need to be designated in nginx as legitimate hosts;
    # Use the ".xxx" notation to get both xxx and *.xxx in the match
    rv.update({ 'servername': '.{}'.format( settings.MP_ROOT['HOST'] ) })
    for subdomain in settings.MP_ROOT['HOST_SUBDOMAINS']:
        rv[ 'servername_{}'.format( subdomain ) ] = '.{}.{}'.format(
                subdomain, settings.MP_ROOT['HOST'] )

    # Puts all MP_URL_*** settings into dict to be added to context
    for prefix_name in filter( lambda setting:
            setting.startswith('MP_URL_'), dir(settings) ):
        rv[ prefix_name ] = getattr( settings, prefix_name, '' )

    return rv

def _write_conf_files( context, file_names ):
    for file_name in file_names:
        out_name = template_file_write( deploy_path('nginx'), file_name,
                    'tmpl', 'conf', context )
        log.info("  %s", out_name)

"""
    Log file pathing
    Provide fixups for default and specific locations for nginx error_log
    and access_log directives. Note that access_log allows for different
    formatting, while error log only allows for setting severity level.
"""

if settings.MP_LOG_OPTIONS.get('SYSLOG'):
    syslog = 'syslog:server=unix:/dev/log,tag=nginx,facility=local6,nohostname'
    error_location = syslog
    access_location = syslog + ' default_format'
else:
    error_location = NGINX_LOG_LOCATION + 'error.log'
    access_location = NGINX_LOG_LOCATION + 'access.log default_format buffer=1m flush=1s'

_access_log = access_location
_health_log = '{} default_format buffer=32k flush=10s'.format(
        NGINX_LOG_LOCATION + 'health.log')
_garbage_log = '{} default_format buffer=32k flush=10s'.format(
        NGINX_LOG_LOCATION + 'garbage.log')

# Full debug logging support, needs debug build of nginx.
error_level = 'info'
_FORCE_DEBUG_LOG = False
if log.debug_on() and _FORCE_DEBUG_LOG:
    error_level = 'debug'
_error_log = '{} {}'.format( error_location, error_level )
