#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Plan receivers
"""
from django.conf import settings
from django.dispatch import receiver

from mpframework.common import log
from mpextend.product.account.signals import apa_add_users


@receiver( apa_add_users )
def handle_apa_add_users( **kwargs ):
    """
    When an APA for specific content adds a user, add content related to it to plans of
    users associated with an account
    """
    apa = kwargs.get('apa')
    try:
        if apa.includes_all:
            log.debug("Skipping add to user(s) plans, since apa for ALL content: %s", apa)

        else:
            from mpframework.user.mpuser.models import mpUser
            from .models import UserPlan
            users = kwargs.get('users')
            if not users:
                users = mpUser.objects.filter( id__in=apa.user_ids )
            log.info2("Adding to %s users plan: %s", len(users), apa )
            for user in users:
                try:
                    plan = UserPlan.objects.get_or_create( user )
                    plan.add_collections( apa.get_top_collections() )
                    user.invalidate()

                except Exception:
                    log.exception("Updating plan: %s", user)
                    if settings.MP_TESTING:
                        raise

    except Exception:
        log.exception("Updating users for apa: %s", apa)
        if settings.MP_TESTING:
            raise
