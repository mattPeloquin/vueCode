#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Settings read from configuration and environment

    DESIGNED TO BE * IMPORTED BY settings.__init__.py

    Values are loaded from environment and yaml config files (environment trumps)
    The yaml config env mirror the run-time environments (dev, prod), with
    the environment controlled by the MP_PROFILE environment variable.
"""
import time
import socket

from mpframework.common.deploy import is_prod_profile
from mpframework.common.deploy.settings import get_ecs as ecs
from mpframework.common.deploy.platforms import all_platforms
from mpframework.common.deploy.platforms import root_name
from mpframework.common.deploy.paths import work_path
from mpframework.common.aws.ec2 import aws_instance_info
from mpframework.common.aws.secrets import aws_email_credentials
from mpframework.common.utils import join_urls


#--------------------------------------------------------------------
# Key resources

# General root values
MP_ROOT = ecs().load_value('MP_ROOT')

# External services
MP_ROOT_CACHE = ecs().load_value('MP_ROOT_CACHE')
MP_ROOT_URLS = ecs().load_value('MP_ROOT_URLS')

# Key server and system load configuration
MP_SERVER = ecs().load_value('MP_SERVER')
MP_NGINX = ecs().load_value('MP_NGINX')
MP_UWSGI = ecs().load_value('MP_UWSGI')
MP_CACHE_AGE = ecs().load_value('MP_CACHE_AGE')
MP_TUNING = ecs().load_value( 'MP_TUNING', default={} )

#--------------------------------------------------------------------
# Platform and profile setup

# Set during startup by manage.py
MP_DEVWEB = ecs().load_bool( 'MP_DEVWEB', suppress=True )
MP_WSGI = ecs().load_bool( 'MP_WSGI', suppress=True )
MP_COMMAND = ecs().load_bool( 'MP_COMMAND', suppress=True )

# Default platforms set by MP_PLATFORMS env variable, available
# subfolders, or root - see all_platforms.
MP_PLATFORMS = all_platforms()
MP_PLATFORMS_ROOT = root_name()

# Profile and optional add-on tag always set in environment or by fabric
MP_PROFILE = ecs().load_value( 'MP_PROFILE', default='local', suppress=True )
MP_PROFILE_TAG = ecs().load_value( 'MP_PROFILE_TAG', default='' )
MP_PROFILE_FULL = '{}{}'.format( MP_PROFILE, MP_PROFILE_TAG )

# Current revision number for the code, used in some caching and versioning
MP_CODE_CURRENT = ecs().load_value( 'MP_CODE_CURRENT', default='' )

# May use start time in some cases to differentiate server runs
MP_TIME_START = str( time.time() )
MP_TIME_STAMP = MP_TIME_START[-6:].replace( '.', '' )

# Note whether running under prod profile; this should ONLY be used for
# rare protection of prod data or dev/test support
MP_PROFILE_IS_PROD = is_prod_profile( MP_PROFILE )

# Private server IP, used as a namespace when development resources
# need to share services (e.g., to create unique, traceable folder names on S3)
MP_IP_PRIVATE = str( socket.gethostbyname(socket.gethostname()) )

# Define negative parameters for subdomains
MP_INVALID_NAME = ecs().load_value('MP_INVALID_NAME')
MP_INVALID_SUBDOMAIN = ecs().load_value('MP_INVALID_SUBDOMAIN')

# After experimenting with separate flags for Django vs. MPF debug,
# decided it was best to just leverage Django debug to keep permutations down
DEBUG = ecs().load_bool('DEBUG', echo=True)

# Is automated testing being run?
# HACK - Some test functionality specific to types
# Unit testing uses the Django test client, Selenium uses DJ, external is external
MP_TESTING = ecs().load_bool('MP_TESTING')
MP_TEST_TYPE = ecs().load_value('MP_TEST_TYPE')
MP_TESTING_VIEWS = MP_TEST_TYPE and MP_TEST_TYPE == 'View'
MP_TESTING_E2E = MP_TEST_TYPE and 'System' in MP_TEST_TYPE
MP_TESTING_UNIT = MP_TESTING and not MP_TESTING_E2E

# Flags for some debugging and deploy optimizations
MP_IS_COMMAND = bool( MP_COMMAND )
MP_IS_RUNNING_APP = bool( MP_DEVWEB or MP_WSGI )
MP_IS_DJ_SERVER = bool( MP_DEVWEB or MP_TESTING )
MP_DEV_EXCEPTION = bool( DEBUG or MP_TESTING )
MP_LOAD_ADMIN = ecs().load_bool( 'MP_LOAD_ADMIN',
            MP_TESTING_VIEWS or not MP_IS_COMMAND )

# Feature flagging
MP_FLAGS = ecs().load_value( 'MP_FLAGS', default={} )

# UI configuration
MP_SB = ecs().load_value( 'MP_SB', default={} )
MP_UI_TEXT = ecs().load_value( 'MP_UI_TEXT', default={} )
MP_UI_OPTIONS = ecs().load_value( 'MP_UI_OPTIONS', default={} )
MP_SANDBOX_EVENTS = ecs().load_value('MP_SANDBOX_EVENTS')

# Other settings
MP_ADMIN = ecs().load_value('MP_ADMIN')
MP_LOOKUP = ecs().load_value( 'MP_LOOKUP', default={} )

#--------------------------------------------------------------------
# Cloud usage

# If MP_CLOUD is set True, ALL cloud services are assumed to be available
# including DB, S3, CF, Cache, and SES
MP_CLOUD = ecs().load_value('MP_CLOUD')

if MP_CLOUD:

    # Load credential and other info from the instance running Django,
    # or in some remote command cases get info from a file.
    MP_AWS_INSTANCE = aws_instance_info()

    # Environment flag used for commands that run locally but use remote AWS
    # Disables references to DB and other AWS services that will cause errors for
    # local execution that uses AWS commands remotely.
    MP_AWS_REMOTE_ONLY = ecs().load_bool('MP_AWS_REMOTE_ONLY', default=False)

    # AWS info needed to create and use resources
    MP_ROOT_AWS = ecs().load_value('MP_ROOT_AWS')

"""-------------------------------------------------------------------
    Playpens - sharing/segregation of profile and resource namespace

    Playpens partition dev and prod shared resources, so the same
    server can run under different profiles with different namespaces,
    and different servers can have their own DB, S3, etc. namespaces
    in shared folders, DB servers, etc.

     - Playpens have a primary name that defaults to current profile and
       potentially custom platforms or dev information.

     - The Playpen can be explicitly set in profiles to allow different profiles
       to share resources (e.g., prod-mpd using production DB).

     - There are specialized playpen settings for caching, storage,
       SQS and other resources where more resolution beyond playpen name is useful

     - On AWS, dev servers are partitioned by IP address (clusters are separated by name)
       Each root is its own AWS account and one set of platforms, so AWS playpens
       ASSUME ONE ROOT/PLATFORM and do not include platforms in playpen names.

     - For local dev, also split out resource spaces by profile and root/platform.
       This MUST be done because DB, etc. are different for different platform combos.

     - Automated test runs have test appended to the playpen to segregate them
"""
_playpen_name = ecs().load_value( 'MP_PLAYPEN_NAME', default=MP_PROFILE )

# Setup group based on given group name and testing
# Add platforms for local test differentiation when not using AWS
_playpen_group = '-TEST' if MP_TESTING else ''
if not _playpen_name and not MP_CLOUD:
    # CAREFUL -- if you are mixing local dev with AWS resources, the root platform name
    # will not be added to the playpen namespace, which could lead to resources being
    # overrun on local server locations if platforms are switched -- this would
    # be a pretty rare use case, so don't try to deal with it automatically
    _playpen_group = '{}-{}'.format( _playpen_group, '_'.join( MP_PLATFORMS[1:] ))

MP_PLAYPEN_GROUP = _playpen_name + _playpen_group

# Adding IP allows different servers to shared same resource like bucket or DB
# Normally only used for non-clustered AWS resources (clustered servers have
# multiple IPs sharing resources, and local servers normally use local resources)
_playpen_add_ip = ecs().load_value('MP_PLAYPEN_ADD_IP', default=False)

# The namespace is used for URL locations that will map to resource locations (like
# folders) when a particular profile instance is running
if _playpen_add_ip and MP_IP_PRIVATE and MP_CLOUD:
    _playpen_namespace = '{}-'.format( MP_IP_PRIVATE )
else:
    _playpen_namespace = ''

# Profile playpen includes the playpen namespace, to partition resources by server
# instance as well as by profile and platforms
_playpen = _playpen_namespace + _playpen_name + _playpen_group

# Offer option to manually set playpen
MP_PLAYPEN = ecs().load_value( 'MP_PLAYPEN', default=_playpen, echo=True )

# Specialized playpen defaults
MP_PLAYPEN_STORAGE = ecs().load_value( 'MP_PLAYPEN_STORAGE', default=MP_PLAYPEN )
MP_PLAYPEN_CACHE = ecs().load_value( 'MP_PLAYPEN_CACHE', default=MP_PLAYPEN )
MP_PLAYPEN_CACHE_USER = ecs().load_value( 'MP_PLAYPEN_CACHE_USER', default=MP_PLAYPEN_CACHE )
MP_PLAYPEN_SQS = ecs().load_value( 'MP_PLAYPEN_SQS', default=MP_PLAYPEN )
MP_PLAYPEN_OPTIONS = ecs().load_value( 'MP_PLAYPEN_OPTIONS', default=MP_PLAYPEN, echo=True )

# Add timestamp to appropriate playpen namespaces
MP_PLAYPEN_ADD_TIMESTAMP = ecs().load_bool('MP_PLAYPEN_ADD_TIMESTAMP')
if MP_PLAYPEN_ADD_TIMESTAMP:
    MP_PLAYPEN_CACHE = '{}-{}'.format( MP_PLAYPEN_CACHE, MP_TIME_STAMP )
    MP_PLAYPEN_SQS['VERSION'] = '{}-{}'.format( MP_PLAYPEN_SQS['VERSION'], MP_TIME_STAMP )

"""--------------------------------------------------------------------
    MPF URL partitioning

    The following constants build URLs prefixes for:
      - Route prefixes to optionally separate server groups.
      - Special-case nginx and MPF paths for security and optimization
      - Organizing Django url groups for security and maintainability
      - For some user-visible urls, make them readable

    The (optional) server URL groups baked into MPF code are:
        FOH - Front-Of-House, DEFAULT high-traffic so no prefix
        BOH - Back-Of-House, for staff screens and APIs
        FT - Food Truck, external integration calls and higher risk requests
        OSK - Off-Site-Kitchen is task only; so no prefixes are defined
"""
MP_URL_FT = MP_ROOT['URL_PREFIX_FT']
MP_URL_BOH = MP_ROOT['URL_PREFIX_BOH']

# All requests for protected content go through one of these prefixes.
MP_URL_PROTECTED = 'ca'
MP_URL_PROTECTED_FT = join_urls( MP_URL_FT, MP_URL_PROTECTED )
MP_URL_PROTECTED_PASS = 'cap'  # nginx pass-through of some file types

# No-host request urls
# Used when the sandbox cannot be defined as part of the host name.
# This occurs for URLs through edge server and external sources
# like webhooks and OAuth.
# MPF passes sandbox ID in path for URLs originated in the platform,
# so routes to FOH by default. Querystring and root versions are for
# external integration so route to FT.
MP_URL_NO_HOST = MP_ROOT['URL_PREFIX_NO_HOST']
MP_URL_NO_HOST_ID = '{}/(?P<no_host_id>[\w]+)'.format( MP_URL_NO_HOST )
MP_URL_NO_HOST_FT = join_urls( MP_URL_FT, MP_URL_NO_HOST )

# Public page endpoints
MP_URL_USER = 'user'
MP_URL_PORTAL = 'portal'
MP_URL_PUBLIC = 'public'
MP_URL_PUBLIC_FT = join_urls( MP_URL_FT, MP_URL_PUBLIC )

# API and webhook endpoints
MP_URL_API = 'api'
MP_URL_API_FT = join_urls( MP_URL_FT, MP_URL_API )
MP_URL_API_BOH = join_urls( MP_URL_BOH, MP_URL_API )
MP_URL_API_PUBLIC = join_urls( MP_URL_API, MP_URL_PUBLIC )
MP_URL_API_PUBLIC_FT = join_urls( MP_URL_FT, MP_URL_API_PUBLIC )
MP_URL_API_PUBLIC_BOH = join_urls( MP_URL_BOH, MP_URL_API_PUBLIC )

# Root and staff Django admin areas
MP_URL_ROOTSTAFF = join_urls( MP_URL_BOH, 'rt' )
MP_URL_ROOTSTAFF_ADMIN = join_urls( MP_URL_ROOTSTAFF, 'ad' )
MP_URL_STAFF_ADMIN = join_urls( MP_URL_BOH, 'ad' )

# Dev and special uses
MP_URL_PUBLIC_DIRECT = MP_URL_PUBLIC + 'direct'  # Serve public files directly (vs. edge)
MP_URL_EXTERNAL = join_urls( MP_URL_FT, 'ext' )  # Requests for non-framework external components
MP_URL_MPF = join_urls( MP_URL_BOH, 'mpf' )      # Internal debug/test support

# Token used for creating portal paths
MP_URL_NAV_DEEPLINK = '/'

# Well known location for servicing health checks
# This is used both as a URL location AND as a hostname nginx healthcheck
# CANNOT overlap with MPF url prefixes, as it needs unique nginx location
MP_HEALTHCHECK_URL = 'mphealth'
MP_HEALTHCHECK_HOST = '{}.{}'.format( MP_HEALTHCHECK_URL, MP_ROOT['HOST'] )

# NGINX locations PREFIXES for uWSGI proxy
# PREFIXES NOT HERE ARE NOT PASSED TO UWSGI
MP_URL_NGINX = {
    'PUBLIC_CACHE': (
        MP_URL_PUBLIC,
        MP_URL_PUBLIC_FT,
        MP_URL_API_PUBLIC,
        MP_URL_API_PUBLIC_FT,
        ),
    'MAIN': (
        MP_URL_FT,
        MP_URL_API,
        MP_URL_NO_HOST,
        MP_URL_PROTECTED,
        MP_URL_PORTAL,
        MP_URL_USER,
        ),
    'ADMIN': (
        MP_URL_BOH,
        ),
    'ROOT_PASS': ( '/', '/service_worker\.js', '/manifest\.json', '/favicon\.ico',
            '/sitemap\.xml', '/robots\.txt' ),
    }

# All url paths designated as Django admin pages
MP_URL_ADMIN_PAGES = (
    MP_URL_STAFF_ADMIN,
    MP_URL_ROOTSTAFF_ADMIN,
    )

# ALWAYS show these, even if sandbox portal is private, and exclude
# from tracking and session management
_always_show = ( 'robots.txt', 'favicon.ico', 'service_worker.js', 'manifest.json' )

# Middleware authentication
# Urls that match these PREFIXES don't require a user session
# in middleware (although authentication may be considered elsewhere)
# No-host URLs never require user session
MP_URL_PATHS_PUBLIC = [
    MP_URL_USER,
    MP_URL_PUBLIC,
    MP_URL_PUBLIC_FT,
    MP_URL_API_PUBLIC,
    MP_URL_API_PUBLIC_FT,
    MP_URL_API_PUBLIC_BOH,

    # Protected access is NOT enforced in middleware to allow for loose
    # content protection as work around to session-loss issues
    MP_URL_PROTECTED,
    MP_URL_PROTECTED_FT,

    # Server (vs. edge) hosting of public static content
    MP_URL_PUBLIC_DIRECT,
    ] + list( _always_show )

# URLs with these PREFIXES won't have full processing
MP_URL_LITE_EXCLUDES = (
    ) + _always_show

# URLs with these PREFIXES won't be tracked
MP_URL_TRACKING_EXCLUDES = (
    MP_URL_BOH,
    MP_URL_NO_HOST,
    MP_URL_NO_HOST_FT,
    MP_URL_API,
    MP_URL_API_PUBLIC,
    MP_URL_API_PUBLIC_FT,
    MP_URL_PROTECTED,
    MP_URL_PROTECTED_FT,
    ) + _always_show

#--------------------------------------------------------------------
# Misc MPF, Django, and external settings

# Django seed for hashing
SECRET_KEY = ecs().load_value('SECRET_KEY')

# Emails that Django sends admin emails to
ADMINS = tuple(tuple(item) for item in ecs().load_value('ADMINS'))

# Values for CORS and other HTTP authentication
MP_HTTP_SECURITY = ecs().load_value('MP_HTTP_SECURITY')

# Compress JS/CSS and remove spaces from HTML?
MP_COMPRESS = ecs().load_value('MP_COMPRESS')

# Force tests to create DB in file instead of in memory
MP_TEST_USE_NORMAL_DB = ecs().load_bool('MP_TEST_USE_NORMAL_DB')

#--------------------------------------------------------------------
# User Management settings

# Length of time for sessions to remain valid
MP_USER_SESSION_AGE_LONG = ecs().load_int('MP_USER_SESSION_AGE_LONG')
MP_USER_SESSION_AGE_SHORT = ecs().load_int('MP_USER_SESSION_AGE_SHORT')

# Password policy for new/changing passwords
MP_PASSWORD_MIN_LEN = ecs().load_value('MP_PASSWORD_MIN_LEN')
MP_PASSWORD_INVALID = ecs().load_value('MP_PASSWORD_INVALID')

# Login failure timeout management
MP_LOGIN_FAILURE_THRESHOLD = ecs().load_value('MP_LOGIN_FAILURE_THRESHOLD')
MP_LOGIN_FAILURE_MULTIPLIER = ecs().load_value('MP_LOGIN_FAILURE_MULTIPLIER')
MP_LOGIN_FAILURE_MAX = ecs().load_value('MP_LOGIN_FAILURE_MAX')
MP_LOGIN_FAILURE_WAIT = ecs().load_value('MP_LOGIN_FAILURE_WAIT')

#--------------------------------------------------------------------
# Email

if MP_CLOUD:

    # MPF uses Django SMTP to send through SES
    # The user and password for SMTP are setup in SES and stored in secrets
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = MP_ROOT['EMAIL_SERVER']
    EMAIL_USE_TLS = True
    ( EMAIL_HOST_USER, EMAIL_HOST_PASSWORD ) = aws_email_credentials()

else:
    # For local servers, put emails into folder
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = work_path( MP_PLAYPEN, 'emails' )

EMAIL_PORT = ecs().load_value('EMAIL_PORT')
EMAIL_TIMEOUT = ecs().load_value('EMAIL_TIMEOUT')
EMAIL_MP_RETRYS = ecs().load_value('EMAIL_MP_RETRYS')

# Email notifications; add server name if name supports it
DEFAULT_FROM_EMAIL = ecs().load_value('DEFAULT_FROM_EMAIL')
try:
    DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL.format( MP_PLAYPEN )
except KeyError:
    pass

#--------------------------------------------------------------------
# Logging - some values may be read from environment

# Adjustable logging levels
MP_LOG_LEVEL_INFO_MIN = ecs().load_int('MP_LOG_LEVEL_INFO_MIN', echo=True)
MP_LOG_LEVEL_DEBUG_MIN = ecs().load_int('MP_LOG_LEVEL_DEBUG_MIN', echo=True)

# Options for browser phone-home logging
MP_LOG_BROWSER = ecs().load_value('MP_LOG_BROWSER')

# Sub-logging initial settings; overridden if running as application with options in DB
MP_LOG_ALL = ecs().load_bool('MP_LOG_ALL')
MP_LOG_SUB = ecs().load_value('MP_LOG_SUB', echo=True)

# Other logging options
MP_LOG_OPTIONS = ecs().load_value('MP_LOG_OPTIONS')

#--------------------------------------------------------------------
# Debug and Testing

# Environment testing options
MP_TEST_LEVEL = ecs().load_int('MP_TEST_LEVEL') if MP_TESTING else 0
MP_TEST_NO_LOG = ecs().load_bool('MP_TEST_NO_LOG',
      default=bool( MP_TESTING and MP_TEST_LEVEL <= 1))

# Other test options usually set in environment
MP_TEST_BROWSER = ecs().load_value('MP_TEST_BROWSER')
MP_TEST_URL = ecs().load_value('MP_TEST_URL')
MP_TEST_SITE_NAME = ecs().load_value('MP_TEST_SITE_NAME')
MP_TEST_WAIT = ecs().load_value('MP_TEST_WAIT')
MP_TEST_RUNS = ecs().load_value('MP_TEST_RUNS')

# Mock some AWS info to allow code paths to be tested
if not MP_CLOUD:
    MP_AWS_INSTANCE = { 'region': 'AWS-TEST' }

# Not using DJ toolbar by default
DEBUG_TOOLBAR = False

# Throw exceptions if template errors?
MP_TEMPLATE_DEBUG = ecs().load_bool('MP_TEMPLATE_DEBUG', default=False)

# Flag that controls whether all fixtures are loaded
MP_TEST_USE_FIXTURES = ecs().load_bool('MP_TEST_USE_FIXTURES')

# What locations be doing debugging
MP_DEV_IPS = ecs().load_value('MP_DEV_IPS', default=())

# In areas that need unique names, use guids or more friendly names built from IP,
# etc. that work better for human debugging
MP_HASH_UNIQUE_NAMES = ecs().load_bool('MP_HASH_UNIQUE_NAMES')
