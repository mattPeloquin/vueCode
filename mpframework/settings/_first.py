#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    First Django settings

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""

from mpframework.common.deploy.paths import work_path

from . import env

#---------------------------------------------------
# Apps and Middleware

# Urls are stored in cascading tree of files for platforms and their apps,
# but all MPF instances start from this root module
ROOT_URLCONF = 'mpframework.settings.urls'

# Admin apps are expensive, so don't load for commands that don't need
# Ordering of admin affects some loading of templates from app dirs
MP_APPS_ADMIN = [] if not env.MP_LOAD_ADMIN else [
    'nested_admin',                 # Nesting inlines in admin to follow FKs
    'django.contrib.admin',         # Default Django admin
    'django.contrib.messages',      # Required by admin
    ]

MP_APPS_EXTERNAL = [
    'django.contrib.contenttypes',  # Support for Django models
    'django.contrib.auth',          # User model and authorization
    'django.contrib.staticfiles',   # Manipulating static files
    'django.forms',                 # Make forms use normal template processing
    'sass_processor',               # Build sass css processing into templates
    'compressor',                   # Compress static files loaded by django
    'django_extensions',            # Useful management commands
    's3direct',                     # Direct to S3 upload
    'timezone_field',               # Support for selecting timezone (needs pytz)
    'mptt',                         # Model tree support
    ]

MP_APPS_CORE = [
    'mpframework.foundation.tenant',
    'mpframework.user.mpuser',
    'mpframework.content.mpcontent',
    'mpframework.frontend.sitebuilder',
    'mpframework.frontend.portal',
    ]

MP_APPS_LAST = [
    # HACK - Include last, raise startup signal in dev/test
    'mpframework.foundation.ops',
    ]

INSTALLED_APPS = (
    MP_APPS_EXTERNAL +
    MP_APPS_ADMIN +
    MP_APPS_CORE +
    MP_APPS_LAST )

MP_MIDDLEWARE_EARLY = [
    # Ensure first/last opportunity for all request/responses
    'mpframework.foundation.ops.middleware.mpFirstLastMiddleware',
    ]
MP_MIDDLEWARE_MAIN = [
    # First determine sandbox tenancy based on url request
    'mpframework.foundation.tenant.middleware.SandboxMiddleware',

    # Customize Django security and session middleware
    'mpframework.foundation.ops.middleware.mpCorsMiddleware',
    'mpframework.foundation.ops.middleware.mpCspMiddleware',
    'mpframework.user.mpuser.middleware.mpSessionMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    # Replace django user authentication and user object management
    # and then Check for URL access based on user privilege
    'mpframework.user.mpuser.middleware.mpAuthenticationMiddleware',
    'mpframework.user.mpuser.middleware.UserAccessMiddleware',

    # MPF middleware that need to setup request attributes
    'mpframework.frontend.sitebuilder.middleware.SitebuilderMiddleware',

    'django.middleware.common.CommonMiddleware',

    # Used by django admin
    'django.contrib.messages.middleware.MessageMiddleware',

    # MPF response exception handling
    'mpframework.foundation.ops.middleware.mpExceptionMiddleware',
    ]
MIDDLEWARE = MP_MIDDLEWARE_EARLY + MP_MIDDLEWARE_MAIN

"""--------------------------------------------------------
    User session and cookie management

    Use volatile caching for sessions.
    In cluster must have shared cache for this to work, and
    caching not available will PREVENT ALL LOGINS

    So far this has proven reasonable in production, as cache going
    down isn't any more risky than DB going down
"""

# Allowed hosts defines what host names Django will accept
# The . prefix makes all subdomains work, while * allows all,
# which is what MPF uses since it manages hosts per sandbox
ALLOWED_HOSTS = [ '*' ]

if not env.MP_IS_DJ_SERVER:
    # Mark session cookies as secure only
    # Only public pages are allowed to display on HTTP
    SESSION_COOKIE_SECURE = True
    # As per Django docs, this not really important for security, but force
    # to avoid false positives in audit tools.
    # FUTURE - IF ANY FORM NEEDS CSRF IN PUBLIC, WILL NEED
    # MIDDLEWARE THAT ONLY SETS THIS ON A SECURE RESPONSE
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

# Use Django cache-only session, with no DB backing
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'users'

# Length of time for sessions to remain valid in BROWSER
# Set to maximum time browser will retain the session id in the cookie
SESSION_COOKIE_AGE = env.MP_USER_SESSION_AGE_LONG

# MPF overides Django session
SESSION_COOKIE_NAME = "{}{{}}_session".format( env.MP_PLATFORMS_ROOT )

# Django code is used for CSRF cookie
CSRF_COOKIE_NAME = '{}_csrf'.format( env.MP_PLATFORMS_ROOT )

# Don't persist CSRF on browser; store in memory only
CSRF_COOKIE_AGE = None

# Better page for CSRF failure, which can occur when browser gets
# out of whack or cookies are disabled
CSRF_FAILURE_VIEW = 'mpframework.foundation.tenant.views.csrf_failure.handle_csrf_failure'

#---------------------------------------------------
# Login, Navigation

# Replace Django default user with mpUser
AUTH_USER_MODEL = 'mpuser.mpUser'
MP_USER_AUTHENTICATION_BACKEND = 'mpframework.user.mpuser.backends.mpUserBackend'
AUTHENTICATION_BACKENDS = ( MP_USER_AUTHENTICATION_BACKEND ,)

# Used by the Django admin
LOGIN_URL = '/{}/login'.format( env.MP_URL_USER )
LOGOUT_URL = '/{}/logout'.format( env.MP_URL_USER )
LOGIN_REDIRECT_URL = '/'

# Allow slash appending on URLs
APPEND_SLASH = True

# How long does a password reset email last?
PASSWORD_RESET_TIMEOUT_DAYS = 4

#---------------------------------------------------
# Logging setup

from mpframework.common import log
from mpframework.common.logging import setup

# Tell Django MPF will be configuring logging
LOGGING_CONFIG = None

# Setup Django settings.LOGGING
# Some may be overridden later when options read from DB
_local_log = env.MP_LOG_OPTIONS.get('LOCALFILE')
_local_log = work_path( _local_log ) if _local_log else None
_syslog = env.MP_ROOT['SYSLOG'] if env.MP_LOG_OPTIONS.get('SYSLOG') else None
LOGGING = setup.logging_dict(
            debug_level     = env.MP_LOG_LEVEL_DEBUG_MIN,
            verbose         = env.MP_LOG_OPTIONS.get('VERBOSE'),
            sub_on          = env.MP_LOG_ALL,
            syslog          = _syslog,
            as_app          = env.MP_IS_RUNNING_APP,
            logfile_path    = _local_log
            )

# HACK - MONKEY PATCH DB connection wrapper to use MPF logging
# level; DB connections are thread-local, so this is easiest way to manage
def queries_logged( self ):
    return log.info_on() > 1 or self.force_debug_cursor or env.DEBUG
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.queries_logged = property( queries_logged )

#--------------------------------------------------------------------
# Other Django settings

# Make admin and other Django objects timezone aware (all data stored as UTC)
# and make Django default UTC (sandboxes override)
USE_TZ = True
TIME_ZONE = 'UTC'

# Django 3.2 changed default id field to BigInt
# FUTURE - migrate to BigInt if any table at risk of exceeding int
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Harden against DoS through POSTs
DATA_UPLOAD_MAX_MEMORY_SIZE = 500000
# FUTURE SCALE - the max number if post items needs to be set high to support
# large group accounts because of the way the group admin works.
# Until that is changed to only handle deltas of users on save, this
# will be the maximum number of users in a group account
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2500

SILENCED_SYSTEM_CHECKS = [
    'auth.W004',    # MPF custom user tenancy doesn't use a unique username
    'urls.W002',    # Some sub-urls intentionally use / prefix

    # MPF customizes session and authentication, so silence errors from
    # admin about them not being present
    'admin.E408',
    'admin.E410',
    ]

# Use sessions for messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Don't distinguish between manager and admin notifications
MANAGERS = env.ADMINS

# FUTURE - Make locale based on sandbox
USE_L10N = True
USE_THOUSANDS_SEPARATOR = True

# FUTURE - translation of platform is future concern (content is all English)
USE_I18N = True
LANGUAGE_CODE = 'en-us'
