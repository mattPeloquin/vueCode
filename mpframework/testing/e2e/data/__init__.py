#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    E2E test data templates
    This folder holds dicts used to create randomized test data.
"""
import random
from decimal import Decimal
from decimal import ROUND_DOWN

from django.utils.crypto import get_random_string

from .content import *
from .users import *
from .files import *


# TESTWORK - Change this to env var
_UNICODE_ON = False


def get_unique_dict( data, group='ALL' ):
    """
    Grab a top-level data dict from given dict group and create a
    new group count for the new item
    """
    _key, data_dict = random.choice( data.items() )
    _increment_count( group )
    return get_unique_data( data_dict, group )

def get_unique_data( data_dict, group='ALL' ):
    """
    Given a data_dict with an arbitrarily nested set of dictionaries,
    return a copy updated with the current random tag and group count
    """
    def _unique_dict( orig ):
        # Support nested dictionary recursion
        rv = {}
        for key, value in orig.items():
            if isinstance( value, dict ):
                rv[ key ] = _unique_dict( value )
            else:
                rv[ key ] = randomize_string( value, _unique_tag( group ),
                                              _unique_tag( group, ascii=True ) )
        return rv
    return _unique_dict( data_dict )

def randomize_string( value, default='', ascii='' ):
    """
    Use the lambda function replacement tags to provide randomized values for
    each occurrence of a tag in a string
    """
    while True:
        tag_used = False
        # Do default replacement first
        if '{}' in value:
            value = value.replace( '{}', default )
            continue
        if '{ascii}' in value:
            value = value.replace( '{ascii}', ascii )
            continue
        # Then do random tags one at a time until all gone
        for tag, fn in _tags.items():
            if tag in value:
                value = value.replace( tag, str( fn() ), 1 )
                tag_used = True
        if not tag_used:
            break
    return value

_tags = {
    '{price}': lambda: Decimal( random.random() * random.randint(1,9999) )
                                .quantize( Decimal('.01'), rounding=ROUND_DOWN ),
    '{time}': lambda: random.randint( 10, 99 ),
    '{txt}': lambda: get_random_text(  ),
    '{int}': lambda: random.randint( 0, 99999999 ),
    '{i64}': lambda: random.randint( 1, 64 ),
    '{i255}': lambda: random.randint( 0, 255 ),
    '{f1}': lambda: random.random(),
    '{image_file}': lambda: random.choice( IMAGE_FILES ),
    '{content_file}': lambda: random.choice( CONTENT_FILES ),
    '{video_file}': lambda: random.choice( VIDEO_FILES ),
    '{audio_file}': lambda: random.choice( AUDIO_FILES ),
    }

"""
    Provide unicode UTF-8 random string
    Add spaces and use latin alphabet more frequently
    By default don't choose characters that can mess up HTML properties
"""
def get_random_text( length=None, spaces=True, exclude='' ):
    length = length or random.randint( 1, 512 )
    string = []
    while len( string ) < length:
        if spaces and not random.randint( 0, 5 ):
            string.append(' ')
        else:
            char = random.choice( _chars )
            if char not in exclude:
                string.append( char )
    return ''.join( string )

# Inspired by Stack Overflow:
# https://stackoverflow.com/questions/1477294/generate-random-utf-8-string-in-python
_unicode_ranges = [
    # Skip characters need to be escaped for CSS names for simplicity
    ( 0x0030, 0x0039 ), # Numbers
    ( 0x0030, 0x0039 ), # Numbers
    ( 0x0041, 0x005A ), # Make latin more prominant
    ( 0x0041, 0x005A ), # Make latin more prominant
    ( 0x0061, 0x007A ), # Make latin more prominant
    ( 0x0061, 0x007A ), # Make latin more prominant
    ( 0x0061, 0x007A ), # Make latin more prominant
    ]
if _UNICODE_ON:
    _unicode_ranges += [
        ( 0x00A1, 0x00FF ), # Everything above 00A1 is okay for HTML class attrs

        # FUTURE - JSON conversion on Linux servers not sending all unicode correctly
        ( 0x0100, 0x024F ), # Grab everything through Arabic
        ( 0x0370, 0x06FF ), # skipping symbols in middle
        ( 0x6300, 0x63FF ), # Grab some CJK
        ]

_chars = [
    unichr( code_point ) for current_range in _unicode_ranges
            for code_point in range( current_range[0], current_range[1] + 1 )
    ]

"""
    Each time tests are run, create a random string to share across tests
    and also keep track of count of each group
"""
TEST_SESSION = get_random_string( 2 ) + get_random_text( 3, spaces=False )
TEST_SESSION_ASCII = TEST_SESSION[:2]
counts = {}

def _unique_tag( group, ascii=False ):
    return '{}-{}'.format( counts[ group ],
                            TEST_SESSION_ASCII if ascii else TEST_SESSION )

def _increment_count( group ):
    global counts
    if group in counts:
        counts[ group ] = counts[ group ] + 1
    else:
        counts[ group ] = 1
    return counts[ group ]
