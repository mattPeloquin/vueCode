#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Template and django-compressor settings

    Django template loading is first-encountered in folders
    searched for template files set in the settings below.

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""

from mpframework.common.utils import join_urls
from mpframework.common.deploy.paths import mpframework_path
from mpframework.common.deploy.paths import packages_path

from . import env
from . import _file


"""--------------------------------------------------------------------
    Template Folders

    The folders below are tried by the filesystem.loader in the
    order listed below -- first hit encountered is the one used.

    1) Django folder is checked fist, to allow loading/extend templates
    using paths prefixed by 'templates/', which supports overriding
    without unwanted recursion.

    2) Next add MPF templates. The settings process will
    append the templates for platform folders after this. Note that
    order of the platforms is important, which is why:

        MIDDLE PLATFORMS (e.g., mpextend) DON'T OVERRIDE EACH
        OTHER'S TEMPLATES...

    ...because load order is dependent on platform order

    3) The app_directories loader then loads app templates in app order
"""
_template_folders = [
    packages_path( 'django', 'contrib', 'admin' ),
    mpframework_path('templates'),
    ]

"""--------------------------------------------------------------------
    Template Loaders

    MPF places templates in both app folders and platform
    level folders, depending on whether the templates are shared
    or cross-cutting in nature.
"""
template_loaders = (
    # First load templates from explicitly defined in TEMPLATES
    # then look in app sub-folders (follows order of installed apps)
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    )

if env.MP_IS_RUNNING_APP:
    # Use cached template loading when running server, but not otherwise
    # to handle problem with django-compressor where loader caches nodes
    # across platform template files
    template_loaders = (
        ( 'django.template.loaders.cached.Loader', template_loaders ),
        )

"""--------------------------------------------------------------------
    Django template settings
    These may get overridden by dev or platform settings
"""

# Include commonly used template tags and filters as builtins
_built_in_tags = [
    'mpframework.frontend.sitebuilder.templatetags.include_files',
    'mpframework.frontend.sitebuilder.templatetags.filters',
    'mpframework.frontend.sitebuilder.templatetags.mp_include',
    'mpframework.frontend.sitebuilder.templatetags.mp_extends',
    'mpframework.frontend.sitebuilder.templatetags.filters',
    'mpframework.frontend.sitebuilder.templatetags.tags',
    ]

# Context needed for offline processing
# This is also used as a base for normal context.
TEMPLATE_OFFLINE_CONTEXT = {

    # STATIC_URL is set to URL for static content relative to the current url root
    # so templates can use the static_url value directly instead of the
    # Django template tag, which can be kludgy to concatonate
    'static_url': _file.STATIC_URL,
    'static_url_resource': join_urls( _file.STATIC_URL, 'mpf-root' ),

    # Static file compression support
    'compress_on': env.MP_COMPRESS['JS'] or env.MP_COMPRESS['CSS'],

    'debug': env.DEBUG,
    'code_rev': env.MP_CODE_CURRENT,
    'profile_is_prod': env.MP_PROFILE_IS_PROD,
    'dev_server': env.MP_DEVWEB,
    'mp_testing': env.MP_TESTING,
    }
if env.MP_DEVWEB:
    TEMPLATE_OFFLINE_CONTEXT.update({
        'log_localfile': env.MP_LOG_OPTIONS.get('LOCALFILE'),
        })

# Global context processors provide variables to every template
_template_context_processors = [
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.template.context_processors.tz',
    'django.template.context_processors.i18n',
    'mpframework.foundation.ops.context_processors.common',
    'mpframework.foundation.tenant.context_processors.tenant',
    'mpframework.frontend.sitebuilder.context_processors.portal',
    'mpframework.user.mpuser.context_processors.user',
    'mpframework.content.mpcontent.context_processors.content',
    'mpframework.frontend.portal.context_processors.portal',
    ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': _template_folders,
        'OPTIONS': {
            'loaders': template_loaders,
            'builtins': _built_in_tags,
            'context_processors': _template_context_processors,
            'debug': env.MP_TEMPLATE_DEBUG,
            },
        },
    ]

# Make Django forms use the same rendering as MPF templates
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

"""-----------------------------------------------------------------
    django-compressor settings

    MPF uses a mix of offline and inline compression, so the
    COMPRESS_OFFLINE default setting is NOT uses. Instead:

        1) Offline file compression uses the compress_mp tag and is
           run as part of the fab static command.
        2) Inline snippets use compress_mp_inline tag, and are only
           used with cached template fragments.

    FUTURE - could add inline filters for SASS, HTML compression, etc.
"""
COMPRESS_ENABLED = TEMPLATE_OFFLINE_CONTEXT['compress_on']
COMPRESS_OUTPUT_DIR = 'min'
COMPRESS_CACHE_BACKEND = 'template'

# Compressed file references are stored in the manifest, hashed by filename
# These manifests are tied to profile, so different profile versions can coexist
# The context for the manifest supports both normal and compatible paths
COMPRESS_OFFLINE_MANIFEST = '{}_{}.json'.format(
            env.MP_PROFILE_FULL, env.MP_CODE_CURRENT )
COMPRESS_OFFLINE_CONTEXT = 'mpframework.common.template.mp_compressor.offline_contexts'

# Since MPF does not use compressor in a typical way (cached inline tags are
# stored in cached template fragments, and both these and offline compressed
# files are tied to CODE_CURRENT number in manifest and cache playpen) there
# is no need for compressor to check for modified file times
# (it hits cache every 10 seconds by default)
COMPRESS_MTIME_DELAY = 2592000  # 30 days

# Undocumented option to log errors
COMPRESS_VERBOSE = env.MP_COMPRESS['VERBOSE']

# Where compress stores files
COMPRESS_URL = _file.STATIC_URL
COMPRESS_ROOT = _file.STATIC_ROOT
COMPRESS_STORAGE = _file.STATICFILES_STORAGE

COMPRESS_FILTERS = {
    'js': [
        'compressor.filters.jsmin.JSMinFilter',
        ],
    'css': [
        'compressor.filters.css_default.CssAbsoluteFilter',
        'compressor.filters.cssmin.rCSSMinFilter',
        ],
    }

# Needed to prevent error on the settings debug page
COMPRESS_JINJA2_GET_ENVIRONMENT = {}
