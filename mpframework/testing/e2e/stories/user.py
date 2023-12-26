#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User creation and management
"""

from ..blocks import UserBlock
from ..data import *


def login_user( stc, user=None ):
    """
    Logs in the given user, or creates new one
    """
    if not user:
        user = UserBlock( stc )
    user.login()
    return user


def new_staff( stc, data=None, promoting_staff=None, login=True ):
    """
    Returns a user block for a new staff member
    Logs in a new user, and then promotes them to staff using
    the provided promoting staff, or the default sandbox owner if none
    """
    if not data:
        data = get_unique_dict( STAFF )

    # Create the user by going through the create screen screen
    ub = UserBlock( stc, data )

    # Log staff back in to promote new user
    if promoting_staff:
        promoting_staff.login()
    else:
        stc.owner.login()

    # Set the level to what is defined in the user data, or if this
    # was a non-staff user, set to the default
    ub.set_staff_level()

    if login:
        ub.login()

    return ub
