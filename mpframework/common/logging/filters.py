#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logging Filters
"""
from logging import Filter
from django.conf import settings


# Debug stack trace to identify specific SQL source calls
_STACK = None
#_STACK = "contentuser"

class SqlFilter( Filter ):
    """
    Better log formatting of Django SQL queries
    """

    def filter( self, record ):
        message = getattr( record, 'sql', None )
        if not message or hasattr( record, 'mp_sql_processed' ):
            return True
        try:
            if _STACK and _STACK in message:
                from .. import log
                log.debug_stack( 24, 11 )

            # Make formatting easier to read
            message = message.replace("QUERY = '", "")
            message = message.replace("SELECT",     "\nSELECT")
            message = message.replace("INSERT",     "\nINSERT")
            message = message.replace("UPDATE",     "\nUPDATE")
            message = message.replace("DELETE",     "\nDELETE")
            message = message.replace("FROM",       "\n   FROM")
            message = message.replace("WHERE",      "\n   WHERE")
            message = message.replace("VALUES",     "\n   VALUES")
            message = message.replace("INNER JOIN", "\n    INNER JOIN")
            message = message.replace("LEFT OUTER JOIN", "\n    LEFT OUTER JOIN")

            # Replace some app names to cut down on verbosity
            names = [
                    'ops',
                    'tenant',
                    'user',
                    'mpcontent',
                    'sitebuilder',
                    'portal',
                    'catalog',
                    'account',
                    ]
            for name in names:
                # Remove the "app_" prefix from field names
                message = message.replace('"' + name + '_', '"')
                message = message.replace('`' + name + '_', '`')
            for name in names:
                # Remove the remaining "table." from field names
                message = message.replace('"' + name + '".', '')
                message = message.replace('`' + name + '`.', '')

            record.sql = message
            record.mp_sql_processed = True

        except Exception as e:
            print("Error in SQL logging: %s" % e)
            if settings.MP_DEV_EXCEPTION:
                raise
        return True

