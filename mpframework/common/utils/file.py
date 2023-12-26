#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared file-related utilities
"""
import os
import errno
from hashlib import sha1
from django.conf import settings

from .. import log
from . import get_random_key
from . import timestamp


def unique_name( orig_name, use_time=False, playpen=False, hash=False,
                 orig_len=48, remove_spaces=True ):
    """
    Make a name unique for use on shared file systems, S3, etc.

    Name has no spaces and is intended for one-time creation and then storage
    in the DB -- THE STRING CANNOT BE RECREATED

    By default the start of the string is kept as an admin convenience, and
    a random key are added. A timestamp and playpen can also be added.
    The result may optionally be hashed (or forced by profile setting).
    If the name has a . suffix such as file type, it will always be preserved
    """
    name, ext = os.path.splitext( orig_name )
    if remove_spaces:
        name = name.replace(' ', '')

    # Add key to fragment, and optional timestamp and playpen
    rv = '{}{}{}'.format( name[ :orig_len ], SEPERATOR, get_random_key( 6 ) )
    if playpen:
        rv = '{}_{}'.format( settings.MP_PLAYPEN, rv )
    if use_time:
        rv = timestamp( fmt='%Y-%m%d-%H%M%S_{}' ).format( rv )

    # Hashed name; only take part of the hash, as it is a sanity check
    if hash or settings.MP_HASH_UNIQUE_NAMES:
        rv = sha1( rv.encode( 'utf-8', 'replace' ) ).hexdigest()[:32]

    # New name and original extension
    rv = '{}{}'.format( rv, ext )

    log.debug2("New unique name: %s -> %s", orig_name, rv)
    return rv

SEPERATOR = '__mp'

def unique_name_reversible( name ):
    # Don't make name unique if it was already
    if SEPERATOR in name:
        return name
    else:
        return unique_name( name, orig_len=64, remove_spaces=False )

def reverse_orig_name( name ):
    # This won't replace spaces, but should be recognizable as the original
    name, ext = os.path.splitext( name )
    return '{}{}'.format( name.split( SEPERATOR )[0], ext )


def file_size_mb( size ):
    """
    Provide standard TEXT description of file size in MB given byte size
    """
    if not size:
        return ''
    if size < 1000000:
        size = "< 1"
    else:
        size = size // 1000000
    return "{}MB".format( size )


def create_file_from_post( file_data, local_path ):
    """
    Save a file locally from a file_data post, returning the local path
    file_data may be an in-memory file or a temp file; act appropriately
    """
    if getattr( file_data, 'temporary_file_path', None ):
        log.debug("Upload used on-disk temporary file: %s", local_path)
        local_path = file_data.temporary_file_path()
    else:
        log.debug("Upload used in memory file, writing to disk: %s", local_path)
        local_folder, _file = os.path.split( local_path )
        create_local_folder( local_folder )

        # Write the uploaded file into local server upload location
        with open( local_path, 'wb+' ) as upload_file:
            for chunk in file_data.chunks():
                log.debug_on() and log.debug2("file chunk: %s -> %s", local_path, len(chunk))
                upload_file.write( chunk )

    log.info("LOCAL UPLOAD: %s", local_path)
    return local_path


def create_local_folder( path ):
    """
    Safe creation of folder on local server/machine, even if it exists
    """
    log.debug("Creating local folder: %s", path)
    try:
        os.makedirs( path )
        log.info2("Created folder: %s", path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise Exception("CREATE FOLDER {} -> {}".format(path, e))
