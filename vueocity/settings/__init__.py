#--- Vueocity platform, Copyright 2021 Vueocity LLC
"""
    Items in this file are included by and must conform to
    assumptions in:  mpframework.settings.add_settings
"""

from mpframework.settings import env
from mpframework.settings import _first
from mpframework.settings import _template
from mpframework.settings import _file
from mpframework.settings import _dev
from mpframework.common.deploy.paths import home_path
from mpframework.common.deploy.settings import get_ecs as ecs


_first.INSTALLED_APPS[:] = (
    _first.MP_APPS_EXTERNAL +
    _first.MP_APPS_ADMIN +
    _first.MP_APPS_CORE + [
    # Place Vueocity apps in front of other core apps for template load override
    'vueocity.frontend.portal',
    'vueocity.frontend.onboard',
    'vueocity.foundation.ops',
    ] +
    _first.MP_APPS_LAST )

# Add global template folder and static files first to allow overrides
_template.TEMPLATES[0]['DIRS'][0:0] = [
    home_path( 'vueocity', 'templates' ),
    ]
_file.STATICFILES_DIRS[0:0] = [
    home_path( 'vueocity', 'static' ),
    ]

_template.TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'vueocity.frontend.onboard.context_processors.onboard',
    ]

# Metadata for structuring onboard process
MP_ROOT_ONBOARD_SETUP = ecs().load_value('MP_ROOT_ONBOARD_SETUP')
MP_ROOT_ONBOARD_LEVELS = ecs().load_value('MP_ROOT_ONBOARD_LEVELS')


#--------------------------------------------------------------------
# Test, debug

_fixtures = home_path( 'vueocity', 'testing', 'fixtures' )

_dev.FIXTURE_DIRS.extend([ _fixtures ])

if env.MP_TEST_USE_FIXTURES:

    _file.STATICFILES_DIRS[0:0] = [
        home_path( 'vueocity', 'testing', 'fixtures', 'static' ),
        ]
    _dev.MP_TEST_DJTESTS += [
        'foundation.ops', 'frontend.onboard', 'frontend.portal',
        ]
    _dev.MP_TEST_FIXTURES += [
        'vueweb',
        ]

if env.MP_DEVWEB:
    # Allow visitor use of onboarding screen
    env.MP_URL_PATHS_PUBLIC += [
        'rt/mpf/onboard',
        ]
