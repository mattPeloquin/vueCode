#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extend django compressor tag

    MPF mostly uses django-compressor in the offline mode, which creates
    combined/compressed output of what is rendered between compression tags, and
    places it in a hashed file in the static location.
    Inline mode is used with template cached fragments to package and compress
    small amounts of JS and CSS code.

    A JSON manifest file is created (tied to profile/build) that uses hashes based
    on the FIRST LEVEL contents in the compression tag.
    At runtime, when a template render is requested, the first level contents in the
    compression tag are rendered to recreate hash, which is used used for lookup
    in the JSON manifest.

    MPF extends this process to include support for normal and
    compatibility urls for AWS deployments (isn't needed in local dev).
"""
from django import template

from mpframework.common.template.mp_compressor import mpCompressorNode


register = template.Library()


@register.tag
def compress_mp_inline( parser, token ):
    return _compress( parser, token, True )

@register.tag
def compress_mp( parser, token ):
    return _compress( parser, token )

def _compress( parser, token, inline=False ):
    nodelist = parser.parse( ('endcompress',) )
    parser.delete_first_token()

    args = token.split_contents()
    if not len( args ) in (2, 3):
        raise template.TemplateSyntaxError(
            "%r tag requires one, or two arguments." % args[0])

    # Bake mode into tag name
    mode = 'inline' if inline else 'file'

    # Instead of error handling, allow different modes to be passed through,
    # to allow for different templates of name compress/[js|css]_[mode].html
    kind = args[1]
    name = args[2] if len(args) >= 3 else None

    return mpCompressorNode( nodelist, kind, mode, name )
