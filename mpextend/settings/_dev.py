#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpExtend development settings

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""
from os.path import join

from mpframework.settings import env
from mpframework.settings import _dev
from mpframework.settings import _file
from mpframework.common.deploy.paths import home_path


_fixtures = home_path( 'mpextend', 'testing', 'fixtures' )

# Tell MPF where to find fixtures
_dev.FIXTURE_DIRS.extend([ _fixtures ])

if env.MP_TEST_USE_FIXTURES:

    # Add sandbox public fixtures to static files
    _file.STATICFILES_DIRS[0:0] = [
        join( _fixtures, 'static' ),
        ]

    # NEW names to look for yaml fixtures and tests
    _dev.MP_TEST_DJTESTS += [
        'content.lms', 'content.video', 'content.proxy',
        'product.account', 'product.catalog', 'product.payment',
        'user.plan', 'user.usercontent', 'user.tracking', 'user.sso',
        'foundation.reports',
        ]
    _dev.MP_TEST_FIXTURES += [
        'account', 'catalog', 'plan', 'usercontent',
        ]

    # Where can test fixtures be loaded from?
    MP_TEST_FOLDERS_PACKAGES = (
        join( _fixtures, 'lms' ),
        )
