#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Utilities for working with urls

    FUTURE - use urlobject for url manipulation
"""
import re
from urllib import parse
from django.http import QueryDict
from django.conf import settings

from .paths import path_clean


# Simple regex to detect IP4 and IP6 addresses
IP_RE = re.compile('''
           ( \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} ) |
            ( ([0-9A-Fa-f]{1,4}:+)+[0-9A-Fa-f]{1,4} )
            ''', re.VERBOSE )

_clean = ' /\\'


def append_querystring( url, **kwargs ):
    """
    Easy add for new and existing querystrings using QueryDict
    Returns url with new querystrings from kwargs safely added
    """
    chunks = url.split('?')
    path = chunks[0]
    qs = chunks[1] if len( chunks ) > 1 else ''
    qd = QueryDict( qs, mutable=True )
    qd.update( kwargs )
    if qd:
        rv = '{}?{}'.format( path, qd.urlencode() )
    else:
        rv = path
    return rv

def clean_url( url ):
    """
    Cleanup common items in urls that can come from user data;
    use this to create urls instead of just escaping spaces, etc.
    to keep urls generated from user data more readable
    """
    url = url if url else ''
    url = url.replace( ' ', '_' )
    return url

def join_urls( *fragments, **kwargs ):
    """
    Safe joining of path elements into a url format, preserving any
    querystring on the last element.
    Returns string in form /xxx/yyy/zzz
    (first slash present if in first fragment)
    """
    rv = ''
    if not fragments:
        return rv
    fragments = list(fragments)
    quote = kwargs.pop( 'quote', False )
    scheme = kwargs.pop( 'scheme', False )
    prepend_slash = kwargs.pop( 'prepend_slash', None )
    append_slash = kwargs.pop( 'append_slash', False )
    preserve_slash = kwargs.pop( 'preserve_slash', False )

    # Pop off query to allow path slash manipulation
    query = None
    last_frag = fragments.pop()
    if last_frag:
        query = last_frag.split('?')
        if len( query ) > 1:
            last_frag = query[0]
            query = query[1]
        else:
            query = None
        fragments.append( last_frag )

    if preserve_slash:
        append_slash = last_frag.endswith(('/', '\\'))

    # Find the first non-blank fragment, last, and remaining
    first = ''
    remaining = []
    for pos in range( 0, len( fragments ) ):
        first = str( fragments[pos] ).rstrip( _clean )
        if first:
            if prepend_slash is False:
                first = first.lstrip( _clean )
            if pos + 1 < len( fragments ):
                remaining = fragments[ (pos + 1): ]
            break

    if not remaining:
        rv = first
    else:
        # Keep left-hand slashes on first fragment, while removing
        # all slashes except in-between fragments, to allow for
        # any jumble of fragments with preceding/trailing slashes
        rest = '/'.join( str( frag ).strip( _clean ) for frag in remaining )
        rv = '/'.join([ first, rest ])

    rv = path_clean( rv )

    # Fixup with options
    if append_slash and not rv[-1] == '/':
        rv += '/'
    if quote:
        rv = parse.quote( rv )
    if scheme:
        if scheme is True:
            scheme = 'https'
        rv = '{}://{}'.format( scheme, rv )
    elif prepend_slash and not rv[0] == '/':
        rv = '/' + rv

    if query:
        '?'.join([ rv, query ])

    return rv

def cache_control_dict( browser_age, edge_age=None, name='cache-control',
            private=False ):
    """
    Returns a dict that can be added to metadata for files
    that will be hosted on cloudfront.
    NOTE -- setting private on will currently NEGATE Cloudfront caching
    """
    privacy = ',private' if private else ''
    browser_age = 0 if browser_age is None else browser_age
    edge_age = '' if edge_age is None else ',s-maxage={}'.format( edge_age )
    return {
        name: 'max-age={}{}{}'.format( browser_age, edge_age, privacy )
        }

def attachment_string( attachment ):
    """
    Provide clean attachment string for content-disposition.
    Pass True or filename to user existing or new filename
    """
    if not attachment:
        return 'inline'
    rv = 'attachment'
    if not attachment is True:
        filename = parse.quote( attachment )
        rv += ";filename*=utf-8''{}".format( filename )
    return rv

def get_url_list( urlpatterns=None, exclude_prefixes=None ):
    """
    Provide list of all url patterns by recursively enumerating them
    """
    urls = []

    if not urlpatterns:
        from mpframework.settings.urls import urlpatterns

    def add_urls( urllist, prefix='' ):
        for entry in urllist:
            if hasattr( entry.pattern, 'regex' ):
                url = entry.pattern.regex.pattern
            else:
                url = entry.pattern.describe
            url = prefix + url.strip('^').strip('$')
            if exclude_prefixes and any(
                    url.startswith( exclude ) for exclude in exclude_prefixes ):
                continue
            urls.append( url )
            if hasattr( entry, 'url_patterns' ):
                add_urls( entry.url_patterns, url )

    add_urls( urlpatterns )

    urls.sort()
    return urls
