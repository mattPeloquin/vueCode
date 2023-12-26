#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpExtend extensions that modify mpFramework settings

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""

from mpframework.settings import env
from mpframework.settings import _first
from mpframework.settings import _template
from mpframework.settings import _file
from mpframework.settings import _misc
from mpframework.common.deploy.paths import home_path

from . import _env

# Override and extend mpFramework app loading
_first.MP_APPS_CORE[:] = [

    'mpframework.foundation.tenant',

    'mpextend.user.mpuser',
    'mpframework.user.mpuser',

    'mpextend.content.mpcontent',
    'mpframework.content.mpcontent',

    'mpextend.product.account',
    'mpextend.product.catalog',
    'mpextend.product.payment',

    'mpextend.user.sso',
    'mpextend.user.tracking',
    'mpextend.user.usercontent',
    'mpextend.user.plan',

    'mpextend.content.lms',
    'mpextend.content.proxy',
    'mpextend.content.video',

    'mpextend.frontend.sitebuilder',
    'mpframework.frontend.sitebuilder',
    'mpextend.frontend.portal',
    'mpframework.frontend.portal',

    'mpextend.foundation.reports',
    ]

_first.MP_APPS_LAST[:] = [
    # Extend ops while preserving last load position
    'mpextend.foundation.ops',
    'mpframework.foundation.ops',
    ]

_first.INSTALLED_APPS[:] = (
    _first.MP_APPS_EXTERNAL +
    _first.MP_APPS_ADMIN +
    _first.MP_APPS_CORE +
    _first.MP_APPS_LAST )

_first.MIDDLEWARE += [
    # User tracking via request info
    'mpextend.user.tracking.middleware.UserTrackingMiddleware',
    ]

# Insert file searches to occur before mpframrework
_template.TEMPLATES[0]['DIRS'][0:0] = [
    home_path( 'mpextend', 'templates' ),
    ]
_file.STATICFILES_DIRS[0:0] = [
    home_path( 'mpextend', 'static' ),
    ]

_template.TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'mpextend.foundation.ops.context_processors.common',
    'mpextend.product.catalog.context_processors.catalog',
    'mpextend.product.account.context_processors.account',
    ]

# Add admin permissions for apps with admin pages
env.MP_ADMIN['AREA_PERMISSIONS'].update({
    'plan': ( 'AREA', 'U' ),
    'usercontent': ( 'AREA', 'U' ),
    })

# Options that can be set dynamically
_misc.MP_OPTIONS.extend([

    # Tune user tracking
    ('tracking_inactive_delta', _env.MP_TRACKING['INACTIVE_DELTA'],
             "Seconds until client inactive"),
    ('tracking_inactive_placeholder', _env.MP_TRACKING['INACTIVE_PLACEHOLDER'],
             "Seconds added to inactive tracking"),

    ])
