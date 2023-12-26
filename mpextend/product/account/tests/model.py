#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account Model tests
"""

from decimal import Decimal

from mpframework.testing.framework import ModelTestCase

from mpframework.common.utils import SafeNestedDict
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.user.mpuser.models import mpUser
from mpframework.user.mpuser.utils.activate import activate_user
from mpextend.product.catalog.models import Agreement
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.models import Coupon

from ..models import GroupAccount
from ..models import APA


APA_PRICE = Decimal('2.2')


class ModelTests( ModelTestCase ):

    def test_access( self ):

        from mpframework.content.mpcontent.models import BaseItem
        from ..access import quick_access_check
        from ..access import content_access_options
        from ..access import content_access_data

        user = self.login_nogroup()
        user_group = self.login_user()
        item1 = BaseItem.objects.get( id=1101 )

        self.l("Testing product access")

        access = quick_access_check( user, item1 )
        self.assertTrue( not access )

        access_data = content_access_data( item1, user )
        self.assertTrue( 'BuyPA_10' in access_data['pas'] )
        self.assertTrue( '22' in access_data['accounts'] )

        access_options = content_access_options( item1, user )
        self.assertTrue( 'TestPA_30' in access_options['pas'] )

        access = quick_access_check( user_group, item1 )
        access_data = content_access_data( item1, user_group )
        access_options = content_access_options( item1, user_group )
        self.assertTrue( not access )
        self.assertTrue( 'BuyPA_10' in access_data['pas'] )
        self.assertTrue( 'user@acme.com' in access_data['accounts'] )
        self.assertTrue( 'TestPA_30' in access_options['pas'] )

        self.l("Testing new user access")

        s = Sandbox.objects.get( id=20 )
        nu = mpUser.objects.create_obj( email="nu_email", password=self.TEST_PWD,
                                        sandbox=s )
        self.assertTrue( nu )
        activate_user( nu, s )
        nu = self.login_user( nu.pk )
        au = nu.account_user
        pa = au.primary_account

        self.assertTrue( au )
        self.assertTrue( pa )
        self.assertTrue( pa.name == "nu_email")

        access_data = content_access_data( item1, nu )
        self.assertTrue( 'BuyPA_10' in access_data['pas'] )
        self.assertTrue( str(pa.pk) in access_data['accounts'] )


    def test_accounts( self ):
        self.l("Get fixture users and accounts")

        user_single = self.login_nogroup()
        sandbox = user_single.sandbox
        us_account = user_single.account_user.primary_account
        self.assertTrue( user_single.pk in us_account.user_ids )
        self.assertTrue( not us_account.is_group )

        user_group = self.login_user( 21 )
        ug_account = user_group.account_user.primary_account
        self.assertTrue( user_group.pk in ug_account.user_ids )
        self.assertTrue( ug_account.is_group )

        self.l("New PAs")

        pay_agreement = Agreement( name="PayAgreement" )
        pay_agreement.save()

        onetime_agreement = Agreement( name="OnetimeAgreement",
                              rules=SafeNestedDict({ 'one_time_use': True }) )
        onetime_agreement.save()

        recurring_agreement = Agreement( name="RecurringAgreement" )
        recurring_agreement.save()

        pay_pa = PA.objects.create_obj( sandbox=sandbox, sku='PayPA',
                    agreement=pay_agreement, _access_period='2 MIN',
                    _tag_matches='TP', _unit_price=APA_PRICE  )
        self.assertTrue( pay_pa.agreement == pay_agreement )
        self.assertTrue( pay_pa.access_period_minutes == 2 )
        self.assertFalse( pay_pa.rules['one_time_use'] )

        free_pa = PA.objects.create_obj( sandbox=sandbox, sku='FreePA',
                    agreement=onetime_agreement, _access_period='2 YR',
                    _tag_matches='*' )
        self.assertTrue( free_pa.agreement == onetime_agreement )
        self.assertTrue( free_pa.rules['one_time_use'] )

        free_recurring_pa = PA.objects.create_obj( sandbox=sandbox,
                    sku='RecurringFreePA', _access_period='WK',
                    agreement=recurring_agreement,  )
        self.assertFalse( free_recurring_pa.rules['one_time_use'] )

        perpetual_pa = PA.objects.create_obj( sandbox=sandbox,
                    sku='PerpertualPA', _access_period='',
                    agreement=onetime_agreement, _unit_price=APA_PRICE )
        self.assertTrue( perpetual_pa.rules['one_time_use'] )
        self.assertFalse( perpetual_pa.access_period )

        self._test_accounts( user_group, free_pa, pay_pa )
        self._test_pay_apas( user_group, ug_account, pay_pa )
        self._test_free_apas( user_single, free_pa )
        self._test_free_apas( user_group, free_pa )
        self._test_coupons( user_single, us_account, pay_pa )

    def _test_accounts( self, user, free_pa, pay_pa ):
        self.l("---  Testing Accounts > %s", user)
        au = user.account_user
        ga = GroupAccount.objects.create_obj( sandbox=user.sandbox,
                                              name="TestGA{}".format(user) )
        # These are based on fixture data
        self.assertFalse( au.my_pas )
        self.assertTrue( free_pa in au.available_pas )

        self.l("Remove user from GA, test new healed account")
        # User 20 starts out with a group relationship to primary account
        # Remove it and then log in to heal primary account with new user account
        prev_ga = au.primary_account
        self.assertTrue( prev_ga.is_group )
        self.assertTrue( user.pk in prev_ga.group_account.base_account.user_ids )
        prev_ga.group_account.remove_user( user )
        self.clear_local_buffer()
        self.assertTrue( user.pk not in prev_ga.group_account.base_account.user_ids )

        self.l("Move user to account, make admin")
        user2 = self.login_user( reset=True )
        au = user2.account_user
        prev_sa = au.primary_account
        self.assertTrue( prev_sa != prev_ga )
        ga.add_user( user2 )
        self.assertTrue( au.primary_account.pk == ga.base_account.pk )
        self.assertTrue( user2.pk in ga.base_account.user_ids )
        self.assertFalse( ga.has_admin( user2 ) )
        ga.admins.add( au )
        self.assertTrue( ga.has_admin( user2 ) )

        self.l("Test healing of suspended account")
        # Suspend primary account and login, to set primary to group account
        user2.account_user.primary_account.status = 'S'
        user2.account_user.primary_account.save()
        user2 = self.login_user( reset=True )
        au.health_check()
        self.assertTrue( au.primary_account == prev_sa )
        self.assertFalse( au.my_pas )
        self.assertFalse( au.active_pas() )
        self.assertFalse( au.my_apas )
        self.assertTrue( pay_pa in au.available_pas )

        # Put state back to where it was
        prev_ga.group_account.add_accountuser( au )
        self.clear_local_buffer()
        self.assertTrue( user2.pk in prev_ga.group_account.base_account.user_ids )

    def _test_pay_apas( self, user, account, pay_pa ):
        self.l("--- Testing Pay APA -> %s, %s", user, account)
        ga = GroupAccount.objects.create_obj( sandbox=user.sandbox, name="TestGA2")

        def _user_product_tests( user, apa ):
            self.l(" user product validations: %s -> %s", user, apa )
            au = user.account_user

            # Since this uses same user object, force stashed/cached update
            user.invalidate()

            self.ld("Validating apa and user")
            self.assertTrue( apa.unit_price == u_apa.pa.unit_price )
            self.assertTrue( user.pk in apa.user_ids )
            self.assertTrue( apa.user_attached( user ) )
            self.assertTrue( apa in au.my_apas )
            self.assertTrue( apa in au.active_apas() )
            self.assertTrue( apa in au.active_apas( pay_pa.tags ) )

            self.ld("Validating pa and user: %s", pay_pa)
            self.assertTrue( pay_pa.pk in au.my_pas )
            self.assertTrue( pay_pa in au.active_pas() )
            self.assertTrue( pay_pa in au.active_pas( pay_pa.tags ) )
            self.assertTrue( pay_pa not in au.available_pas )

        self.l("Test APA relationships with default group account: %s", user)
        new_apa = APA.objects.get_license_for_primary( user, pay_pa )
        u_apa = APA.objects.get_license( user, account, pay_pa )
        self.assertTrue( u_apa.pk == new_apa.pk )
        self.assertTrue( u_apa.unit_price == APA_PRICE )
        self.assertTrue( u_apa.access_price == APA_PRICE )

        _user_product_tests( user, u_apa )

        self.l("Test creation of new APA when one exists")
        u_apa2 = APA.objects.get_license( user, account, pay_pa )
        self.assertTrue( u_apa2 == u_apa )

        self.l("Test creation of override APA when one exists")
        u_apa3 = APA.objects.get_license( user, account, pay_pa, override=True )
        self.assertTrue( u_apa3 != u_apa )

        self.l("Test APA relationships with new default user individual account: %s", user)
        # Kill the active APA
        u_apa.save( _disable=True )
        u_apa = APA.objects.get_license( user, account, pay_pa )
        self.assertTrue( u_apa != u_apa2 )
        _user_product_tests( user, u_apa )

        au = user.account_user

        self.l("Test active APA relationship")
        self.assertTrue( u_apa in au.active_apas() )
        u_apa.save( _disable=True )
        user.invalidate()
        self.assertTrue( u_apa not in au.active_apas() )
        u_apa.save( _disable=False )
        user.invalidate()
        self.assertTrue( u_apa in au.active_apas() )

        self.l("Test APA relationships with new group account and existing APA record")
        ga.add_user( user )
        g_apa = APA.objects.get_license( user, ga.base_account, pay_pa )
        self.assertTrue( g_apa != u_apa )
        g_apa.save( _disable=True )

        g_apa = APA.objects.get_license( user, ga.base_account, pay_pa, recycle=False )
        self.assertTrue( g_apa != u_apa )
        self.assertTrue( g_apa.user_attached( user ) )
        self.assertTrue( au in g_apa.ga_users.all() )
        _user_product_tests( user, g_apa )
        g_apa.save( _disable=True )

        self.l("Test group license APA")
        g_apa = APA.objects.get_license( user, ga.base_account, pay_pa, for_group=True )
        self.assertTrue( g_apa.user_attached( user ) )
        self.assertTrue( au not in g_apa.ga_users.all() )
        _user_product_tests( user, g_apa )

    def _test_free_apas( self, user, free_pa ):
        self.l("--- Testing Free APA -> %s", user)
        au = user.account_user
        account = au.primary_account

        # The free APA is one-time use, make sure it is accessible now
        self.assertTrue( free_pa in au.available_pas )

        # Then create relationship and test
        u_apa = APA.objects.get_license( user, account, free_pa )
        self.assertTrue( u_apa )
        if account.is_group:
            self.assertTrue( au in u_apa.ga_users.all() )
        else:
            self.assertTrue( au not in u_apa.ga_users.all() )
        self.assertTrue( user.pk in u_apa.user_ids )

        user.invalidate()

        self.assertTrue( free_pa.pk in au.my_pas )
        self.assertTrue( free_pa in au.active_pas() )
        self.assertTrue( free_pa in au.active_pas( free_pa.tags ) )
        self.assertTrue( free_pa not in au.available_pas )

        # Kill the APA and then make sure it can't be used again
        u_apa.save( _disable=True )
        user.invalidate()

        self.assertTrue( free_pa.pk in au.my_pas )
        self.assertTrue( free_pa not in au.active_pas() )
        self.assertTrue( free_pa not in au.active_pas( free_pa.tags ) )
        self.assertTrue( free_pa not in au.available_pas )

        u_apa = APA.objects.get_license( user, account, free_pa )
        self.assertFalse( u_apa )

    def _test_coupons( self, user, account, pa ):
        self.l("--- Testing Coupons -> %s, %s", user, account)

        bad_c = Coupon.objects.coupon_search( user.sandbox, 'DiscountPA_10', pa=pa )
        self.assertTrue( bad_c is None, "Coupon get for specific PA should have return none")
        c2 = Coupon.objects.coupon_search( user.sandbox, 'DiscountPA_10' )
        self.assertTrue( c2 )

        new_c = Coupon.objects.create_obj( **{
                'sandbox': user.sandbox,
                'code': 'TestDiscount',
                'unit_price': 0.5,
                '_access_period': '23 min',
                '_rules': SafeNestedDict({
                    'unit_points': 111,
                    'unit_minutes': 10,
                    'active_users_max': 20,
                    'initial_price': 99,
                     })
                })
        c = Coupon.objects.coupon_search( user.sandbox, 'TestDiscount', pa=pa )
        assert( new_c and c and c == new_c )
        self.assertTrue( c.uses_current == 0 )
        self.assertTrue( c.available )
        self.assertTrue( c.unit_price == 0.5 )

        apa = APA.objects.get_license( user, account, pa, coupon=c )
        self.assertTrue( c.uses_current == 1 )
        self.assertTrue( apa )
        self.assertTrue( apa.access_period_minutes == 23 )

        self.assertTrue( apa.unit_price == APA_PRICE * Decimal('0.5') )
        self.assertTrue( apa.access_price == (APA_PRICE * Decimal('0.5')) + 99 )
        self.assertTrue( apa.rules['unit_points'] == 111 )

        apa.sku_units = 9999
        apa.save()
        self.assertTrue( apa.access_period_minutes == 23 )
        self.assertTrue( apa.unit_price == APA_PRICE * Decimal('0.5') )
        self.assertTrue( apa.access_price == ( APA_PRICE * Decimal('0.5') * 9999 ) + 99 )
        self.assertTrue( apa.base_points == 111 * 9999 )
