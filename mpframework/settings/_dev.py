#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django Test and Debug support settings

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""

from ..common.deploy.paths import mpframework_path
from . import env
from . import _first
from . import _template
from . import _file

# Non-uwsgi configs look for application object here
WSGI_APPLICATION = 'mpframework.common.deploy.wsgi_app.dev_app'

# Redefine these here, to easily add to them based on options
MIDDLEWARE = _first.MIDDLEWARE
INSTALLED_APPS = _first.INSTALLED_APPS

# Test run customizations
TEST_RUNNER = 'mpframework.testing.framework.runner.TestRunner'

# Set of localhost aliases
MP_LOCALHOST_ALIASES = [
    'localhost',
    '.127.0.0.1.nip.io',            # This will get set as MP_ROOT_URL
    'mphealth.local-profile',       # Local test of health ping
    ]

#--------------------------------------------------------------------
# Fixtures and test cases
# Order is important here, because of fixture dependencies

# Tell DJ where to find fixtures for loading DB
# Will always load at least root user, so always define the folder
FIXTURE_DIRS = [ mpframework_path('testing', 'fixtures') ]

if env.MP_TEST_USE_FIXTURES:

    # Add folder for public fixture files
    _file.STATICFILES_DIRS += [
        mpframework_path('testing', 'fixtures', 'static')
        ]

    # Test suites to run by default
    MP_TEST_DJTESTS = [ 'common',
        'foundation.tenant', 'foundation.ops', 'frontend.sitebuilder',
        'user.mpuser',
        'content.mpcontent',
        'frontend.portal',
        ]

    # Test fixtures to load
    # Ordering of fixture load matters when default values for a model
    # need "upstream" values from DB (e.g., using pre_save)
    MP_TEST_FIXTURES = [
        'root', 'tenant', 'sitebuilder', 'ops',
        'user', 'content', 'portal',
        ]

    # Where can test fixture content files be loaded from?
    MP_TEST_FOLDERS_FILES = ( mpframework_path(
                'testing', 'fixtures', 'files' ) ,)

else:

    # Only load base user accounts to get root user
    MP_TEST_FIXTURES = [ 'root' ]

#--------------------------------------------------------------------
# Running as Automated testing

if env.MP_TESTING:

    INSTALLED_APPS += [
        # Needed by Django TestCase class
        'django.contrib.sessions',
        ]

#--------------------------------------------------------------------
# Running in debug

if env.DEBUG and not env.MP_TESTING:

    if env.DEBUG_TOOLBAR:

        # Do explicit debug toolbar setup as per website
        DEBUG_TOOLBAR_PATCH_SETTINGS = False

        INSTALLED_APPS += [
            'debug_toolbar',
            ]
        MIDDLEWARE = _first.MP_MIDDLEWARE_EARLY + [
            'debug_toolbar.middleware.DebugToolbarMiddleware',
            ] + _first.MP_MIDDLEWARE_MAIN

        # Add the toolbar's path to the no-login urls
        import debug_toolbar
        env.MP_URL_PATHS_PUBLIC += list( debug_toolbar.urls )

        DEBUG_TOOLBAR_PANELS = (
            'debug_toolbar.panels.timer.TimerPanel',
            'debug_toolbar.panels.templates.TemplatesPanel',
            'debug_toolbar.panels.cache.CachePanel',
            'debug_toolbar.panels.headers.HeadersPanel',
            'debug_toolbar.panels.request.RequestPanel',
            'debug_toolbar.panels.sql.SQLPanel',
            'debug_toolbar.panels.settings.SettingsPanel',
            'debug_toolbar.panels.staticfiles.StaticFilesPanel',
            'debug_toolbar.panels.signals.SignalsPanel',
            'debug_toolbar.panels.logging.LoggingPanel',
            'debug_toolbar.panels.redirects.RedirectsPanel',
            'debug_toolbar.panels.versions.VersionsPanel',
            )

        DEBUG_TOOLBAR_CONFIG = {
            # Start toolbar collapsed
            'SHOW_COLLAPSED': True,
            # Use MPF jQuery
            'JQUERY_URL': '',
            # Control where/when toolbar is injected onto page
            'INSERT_BEFORE': '</djtoolbar>',
            # Sometimes, like download playing, don't want toolbar
            'SHOW_TOOLBAR_CALLBACK': 'mpframework.common.debug.debug_toolbar_show',
            # Make intercept capture based on setting
            'INTERCEPT_REDIRECTS': False,
            }


    # To enable some DJ debug behavior, set internal IPs it is enabled for
    if env.MP_DEV_IPS:
        from iptools import IpRangeList
        INTERNAL_IPS = IpRangeList( *env.MP_DEV_IPS )

    # Override template loading to not use caching
    _template.TEMPLATES[0]['OPTIONS']['loaders'] = _template.template_loaders

    # Inject Django and mpFramework debug values into templates
    _template.TEMPLATES[0]['OPTIONS']['context_processors'] += (
        'mpframework.foundation.ops.context_processors.mpdebug',
        )

    MIDDLEWARE += [
        'mpframework.foundation.ops.middleware.mpDebugMiddleware',
        ]

if env.MP_TEMPLATE_DEBUG:

    class TemplateVariableDebug( str ):
        """
        Provide some ability to see errors swallowed in Django template processing
        Normally this isn't a concern, but sometimes a coding error in a model
        that is referenced in context can be hard to find if it manifests as
        a type of exception (like AttributeError) that templates swallow.
        """
        def __mod__( self, other ):
            from mpframework.common import log
            log.debug2("Template unknown value: %s", other)
            # Uncomment to throw exceptions
            #raise Exception("Template variable error")

    _template.TEMPLATES[0]['OPTIONS'][
            'string_if_invalid'] = TemplateVariableDebug('')

#--------------------------------------------------------------------
# Running as a dev server

if env.MP_DEVWEB:

    env.MP_URL_PATHS_PUBLIC += [

        # Support localprotected serving of protected content to visitors
        _file.MP_URL_PROTECTED_XACCEL.strip('/'),

        ]
