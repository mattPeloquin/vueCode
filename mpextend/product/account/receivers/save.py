#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account receivers
"""
from django.dispatch import receiver
from django.db.models.signals import post_save

from mpframework.common import log
from mpframework.user.mpuser.signals import mpuser_invalidate
from mpframework.user.mpuser.models import mpUser


@receiver( post_save, sender=mpUser )
def handle_mpuser_post_save( **kwargs ):
    """
    Clear out account user caching when user is flushed
    """
    user = kwargs.get('instance')
    au = getattr( user, 'account_user', None )
    if au and au.primary_account and not au.primary_account.is_group:
        if au.primary_account.name != user.email:
            log.info2("Updating user account name: %s -> %s",
                au.primary_account.name, user)
            au.primary_account.name = user.email
            au.primary_account.save()

@receiver( mpuser_invalidate )
def handle_mpuser_invalidate( **kwargs ):
    """
    Clear out account user caching when user is flushed
    """
    user = kwargs.get('user')
    log.debug2("Account app received user flush cache signal: %s", user)
    if hasattr( user, 'account_user' ):
        user.account_user.invalidate()
