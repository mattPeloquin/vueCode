#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Image widget for working with public image resources
"""
import os
from urllib.parse import unquote_plus
from django.conf import settings
from django.forms.widgets import ClearableFileInput
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.urls import reverse

from s3direct.widgets import S3DirectWidget

from .. import log


class S3DirectUpload( S3DirectWidget ):
    """
    Use S3Direct to upload files directly to S3 on the web client in JS
    """
    upload_class = 'direct'

    # Force loading JS/CSS through framework
    class Media:
        js = ()
        css = {}

    def __init__( self, *args, **kwargs ):
        self.mpoptions = kwargs.pop( 'mpoptions', {} )
        super().__init__( *args, **kwargs )

    def render( self, name, value, attrs=None, **kwargs ):
        log.debug2("Rendering S3Direct: %s, %s -> %s", name, value, attrs)
        file_name = os.path.basename( unquote_plus(value.name) ) if value else ''
        output = render_to_string( 'widgets/s3direct.tmpl', {
            'name': name,
            'upload_class': self.upload_class,
            'policy_url': reverse('upload_metadata'),
            'signing_url': reverse('upload_signature'),
            'element_id': self.build_attrs(attrs).get('id', '') if attrs else '',
            'file_name': file_name,
            'file_url': value or '',
            'style': self.build_attrs(attrs).get('style', '') if attrs else '',
            'csrf_cookie_name': settings.CSRF_COOKIE_NAME,
            'dest': self.dest,
            })
        return mark_safe( output )


class _mpFileUpload( ClearableFileInput ):
    """
    Extends wrapping of Django file input

    FUTURE - replace with better file upload/crop
    """

    def __init__( self, *args, **kwargs ):
        self.mpoptions = kwargs.pop( 'mpoptions', {} )
        super().__init__( *args, **kwargs )

    def __deepcopy__( self, memo ):
        rv = super().__deepcopy__( memo )
        rv.mpoptions = self.mpoptions.copy()
        return rv

    def render( self, name, value, attrs=None, renderer=None ):
        """
        Always wrap the file widget in mp_upload tag
        """
        log.debug2("Rendering %s: %s, %s -> %s", self.__class__.__name__,
                    name, value, attrs)
        render = super().render( name, value, attrs=attrs )
        return '''
            <div class="mp_upload {}">
                <div class="mp_file_name">{}</div>
                {}
                </div>
            '''.format( self.upload_class, value or '', render )

    def is_initial( self, value ):
        """
        Force the initial template to always show, so placeholder HTML for
        dynamic updates is in place
        """
        return True

    def get_context( self, name, value, attrs ):
        """
        Add context for MPF widgets with additional options.
        """
        rv = super().get_context( name, value, attrs )
        rv.update( self.mpoptions )
        return rv


class mpFileWidget( _mpFileUpload ):
    template_name = 'widgets/file_upload.html'
    upload_class = 'file'
    clear_checkbox_label = u"clear file"

class mpImageWidget( _mpFileUpload ):
    """
    Force the widget to create anchor/image html even if empty, for
    easy support JS inflation of empty items on ajax updates.
    """
    template_name = 'widgets/image_upload.html'
    upload_class = 'image'
    clear_checkbox_label = u"clear image"
