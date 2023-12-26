#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account-specific context processors
"""

from mpframework.content.mpcontent.access import has_free_access

from .utils import get_au
from .access import get_apa_dicts


def account( request ):
    if request.is_lite or request.is_bad:
        return {}

    user = request.user
    if not user:
        return {}

    # FUTURE - load AU into request and optimize caching if needed every request

    # If a user account is present, add to context along with related settings
    au = get_au( user )
    if au:
        show_ga = au.is_group_admin()
    else:
        show_ga = user.access_staff_view and user.sees_group

    context = {
        'account_user': au,
        'ga_admin': show_ga,

        # Placeholder for unselected account for admin screens
        'account': { 'ga_id': '_' },

        # Send apa info the the client for UI access processing
        'access_apas': lambda: get_apa_dicts( user ),

        # Note if the site is free -- disallow staff check to
        # force use of access code on client
        'access_free_all': lambda: has_free_access( user, staff=False ),
        }

    return context

