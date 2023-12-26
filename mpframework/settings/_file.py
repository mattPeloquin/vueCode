#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django file related settings

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""

from mpframework.common.deploy.settings import get_ecs as ecs
from mpframework.common.deploy.paths import mpframework_path
from mpframework.common.deploy.paths import work_path
from mpframework.common.aws.secrets import aws_cf_credentials
from mpframework.common.utils import join_urls

from . import env


"""------------------------------------------------------------------
    Public (static), protected and archive file support

    - All files are stored on S3 for AWS profiles, and locally in
      work folder for local dev profiles

    - Public files are publicly available, with URLs that allow direct
      access to the file without login or rights. Django refers to
      these files as "static" and "media"; in addition to MPF files
      all Django STATIC_URL and MEDIA_URL files are under public location:

        - The browser client UI (JS, CSS) is provided by public files
        - Provider uploads for customization are Public
        - All user uploads (e.g., ImageField) are Public

    - Protected files are accessed through MPF and only
      accessible to users with rights to see them

    - Archive files are protected files uploaded by providers, but which are
      NOT available for download (usually files used to derive protected files)

    Based on settings, public and protected files may be served from the Django
    webserver, NGINX, or CloudFront.
"""

if env.MP_CLOUD:

    # Support manual assignment of buckets in profiles
    # How a bucket manages it's namespace is controlled by the MP_PLAYPEN_STORAGE
    # setting (e.g., whether different profiles are placed in different folders)
    MP_AWS_BUCKET_PUBLIC = env.MP_ROOT_AWS['S3_BUCKET_PUBLIC']
    MP_AWS_BUCKET_PROTECTED = env.MP_ROOT_AWS['S3_BUCKET_PROTECTED']

    _addon = '/{}'.format( env.MP_PLAYPEN_STORAGE ) if env.MP_PLAYPEN_STORAGE else ''

    # HTTP addresses for accessing S3 buckets directly
    # Used for direct file upload and scenarios where Nginx accesses S3
    # Assume accelerated endpoints are enabled (to support upload acceleration)
    _url = 'https://{{}}.s3-accelerate.amazonaws.com{}/'.format( _addon )
    MP_AWS_S3_PUBLIC_URL = _url.format( MP_AWS_BUCKET_PUBLIC )
    MP_AWS_S3_PROTECTED_URL = _url.format( MP_AWS_BUCKET_PROTECTED )

    # Internal S3 endpoints for buckets
    _endpoint = 'https://{{}}.s3.amazonaws.com{}/'.format( _addon )
    MP_AWS_S3_PUBLIC_ENDPOINT = _endpoint.format( MP_AWS_BUCKET_PUBLIC )
    MP_AWS_S3_PROTECTED_ENDPOINT = _endpoint.format( MP_AWS_BUCKET_PROTECTED )

    if not env.MP_AWS_REMOTE_ONLY:
        # Load credentials for cloudfront protected content signing
        ( env.MP_ROOT_AWS['CF_KEY_ID'], env.MP_ROOT_AWS['CF_KEY']
                ) = aws_cf_credentials()

# File types that should NOT be cached on CF
MP_EDGE_NOCACHE = ecs().load_value('MP_EDGE_NOCACHE')

# URL prefix for public files that nginx will x-accel proxy
MP_URL_PUBLIC_XACCEL = '/public-x/'
if env.MP_IS_DJ_SERVER:
    MP_URL_PUBLIC_XACCEL = '/public/'

"""--------------------------------------------------------------------
    Protected Files

    The origin files are on S3, but may be hosted in 3 different ways
    depending on where this URL points:
     - CloudFront; CF distribution must have origins to correct S3 buckets
     - Nginx; Nginx URL must point to S3 buckets and be set to cache them
     - S3; dev cases only
"""

# General file settings
MP_FILE = ecs().load_value('MP_FILE')

# Settings related to protected files
MP_PROTECTED = ecs().load_value('MP_PROTECTED')

# This URL prefix for protected files will trigger nginx
# x-accel proxy IF files are routed through nginx vs cloudfront.
# Otherwise manage protected files locally for dev
MP_URL_PROTECTED_XACCEL = '/protected-x/'
if env.MP_IS_DJ_SERVER:
    MP_URL_PROTECTED_XACCEL = '/localprotected/'

"""--------------------------------------------------------------------
    Static File support

    'static' refers to any content served as-is by the web server.

    These files represent browser code and resources stored in revision
    control, and are always public (vs. protected content).

    Static files are served via the Django dev server in development,
    and via AWS Cloudfront with S3 origin.
    For Dev serving, files are loaded directly from folders.
    For AWS Django collectstatic moves files into S3 location after
    transpile/compression processes (see fab static).
"""

# Ways to find static files. Look first in the set of folders
# defined in STATICFILES_DIRS, then in app directories.
# The compressor and CSS finders get processed files.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    'sass_processor.finders.CssFinder',
     )

# File locations where files will be included as static content;
# these are the locations searched by FileSystemFinder
# Ordering is important for any overrides, as the first file found
# with the same relative pathname will be used
STATICFILES_DIRS = [
    # MPF javascript, css, and other content
    mpframework_path('static'),
    ]

"""--------------------------------------------------------------------
    Static and Media folders

    Static files (whether compressed or not) are moved under the static
    folder to be loaded by MPF. This includes MPF public files AND
    3rd party static files managed by MPF.

    Normal prod config is all "static" content is hosted public Cloudfront
    from the "Public" S3 bucket -- files are updated to S3 via the
    static compress/collect command using django-storages.

    In local dev DJ searches these static folders for each request.
    The local static folder is for testing static compress/collect for local
    dev, or with Nginx server hosting static from it's own local folder.
    This may be done to test JS compression, or remove S3 from loop
"""
_static_folder = '_static'

# Add any sandbox namespace to support multiple profiles sharing bucket
MP_PUBLIC_STATIC_FOLDER = join_urls( env.MP_PLAYPEN_STORAGE, _static_folder )

# How big a public media upload is before placed on disk, and where it is put
FILE_UPLOAD_MAX_MEMORY_SIZE = ecs().load_value('FILE_UPLOAD_MAX_MEMORY_SIZE')
FILE_UPLOAD_TEMP_DIR = work_path( env.MP_PLAYPEN_STORAGE, 'temp' )

# Django setting for location of files if they are to be served locally,
# which will be used if doing a local static compress/collect
# Can also be used to host public files from nginx (not a normal config)
STATIC_ROOT = work_path( MP_PUBLIC_STATIC_FOLDER )
MEDIA_ROOT = work_path( env.MP_PLAYPEN_STORAGE )

# Are public files hosted through AWS?
if env.MP_CLOUD:

    # Static file manager that knows how to put files on S3
    STATICFILES_STORAGE = 'mpframework.common.storage.mpS3StorageStatic'

    # MPF puts client items in Django static URL
    _static_url = 'https://{}'.format( env.MP_ROOT_URLS['URL_STATIC'] )
    STATIC_URL = join_urls( _static_url, MP_PUBLIC_STATIC_FOLDER, append_slash=True )
    MEDIA_URL = join_urls( _static_url, env.MP_PLAYPEN_STORAGE, append_slash=True )

# Otherwise using local static files -- could be with nginx or DJ runserver
else:
    parent = '/{}'.format( env.MP_URL_PUBLIC_DIRECT )
    STATIC_URL = join_urls( parent, _static_folder, append_slash=True )

    # HACK - place media next to static to support static moving test fixture files
    DEV_MEDIA_UNDER_STATIC = 'public_uploads'
    MEDIA_URL = join_urls( parent, DEV_MEDIA_UNDER_STATIC, append_slash=True )

    # This storage manager knows how to compress files locally
    STATICFILES_STORAGE = 'mpframework.common.storage.mpLocalStorageStatic'

# Files to never load into static folder location
MP_DEPLOY_STATIC_IGNORE_ALWAYS = (
    # Sass files are compiled ahead of time
    '*.sass',
    '*.scss',
     )
# Files to not load when compression is turned on
MP_DEPLOY_STATIC_IGNORE_COMPRESS = (
    # These script folders are included in the minimzed compress files
    'mpf-js',
    'admin',
    )

# HACK - using Django static hosting to serve files
# Local protected folder for file serving files in some dev environments
MP_FOLDER_PROTECTED_LOCAL = work_path( env.MP_PLAYPEN_STORAGE,
            _static_folder, 'protected_uploads' )

#--------------------------------------------------------------------
# MPF adaptation of Django S3Direct settings

if env.MP_CLOUD:
    MP_AWS_S3DIRECT_DESTINATIONS = {
        'protected': {
            'auth': lambda user: user.is_staff,
            'bucket': MP_AWS_BUCKET_PROTECTED,
            'S3accel': True,
            'allowed': '*',
            'content_length_range': ( 10, 2 * 10 ** 10 ),
            },
        'public': {
            'auth': lambda user: user.is_staff,
            'bucket': MP_AWS_BUCKET_PUBLIC,
            'S3accel': True,
            'allowed': '*',
            'content_length_range': ( 50, 10 ** 8 ),
            },
        }
else:
    # Non-AWS settings for basic testing
    MP_AWS_S3DIRECT_DESTINATIONS = {
        'test': {
            'auth': lambda user: user.is_staff,
            'bucket': 'TEST',
            'S3accel': False,
            'allowed': '*',
            'content_length_range': ( 10, 20000 ),
            },
        }
