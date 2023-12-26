#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    File and image form fields

    These are specified as the default widgets for model file
    fields, so normally don't need to defined in forms.
"""
from django import forms
from django.conf import settings

from ..widgets.file import S3DirectUpload
from ..widgets.file import mpFileWidget
from ..widgets.file import mpImageWidget


class _mpFileFormFieldMixin:
    widget = None

    def __init__( self, *args, **kwargs ):
        protected = kwargs.pop( 'protected', False )
        mpoptions = kwargs.pop( 'mpoptions', {} )

        # Setup direct widget if needed
        if kwargs.pop( 'direct', False ) and settings.MP_CLOUD:
            dest = 'protected' if protected else 'public'
            kwargs['widget'] = S3DirectUpload( dest=dest )
        else:
            kwargs['widget'] = self.widget

        super().__init__( *args, **kwargs )

        # Add mpoptions defaults, don't override ones set in widget
        mpoptions.update( self.widget.mpoptions )
        self.widget.mpoptions = mpoptions

    def to_python( self, data ):
        # Support modifying the file path as text in form, for root fixup
        if isinstance( data, str ):
            return data
        else:
            return super().to_python( data )

class mpImageFormField( _mpFileFormFieldMixin, forms.ImageField ):
    widget = mpImageWidget

class mpFileFormField( _mpFileFormFieldMixin, forms.FileField ):
    widget = mpFileWidget
