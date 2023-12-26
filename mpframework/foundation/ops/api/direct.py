#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for S3Direct integration with framework, which is used
    for staff uploads (user uploads just post).

    FUTURE SECURE - Tighten CORS policy on the S3 buckets

    PORTIONS ADAPTED FROM OPEN SOURCE:
        Unfortunately S3Direct did not have any way to hook or override the
        generation of file path based on request, short of ugly monkey patch.
        So adapted and simplified view to support MPF tenancy and security.
        https://github.com/bradleyg/django-s3direct
"""
from urllib.parse import unquote
from datetime import datetime
from django.conf import settings
from django.views.decorators.http import require_POST

from s3direct.utils import get_aws_v4_signature
from s3direct.utils import get_aws_v4_signing_key

from mpframework.common import log
from mpframework.common.api import respond_api
from mpframework.common.aws.secrets import aws_s3_upload_credentials
from mpframework.common.aws.s3 import cache_control_public
from mpframework.common.aws.s3 import cache_control_protected
from mpframework.common.utils import join_urls
from mpframework.common.utils.file import unique_name_reversible
from mpframework.common.view import staff_required


@require_POST
@staff_required
def upload_signature( request ):
    """
    Get signature needed for secure upload.
    Moved this here for more control, less settings setup
    """
    message = unquote( request.POST['to_sign'] )
    signing_date = datetime.strptime( request.POST['datetime'], '%Y%m%dT%H%M%SZ' )
    _key, secret = aws_s3_upload_credentials()
    signing_key = get_aws_v4_signing_key( secret, signing_date,
                settings.MP_AWS_INSTANCE['region'], 's3' )
    sig = get_aws_v4_signature( signing_key, message )
    return respond_api({
        's3ObjKey': sig,
        })

@require_POST
@staff_required
def upload_metadata( request ):
    """
    Create information needed by client code to perform the upload to S3.
    Setting up the file key is the focal point of changes here.
    """
    target = request.POST['dest']

    # Validate destination config:
    dest = settings.MP_AWS_S3DIRECT_DESTINATIONS[ target ]
    auth = dest['auth']
    if auth and not auth( request.user ):
        log.info2("SUSPECT - Direct AWS permission denied")
        return respond_api( False )

    # Validate file posted with request
    file_type = request.POST['type']
    allowed = dest['allowed']
    if( allowed and file_type not in allowed ) and allowed != '*':
        return respond_api( status=403,
                    error=u"Invalid file type {}".format( file_type ) )

    file_size = int( request.POST['size'] )
    length_range = dest['content_length_range']
    if length_range and not ( length_range[0] <= file_size <= length_range[1] ):
        return respond_api( status=403,
                    error="Invalid file size: {:n} "
                        "(must be between {:n} and {:n} bytes)".format(
                        file_size, length_range[0], length_range[1] ) )

    # Generate file path to store file in provider's protected content area
    # Don't care about what type of file it is, just store it
    file_name = request.POST['name']

    # HACK - disable S3 file mangling for certain file types
    # FUTURE - Drive this from logic in the content type, which will require
    # passing content type through the S3 upload process
    if not any( file_name.endswith( ext ) for ext in
                settings.MP_FILE['NO_MANGLE_TYPES'] ):
        file_name = unique_name_reversible( file_name )

    if target == 'public':
        file_path = request.sandbox.public_storage_path
    else:
        file_path = request.sandbox.provider.protected_storage_path
    file_key = join_urls( file_path, file_name )
    log.debug("Direct File upload key: %s -> %s", request.mpipname, file_key)

    access_key, _secret = aws_s3_upload_credentials()

    # Send info back to the client so it can do signing and send file to S3
    upload_data = {
        'object_key': file_key,
        'access_key_id': access_key,
        'region': settings.MP_AWS_INSTANCE['region'],
        'bucket': dest['bucket'],
        'acl': 'private',

        # Type is left blank for S3 to determine

        # The metadata set here cannot be changed
        'allow_existence_optimization': False,

        # Set default cache parameters; overridden in CF
        'cache_control': ( cache_control_public() if target == 'public' else
                            cache_control_protected() ),
        }
    return respond_api( upload_data )
