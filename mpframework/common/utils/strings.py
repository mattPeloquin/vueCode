#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    String utilities
"""
import re
from django.conf import settings
from django.utils.encoding import force_str


def safe_unicode( obj ):
    """
    Guarantee a unicode string for any output without exceptions
    """
    try:
        return force_str( obj )
    except UnicodeDecodeError:
        if settings.MP_TESTING:
            raise
    return force_str( obj, errors='ignore' )

def bool_convert( value ):
    """
    Guarantee coversion of boolean from a potentially string-like value
    """
    return str( value ).lower() in [
                'true', '1', 'yes', 'on' ] if value else False

def wb( expression ):
    return u"Yes" if bool( expression ) else u"No"

def replace_text_tags( text, text_tags=None ):
    """
    Fill in any tags defined in settings in the text string
    """
    text_tags = text_tags or settings.MP_UI_TEXT
    rv = text
    for key, value in text_tags.items():
        if key in rv:
            rv = rv.format( **{ key: value } )
    return rv

def make_tag( text, max_len=None, under=False, lower=False ):
    """
    Support various conversions of string into tag, code or slug-like string.
    Remove spaces and definite articles, process according to options
    """
    text = safe_unicode( text ).strip()
    words = [ word for word in text.split(' ') if
                word.lower() not in make_tag.DEFINITE_ARTICLES ]
    rv = ('_' if under else '').join( words )
    if max_len:
        rv = rv[ :max_len ]
    if lower:
        rv = rv.lower()
    return rv
make_tag.DEFINITE_ARTICLES = [ 'the', 'a' ]

def truncate( string, max_len, ending=u"..." ):
    if len( string ) > max_len:
        string = string[ :(max_len - len(ending)) ]
        string = "{}{}".format( string, ending )
    return string

def close_compare( s1, s2 ):
    """
    Returns true of any number of given strings match, not including
    whitespace. Falls back to python != if both are not strings.
    """
    if isinstance( s1, str ) and isinstance( s2, str ):
        s1 = close_compare.regex.sub('', s1)
        s2 = close_compare.regex.sub('', s2)
    return s1 == s2
close_compare.regex = re.compile( r'[\s]+', re.MULTILINE )

#--------------------------------------------------------------------------------------

def comma_tuple( string ):
    """
    Returns cleaned and lowered tuple of strings from comma-delimited string
    """
    items = str( string ).split(',') if string else []
    return tuple( str( item ).strip().lower() for item in items )

def union_comma_lists( *args ):
    """
    Given list of comma-delimited strings, return comma list of the union
    all, with duplicates removed (case insensitive).
    """
    sets = comma_lists_to_sets( *args )
    if sets:
        rv = sets[0]
        for s in sets[1:]:
            rv |= s
        return rv

def intersection_comma_lists( *args ):
    """
    Given list of comma-delimited strings, return true if any values
    occur in all lists (case insensitive).
    """
    sets = comma_lists_to_sets( *args )
    if sets:
        rv = sets[0]
        for s in sets[1:]:
            rv &= s
        return rv

def comma_lists_to_sets( *strings ):
    """
    Return list of sets that contain cleaned up and stripped strings
    """
    if len( strings ) > 1:
        rv = []
        for string in strings:
            rv.append( set( comma_tuple( string ) ) )
        return rv