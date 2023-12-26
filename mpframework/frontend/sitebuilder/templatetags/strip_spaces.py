#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tag using variable to control striping of unneeded HTML whitespace

    Inspired by spaceless tag and public domain code from Django Snippets:
        http://djangosnippets.org/_/547/
        http://djangosnippets.org/_/2405/
"""
import re
from django import template
from django.conf import settings
from django.utils.functional import keep_lazy_text

from mpframework.common import log
from mpframework.common.utils.strings import safe_unicode


# Tell django this module exists for loading with {% load strip_spaces %}
register = template.Library()

class SpacelessNode( template.Node ):
    """
    Strip spaces from context if compress variable from context is true
    """

    def __init__( self, nodelist, compress_on=False ):
        self.nodelist = nodelist
        self.compress_on = compress_on    # This is name of context var

    def render( self, context ):
        """
        Override rendering to run custom space stripping after Django render
        """
        content = self.nodelist.render( context )

        # Extra processing can be short-cicuited for debug
        if not settings.MP_COMPRESS['SPACE_STRIP']:
            return content

        # Load compress context variable
        try:
            compress = self.compress_on.resolve( context )
        except Exception:
            log.debug2("Skipping compress because compress_on not in context")
            compress = False

        # Render down result based on compression setting
        return _strip_spaces( content, compress )

@register.tag
def strip_spaces( parser, token ):
    """
    Use as Django's spaceless tag, but with a variable that turns the
    spaceless compression on or off
    """
    contents = token.split_contents()

    # Get the compress variable out of context values if present
    compress = contents[1] if len(contents) > 1 else False
    compress_on = template.Variable( compress ) if compress else False

    # Cleanup tag
    nodelist = parser.parse( ('end_strip_spaces',) )
    parser.delete_first_token()

    return SpacelessNode( nodelist, compress_on=compress_on )

"""
    For compression, strip as many spaces and newlines as possible

     1) CANNOT strip inside textareas
     2) Since JS style isn't using ';', cannot strip newlines in JS

    FUTURE - until webpack approach is used, the compression on
    dynamic content is limited to removing whitespace.
"""
_compress_strip = (
    ( re.compile(r'^\s+', re.MULTILINE), '' ),  # Leading whitespace, lines
    ( re.compile(r'>\s+<', re.MULTILINE), '><' ),  # Whitespace between html
    )

# In non-compress, take out extra blank lines
_nocompress_strip = (
    ( re.compile( r'^\s+$', re.MULTILINE ), '' ),
    )

@keep_lazy_text
def _strip_spaces( html_text, compress ):
    """
    Returns the given HTML with unneeded spaces removed
    """
    rv = safe_unicode( html_text )
    orig_len = len(rv)

    patterns_to_strip = _compress_strip if compress else _nocompress_strip
    for pattern, sub in patterns_to_strip:
        rv = re.sub( pattern, sub, rv )

    log.debug_on() and log.debug2("strip_spaces: %s -> %s", orig_len, len(rv))
    return rv
