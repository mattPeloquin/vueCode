#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extensions to Django-compressor offline compression

    Designed to be used with the static_compress
    command to force offline compression of template files
    with the extension "chtml"
"""
from urllib.request import url2pathname
from django.conf import settings

from compressor.js import JsCompressor
from compressor.css import CssCompressor
from compressor.templatetags.compress import CompressorNode

from mpframework.common import log
from mpframework.common.compat import compat_static
from mpframework.common.compat import compat_public


def offline_contexts():
    """
    Setup normal and compatability offline context for compressor
    """
    for context in [ settings.TEMPLATE_OFFLINE_CONTEXT,
                     _comp_context ]:
        yield context

_comp_context = {}
for key, item in settings.TEMPLATE_OFFLINE_CONTEXT.items():
    if isinstance( item, str ):
        _comp_context[ key ] = compat_static( item )
    else:
        _comp_context[ key ] = item


class mpCompressorMixin:
    """
    Override some file processing in the Compressor class
    """

    def get_filename(self, basename):
        """
        Implement Compressor get_filename to return full path
        to files by always using the static finders to find
        files in the source folders vs. looking in static locations
        first. This is how prod configs worked anyway, and for
        local dev this ensures local compress scenarios mimic prod.

        This file resolution is used BOTH for creating compressed files
        AND for calculating manifest hash every time compressed file
        is loaded by looking up every file.

        MPF uses template caching with most compressed blocks,
        so overhead is only on first hit for a given cache context.
        However overriding to gain more control over where a server
        looks for the files to include in compression.
        """
        return self.finders.find( url2pathname(basename) )

    def get_basename( self, url ):
        """
        Override to remove EITHER the normal or compatibility public url
        """
        try:
            base_url = self.storage.base_url
        except AttributeError:
            base_url = settings.COMPRESS_URL
        if settings.MP_ROOT_URLS['URL_STATIC_COMP'] in url:
            base_url = compat_public( base_url )
        return url.replace( base_url, '' )

    def output_file( self, mode, content, forced=False, basename=None ):
        """
        Override compressor offline processing to create TWO entries
        in the manifest to support normal and compatibility versions.
        """

        # Add profile to compressed file to ensure no collisions between profiles
        basename = '{}_{}'.format( settings.MP_PROFILE_FULL, settings.MP_CODE_CURRENT )

        rv = super().output_file( mode, content, forced, basename )

        # HACK - Make manifest use the compatibility url when needed by checking the
        # rendered content to see if it referenced the compatibility url
        if settings.MP_ROOT_URLS['URL_STATIC_COMP'] in self.context:
            rv = compat_public( rv )

        log.debug("Compress node: %s", rv)
        return rv

class mpJsCompressor( mpCompressorMixin, JsCompressor ):
    pass

class mpCssCompressor( mpCompressorMixin, CssCompressor ):
    pass


class mpCompressorNode( CompressorNode ):

    def render( self, context, forced=True ):

        # Short-circuit if compression type is not enabled
        if ( self.kind == 'css' and not settings.MP_COMPRESS['CSS'] ) or (
                self.kind == 'js' and not settings.MP_COMPRESS['JS'] ):
            return self.get_original_content( context )

        return self.render_compressed( context, self.kind, self.mode, True )

    @property
    def compressors( self ):
        return {
            'js': 'mpframework.common.template.mp_compressor.mpJsCompressor',
            'css': 'mpframework.common.template.mp_compressor.mpCssCompressor',
            }

