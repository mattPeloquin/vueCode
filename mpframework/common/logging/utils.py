#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logging utilities
"""
import os
import logging
import itertools

from django.db import connections


# Process cache for loggers
_LOGGERS = {}

def get_logger( name ):
    """
    Do a pre-cache on getLogger caching, since MPF calls
    get_logger with every executed log call.
    """
    logger = _LOGGERS.get( name )
    if not logger:
        logger = logging.getLogger( name )
        if logger:
            _LOGGERS[ name ] = logger
    return logger

def db_queries():
    return list( itertools.chain(
                    *[ connections[n].queries for n in connections ] ) )

def find_caller( callee_name ):
    """
    Adaptation of Django logger findCaller

    Returns file, line, and fn name from the first stack frame that does
    not have callee_name in its file path
    """
    rv = "(unknown file)", 0, "(unknown function)"
    f = logging.currentframe()
    if f is not None:
        f = f.f_back
    while hasattr(f, 'f_code'):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        if callee_name in filename:
            f = f.f_back
            continue
        rv = (co.co_filename, f.f_lineno, co.co_name)
        break
    return rv

def find_obj( name ):
    """
    Returns the first object with the given name found on the stack

    HACK -- ONLY INTENDED FOR DEBUG LOGGING

    Throws exception if any problem is found along the way
    """
    f = logging.currentframe()

    def frame_valid():
        # Check the frame is valid
        valid = f and hasattr( f, 'f_code' )
        # Guard against recursion if call to the name triggers log call
        return valid and name not in f.f_code.co_name

    while frame_valid():
        obj = f.f_locals.get( name )
        if not obj:
            f = f.f_back
            continue
        break

    return obj


#--------------------------------------------------------------------
# Safe text dumps, which remove secrets

secret_items = ['key', 'pass', 'pwd', 'origin', 'sig', 'secret']

def is_secret( text ):
    """
    If text starts with any of the secret item text, assume it is secret
    Hiding is very important to prevent accidental exposure
    of credentials or sensitive information; may want to manage elsewhere
    """
    return any( item in text.lower() for item in secret_items )

def remove_secrets( item, include=None ):
    """
    Remove secrets from an item
    Designed to recursively search nested dicts for secrets, while sorting
    Can designate an include prefix to keep
    """
    if isinstance( item, dict ):
        new_item = {}
        for key, value in item.items():
            if isinstance( key, str ):
                if key.startswith('__') or (include and not key.startswith(include)):
                    continue
                if is_secret( key ):
                    value = '****'
            else:
                value = remove_secrets( value )
            new_item[ key ] = value
    else:
        new_item = item if not is_secret( str(item) ) else '****'
    return new_item


#--------------------------------------------------------------------

_pad_space = "  "

def pretty_print( item, padding=_pad_space ):
    """
    Expand dicts out for easier reading in debug, including
    dicts nested in other dicts or lists.
    Will attempt to sort dict keys and lists; if heterogenous
    data types will just use default.
    """
    from ..utils.strings import safe_unicode
    try:
        if isinstance( item, str ):
            return item

        pretty_list = []
        if isinstance( item, dict ):
            item_dict = item.copy()
            keys = list( item_dict )
            try:
                keys = sorted( keys )
            except Exception:
                pass
            for key in keys:
                value = pretty_print( item_dict[key], padding + _pad_space )
                pretty_list.append( "\n%s%s: %s" % (
                            padding, safe_unicode( key ), safe_unicode( value ) ))
        elif isinstance( item, (list, set) ):
            item_list = item.copy()
            try:
                item_list = sorted( item_list )
            except Exception:
                pass
            for list_item in item_list:
                if isinstance( list_item, dict ):
                    dict_text = pretty_print( list_item, padding + _pad_space )
                    pretty_list.append( "%s\n" % safe_unicode( dict_text ) )
                else:
                    pretty_list.append( "%s, " % safe_unicode( list_item ) )

        if pretty_list:
            return "".join( pretty_list )
        else:
            return item

    except Exception as e:
        return "PRETTY_PRINT_ERROR( %s )" % e
