#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for reports
"""

def email_host( email ):
    return str( email ).split('@')[ -1 ]

def email_group( email ):
    return '.'.join( email_host( email ).split('.')[ :-1 ] )
