#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Form mixins
"""
from django.core.files.uploadedfile import UploadedFile

from .. import log
from ..utils.html_utils import sanitize_html


class mpFileFieldFormMixin:
    """
    Support for managing uploaded file metadata
    HACK - assumptions about field setup and naming are used
    """

    def clean( self ):
        """
        Setup file sizes for registered file fields
        """
        for name, item in self.cleaned_data.items():
            # Override size with file size if new upload
            if isinstance( item, UploadedFile ):
                model_field = self.instance._meta.get_field( name )
                if getattr( model_field, 'mpfile', None ):
                    log.debug("Setting file bytes: %s", item)
                    self.cleaned_data[ name + '_bytes' ] = item.size

        return super().clean()


class mpHtmlFieldFormMixin:
    """
    Shared form code for dealing with HTML in field values
    """
    sanitize_html_fields = ()

    def clean( self ):
        """
        Sanitize designated html fields when posted to resolve any issues with
        bad or malformed input. Handling here to provide single cleaning, point
        and to provide user feedback on changes made to their text.
        """
        rv = super().clean()
        if not self.sandbox or self.sandbox.policy.get('site_limits.clean_html'):
            for name, item in self.cleaned_data.items():
                if name in self.sanitize_html_fields:
                    self.cleaned_data[ name ] = sanitize_html( item )
        return rv
