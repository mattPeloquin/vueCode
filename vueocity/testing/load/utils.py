#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared testing code
"""
import random


def get_from_dict( d, keysearch=None, valsearch=None ):
    """
    Return key and value for specific dict item that matches a search
    criteria for key and/or value. If neither provided, return random item.
    """
    if not d:
        return

    if not keysearch and not valsearch:
        random_key = random.choice( list( d ) )
        return d[ random_key ]

    for key, value in d.items():
        if keysearch in key or valsearch in value:
            return d[ key ]
