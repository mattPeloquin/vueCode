#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    APA manager

    APAs are created programmatically through a number of different
    mechanisms and can also be created manually through the admin.
"""
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from mpframework.common import log
from mpframework.common.utils import SafeNestedDict
from mpframework.common.events import sandbox_event
from mpframework.common.logging.timing import mpTiming
from mpframework.foundation.tenant.models.base import TenantManager

from ..utils import get_au


class ApaManager( TenantManager ):

    def get_apas( self, account, *args, **kwargs ):
        """
        Return list of Activated apas that meet common filtering tasks
        for the apas related to an account.
        There are special reserved kwargs for special filtering in addition
        to passing along args and kwargs to filter.
        """
        assert account
        rv = []
        if log.debug_on():
            t = mpTiming()
            log.timing2("START getting apas: %s -> %s, %s", account, args, kwargs)

        user = kwargs.pop( 'user', None )
        available = kwargs.pop( 'available', False )
        not_available = kwargs.pop( 'not_available', False )
        backoffice = kwargs.pop( 'backoffice', False )

        if user and account.is_group:
            args += ( Q( ga_users__user_id=user.pk ) |
                      Q( ga_license=True ) ,)

        if backoffice:
            kwargs['purchase_type'] = 'B'

        apas = self.mpusing('read_replica')\
                .filter( *args, account=account, is_activated=True, **kwargs )\
                .order_by('-period_start')
        for apa in apas.iterator():
            if not_available and apa.is_available:
                continue
            if available and not apa.is_available:
                continue
            log.detail3(" including apa: %s", apa)
            rv.append( apa )

        if log.debug_on():
            log.timing("FINISH getting apas %s: %s -> %s", t, account, rv)

        return rv

    def get_license_for_primary( self, user, pa, **kwargs ):
        """
        Create APA for primary user account
        """
        au = get_au( user )
        if au:
            return self.get_or_create( user, au.primary_account, pa, **kwargs )

    def get_license( self, user, account, pa, **kwargs ):
        return self.get_or_create( user, account, pa, **kwargs )

    def get_or_create( self, user, account, pa, **kwargs ):
        """
        Create and/or return an APA for the given account and PA

        Returns existing active APA tied to user if available and
        override flag is not set.
        Returns none if a one-time APA for PA already exists or error occurs
        Otherwise returns new APA.

        With purchase platforms, APAs are created BEFORE final approval, and
        activated if payment goes through, to keep record of attempts.
        """
        log.debug2("get_or_create APA: %s -> %s -> %s", user, account, pa)
        assert user and account and pa
        assert not user.is_staff

        # Make sure user is connected to the requested account
        accounts = []
        try:
            if hasattr( user, 'account_user' ):
                accounts = user.account_user.accounts
                if account not in accounts:
                    log.warning("APA CREATE user/account mismatch: %s, %s -> %s",
                                    user, account, accounts)
                    return
        except ObjectDoesNotExist:
            if settings.MP_DEV_EXCEPTION:
                raise
            log.warning("APA CREATE failed, no user accounts: %s", user)
            return

        # FUTURE SCALE - if checking user_attached for APAs on large group accounts a problem, refactor checks to use 1 DB call
        try:
            coupon = kwargs.pop( 'coupon', None )
            override = kwargs.pop( 'override', False )

            if not override:
                # If active APAs on any of user's accounts, return first valid one
                # Note the list from DB is constrained by _is_active flag, but need
                # to check the is_active property in case end date has been exceeded
                active_apas = self.filter( sandbox=user.sandbox, pa=pa, _is_active=True,
                                           account__in=accounts )
                for apa in active_apas.iterator():
                    log.debug2("Checking active APA for user access: %s -> %s", user, apa)
                    if apa.is_active( save=True, deep=True ):
                        if apa.user_attached( user ):
                            log.info2("ACCESS GRANTED, APA active: %s -> %s", user, apa)
                            return apa

            # If the request is for a one time use PA, verify it hasn't been used,
            # but only against the requested account/user combination
            if pa.rules['one_time_use']:
                used_apas = self.filter( sandbox=user.sandbox,
                                         account=account, pa=pa,
                                         coupon=coupon.code if coupon else '',
                                         _is_active=False, is_activated=True )
                for apa in used_apas.iterator():
                    if apa.user_attached( user ):
                        log.info2("APA exists for user, one time, used up: %s -> %s", user, apa)
                        return

            # Otherwise try to create new or recycle existing APA
            apa = self.create_obj( user, account, pa, coupon, **kwargs )

            if apa and apa.is_active( save=True, deep=True ):
                log.info2("ACCESS GRANTED, new APA: %s -> %s", user, apa)
                if apa.access_free:
                    sandbox_event( user, 'user_license_free', pa )
                else:
                    sandbox_event( user, 'user_license_purchase', pa )

            return apa

        except Exception:
            log.exception("APA get_or_create: %s -> %s -> %s", user, account, pa)
            if settings.MP_TESTING:
                raise

    @transaction.atomic
    def create_obj( self, user, account, pa, coupon, **kwargs ):
        log.debug("APA create: %s -> %s -> %s, %s", user, account, pa, coupon)
        assert user and account and pa

        # Is this APA a group license?
        for_group = kwargs.get('for_group')
        assert not for_group or account.is_group

        # Units used in price calculations for only purchases
        units = kwargs.get( 'units', 1 )

        # Use any coupon adjustments, or set to defaults to PA
        if coupon and coupon.available:
            coupon_code = coupon.code
            access_period = coupon.access_period
            access_end = coupon.access_end
            tag_matches = coupon.tag_matches
            rules = coupon.rules
            # Update coupon uses here since coupon object is available and
            # may not be at activation, and this is where any end date mods were made
            # FUTURE - unactivated APAs count against coupon usage; move if problem
            uses = self.filter( sandbox=user.sandbox, coupon=coupon.code ).count()
            coupon.uses_current = uses + 1
            coupon.save()
        else:
            coupon_code = ''
            access_period = ''
            access_end = pa.access_end
            tag_matches = ''
            rules = SafeNestedDict()

        # Search for an unactivated APA with same account and cost profile.
        # If found, use that record instead of creating a new one. This happens
        # with purchases and some linking scenarios where APA is created before
        # process is finalized.
        # Don't try to reuse APAs when a group APA is requested to avoid issues
        # with different group APAs or site-license APAs conflicting.
        apa = None
        if not for_group and kwargs.get( 'recycle', True ):
            log.debug("Checking APA recycle: %s, %s -> %s", user, account, pa )
            recyclable_apas = self.select_for_update()\
                    .filter( sandbox=user.sandbox,
                             is_activated=False,
                             account=account, pa=pa,
                             sku_units=units,
                             coupon=coupon_code )
            for exist_apa in recyclable_apas.iterator():
                if exist_apa.user_attached( user ):
                    log.info2("RECYCLE APA: %s %s -> %s, %s -> %s, %s",
                              exist_apa.pk, exist_apa, user, account, pa, coupon)
                    exist_apa.is_activated = False
                    apa = exist_apa
                    break

        # Otherwise create new APA record
        if not apa:
            log.info2("CREATING APA: %s, %s -> %s, %s, units:%s",
                        user, account, pa, coupon, units)

            apa = self.model( sandbox=user.sandbox,
                              account=account, pa=pa,
                              sku_units=units,
                              coupon=coupon_code )

        # Note if this is a group license
        apa.ga_license = bool( account.is_group and for_group )

        # Update attributes for new and OVERWRITE for recycle
        # End is always updated for relative time from now
        # Pricing, points, tag_matches, and rules are updated to capture case
        # where PA or Coupon was updated since original APA creation and recycling
        apa._access_period = access_period
        apa.access_end = access_end

        apa._unit_price = pa.unit_price
        if coupon_code:
            coupon.price_adjust( apa )

        apa._tag_matches = tag_matches
        apa._rules = rules

        # Save now so any MTM user relationships can be set up before activation
        apa.save( _user=user )

        # If group account but not group license, add user that created to handle
        # case of coupon/sku activation by individual users
        if account.is_group:
            if for_group:
                apa.add_ga_user( user )
            else:
                apa.add_ga_user( user, force=True )
                apa.ga_users_max = 1
                apa.save()

        # Support immediate activation so APA can allow user access
        # Activate free APAs if not already forced
        activate = kwargs.get( 'activate', True )
        if not activate and apa.access_no_payment:
            activate = u"No payment needed for activation"
        if activate:
            log.debug("Activating new APA immediately: %s", apa)
            apa.save( _user=user, _activate=activate )

        return apa

    def migrate_user_apas_to_account( self, au, account, all=False ):
        """
        Idempotent migrate for a user's singular APAs to account:

         - If a user is participating in group site-license or selected-user
           APAs, those are NOT transferred.
         - User WILL be removed from GA selected-user APAs.
         - All single-user account records are transferred; if target is a
           group account the records are converted to single-user records.
         - By default, only active records are transferred, which keeps
           new account from being cluttered with expired license history
        """
        assert au and account
        log.info2("Migrating APAs to account: %s -> %s", au, account)
        apa_filter = {
            'sandbox': au.user.sandbox,
            'is_activated': True,
            'account__in': [ a for a in au.accounts if a != account ],
            }
        if all:
            # This may take an expired license that hasn't been checked, which is ok
            apa_filter.update({ '_is_active': True })

        for apa in self.filter( **apa_filter ).iterator():
            log.debug("Considering migrating APA: %s -> %s", au, apa)
            migrate_apa = False

            if apa.account.is_group:
                num_users = apa.ga_users.count()

                # Only Migrate single records for this user
                # Don't migrate site-license APA or multi-user APAs
                if num_users == 1 and apa.ga_users.filter( id=au.pk ).exists():
                    migrate_apa = True

                # Remove user from selected-user APAs
                elif num_users:
                    apa.ga_users.remove( au )
                    apa.save()
            else:
                migrate_apa = True

            if migrate_apa:
                log.debug("Migrating apa: %s -> %s -> %s", au, apa, account)
                apa.account = account
                if account.is_group:
                    apa.ga_users.add( au )
                apa.save()
