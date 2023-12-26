#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Editor upload implementation

    Editor uploads are one-time; there is no file management supported on the
    server; a unique name is created, and will be abandoned if upload happens again.

    The editor integrates with MPF's Public and Protected storage,
    but to simplify usage, the type of class the editor is being used
    with is not tracked.

    Since some editor items have Sandbox scope and some have Provider,
    ALL editor uploads are placed in the Public or Protected
    PROVIDER storage location.
"""
import json
from django import forms
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.http import HttpResponseForbidden

from mpframework.common import log
from mpframework.common.api import respond_api
from mpframework.common.utils import join_urls
from mpframework.common.utils.file import unique_name
from mpframework.common.utils.strings import bool_convert
from mpframework.common.storage import public_storage
from mpframework.common.storage import protected_storage
from mpframework.common.view import staff_required


IMAGE_TYPES = ['image/png', 'image/gif', 'image/jpg', 'image/jpeg', 'image/x-icon']

UPLOAD_FOLDER = 'editor'

# HACK - the URL offset that the HTML editor frames are loaded into relative
# from the root url. This allows for protected file references to be adjusted
# in the editor so the urls can display correctly
PROTECTED_FOLDER_HACK = '../..'

class FileForm( forms.Form ):
    file = forms.FileField()

@require_POST
@staff_required
def upload_file( request, protected=False, link=False, image=False ):
    """
    View for processing file upload requests for the HTML editor
    """
    sandbox = request.sandbox
    assert sandbox

    protected = bool_convert( protected )
    link = bool_convert( link )
    image = bool_convert( image )

    form = FileForm( request.POST, request.FILES )
    if form.is_valid():
        file = form.cleaned_data['file']
        log.debug("Upload file request: %s -> %s -> protected:%s, link:%s, image:%s",
                    sandbox, file.name, protected, link, image)

        if image and file.content_type not in IMAGE_TYPES:
            log.info("CONFIG - Image upload rejected due to type: %s -> %s",
                            request.mpipname, file.name)
            return HttpResponse("Bad image format")

        file_url = _save_file( sandbox, protected, file )

        if link:
            return HttpResponse( file_url )
        else:
            return respond_api({ 'filelink': file_url, 'filename': file.name })

    return HttpResponseForbidden()

def _path( sandbox, protected, file ):
    """
    Create editor path based on public/protected, add underscore in public to
    separate it from sandbox names
    """
    storage_path = ( sandbox.provider.protected_storage_path if protected else
                     sandbox.provider.public_storage_path )
    upload_folder = '{}{}'.format( '' if protected else '_', UPLOAD_FOLDER )
    return join_urls( storage_path, upload_folder, unique_name( file.name ) )

def _save_file( sandbox, protected, file ):
    """
    All editor files are stored under the provider folder
    """
    path = _path( sandbox, protected, file )
    log.debug("Editor saving file: %s -> %s", sandbox, path)

    storage = protected_storage if protected else public_storage

    file_path = storage.save( path, file )
    file_url = storage.url( file_path )

    if protected:
        file_url = join_urls( PROTECTED_FOLDER_HACK, file_url )

    log.info("Editor upload: %s -> %s -> %s", sandbox, file_path, file_url)

    return file_url
