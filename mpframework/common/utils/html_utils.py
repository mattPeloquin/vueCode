#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    HTML-related utilities
"""
import bleach


"""
    Standardize HTML sanitizing with bleach
    MPF allows HTML injection in some areas from staff input, so
    is by default much more permissive than the default bleach.
"""
TAG_WHITELIST = bleach.sanitizer.ALLOWED_TAGS + [
                'span', 'div', 'p', 'br',
                'article', 'section', 'main',
                'h1', 'h2', 'h3', 'h4',
                'img', 'video',
                'table', 'tbody', 'td', 'tr' ]
ATTR_WHITELIST = [ 'style', 'class', 'title' ]

def _styles():
    """
    HACK - create style "list" that always returns true
    This works around html5lib/bleach not taking a function for style types
    The default RE processing will catch malformed style, while valid-looking
    patterns that get through are not security risks.
    """
    class _Styles( list ):
        def __contains__( self, _style ):
            return True
    return _Styles([])

def sanitize_html( text ):
    return bleach.clean( text, tags=TAG_WHITELIST,
                attributes = { '*': ATTR_WHITELIST,
                    'a': [ 'href', 'target' ],
                    'img': [ 'src' ],
                    },
                styles=_styles() )


def textarea_px_from_attrs( attrs ):
    """
    HACK - Approximate initial textarea size before element dimensions known
    """
    width = 11 * int( attrs.get( 'cols', 80 ) )
    height = 18 * int( attrs.get( 'rows', 16 ) )
    return width, height
