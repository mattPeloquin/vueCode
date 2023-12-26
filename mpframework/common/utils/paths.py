#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    File and path utilities
"""
import os
import re


_reduce_slashes = re.compile( r'(?<!:)[/]+' )
_bad_chars = re.compile( r'[<>\|]+' )


def path_clean( path ):
    """
    Clean path (file or url) to covert all slashes to Linux format,
    and make a name compatible on S3, Linux, and Windows
    """

    # Ensure path will be manipulated as unicode
    rv = str( path )

    # Convert backslashes to forward slashes
    rv = rv.replace( '\\', '/' )

    # Reduce duplicate forward slashes
    rv = _reduce_slashes.sub( '/', rv )

    # Remove potentially troublesome chars for file names
    # http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMetadata.html
    rv = _bad_chars.sub( '_', rv )

    return rv

def join_paths( *fragments ):
    """
    Some additions to os.path.join to safely join paths
    If a fragment that is not the first has a beginning slash, strip it
    so os.path.join won't treat it as an absolute path
    """
    first = fragments[0] if fragments and fragments[0] else ''
    remaining = [ str( fragment ).strip( os.sep ) if fragment else '' for fragment in fragments[1:] ]
    return path_clean( os.path.join( first, *remaining ) )

def path_extension( path ):
    if path:
        fragments = path.split('.')
        if fragments:
            return fragments[-1]
