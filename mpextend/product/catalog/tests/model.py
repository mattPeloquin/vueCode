#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Catalog model Tests
"""
from decimal import Decimal

from mpframework.common.utils import now
from mpframework.common.utils import SafeNestedDict
from mpframework.testing.framework import ModelTestCase

from ..models import PA
from ..models import Coupon
from ..models import Agreement


class ModelTests( ModelTestCase ):

    def test_main( self ):
        user = self.login_user()

        # There will be at least 1 test PA in fixture
        orig_products = PA.objects.get_available_pas( user.sandbox.pk )
        self.assertTrue( orig_products )

        self.l( "New products" )

        agr10 = Agreement.objects.get( id=10 )
        self.assertTrue( agr10 )

        pa = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                        sku='TC1+', _name="Prod test for TC1",
                        _tag_matches="TC1, YYZ*111, 9.5, Test Batch" )
        pa.save()
        pa = PA.objects.filter( _name__startswith="Prod test" ).first()
        self.assertTrue( pa.tag_matches == "TC1, YYZ*111, 9.5, Test Batch" )
        self.assertTrue( pa.tags == ("tc1", "yyz*111", "9.5", "test batch") )

        tc_prod = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                        sku='TC', _tag_matches="TC*" )
        tc_prod.save()

        s20_prod = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                        sku='S20', _tag_matches="*S20" )
        s20_prod2 = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                        sku='S20.2', _tag_matches="/.+0$" )
        s20_not = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                        sku='S20.3', _tag_matches="!*S20" )
        s20_none = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                        sku='S20.4', _tag_matches="/???????" )
        s20_prod.save()
        s20_prod2.save()
        s20_not.save()
        s20_none.save()

        some_prod = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                        sku="Some_content",
                        _tag_matches="PPT-S20, /^S(?!30).*, PDF*, *2141, TC1, TestTag" )
        some_prod.save()

        self.clear_local_buffer()

        every_product = PA.objects.get_available_pas( user.sandbox.pk )
        self.assertTrue( len(every_product) == len(orig_products) + 7 )

        self.l("Content tag matching")

        self.assertTrue( s20_prod.matches_tag( 'S20' ) )
        self.assertTrue( s20_prod.matches_tag( 'yesS20' ) )
        self.assertTrue( s20_prod2.matches_tag( 'S20' ) )
        self.assertTrue( s20_prod2.matches_tag( 'aaaaaaaa0' ) )
        self.assertFalse( s20_prod.matches_tag( '' ) )
        self.assertFalse( s20_prod.matches_tag( None ) )
        self.assertFalse( s20_prod.matches_tag( 'S20-not' ) )
        self.assertFalse( s20_prod2.matches_tag( 'aaaaaa1' ) )

        self.assertTrue( some_prod.matches_tag( 'Vid2141' ) )
        self.assertTrue( some_prod.matches_tag( 'PpT-s20' ) )
        self.assertTrue( some_prod.matches_tag( 'pdf-s30' ) )
        self.assertTrue( some_prod.matches_tag( 's' ) )
        self.assertTrue( some_prod.matches_tag( 'S1245dddadf' ) )
        self.assertFalse( some_prod.matches_tag( 's30aaaaaaa' ) )
        self.assertFalse( some_prod.matches_tag( 'TC1-1' ) )
        self.assertFalse( some_prod.matches_tag( 'TC1-12' ) )
        self.assertFalse( some_prod.matches_tag( 'PP01' ) )
        self.assertFalse( some_prod.matches_tag( 'PD*' ) )
        self.assertFalse( some_prod.matches_tag( 'NO_EXIST' ) )
        self.assertFalse( some_prod.matches_tag( '' ) )

        self.l("Content relationships (matching to content fixtures)")

        self.assertTrue( 'TC1' in str( pa.content_dict()['trees'] ))
        self.assertFalse( 'items_ids' in pa.content_dict() )

        self.assertTrue( len( s20_prod.content_dict()['items'] ) >= 5 )
        self.assertTrue( len( s20_prod2.content_dict()['all_ids'] ) >= 5 )
        all_not_s20 = s20_not.content_dict()['all_ids']
        self.assertTrue( len( all_not_s20 ) >= 20 )
        self.assertFalse( any( i in all_not_s20 for
                                i in s20_prod.content_dict()['items'] ) )
        self.assertFalse( s20_none.content_dict()['all_ids'] )

        self.assertTrue( len( tc_prod.content_dict() ) == 4 )
        self.assertTrue( len( some_prod.content_dict()['trees'] ) == 2 )
        self.assertTrue( len( some_prod.content_dict()['items'] ) == 1 )
        self.assertTrue( len( some_prod.content_dict()['all_ids'] ) == 3 )

        no_prod = PA.objects.get( id=12 )
        self.assertTrue( len( no_prod.content_dict()['all'] ) == 0 )

        # The number of content types will vary depending on what platforms are loaded
        all_prod = PA.objects.get( id=10 )
        self.assertTrue( len( all_prod.content_dict()['tree_ids'] ) >= 5 )
        self.assertTrue( len( all_prod.content_dict()['item_ids'] ) >= 9 )

        self.l("PAs")

        recurring_agreement = Agreement( name="RecurringAgreement" )
        recurring_agreement.save()

        pay_pa = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                    sku='PayPA', _unit_price=1 )
        self.assertTrue( pay_pa.agreement == agr10 )
        self.assertFalse( pay_pa.rules['one_time_use'] )

        free_pa = PA.objects.create_obj( sandbox=user.sandbox, agreement=agr10,
                    sku='FreePA', _rules=SafeNestedDict({ 'one_time_use': True }) )
        self.assertTrue( free_pa.agreement == agr10 )
        self.assertTrue( free_pa.rules['one_time_use'] )

        free_recurring_pa = PA.objects.create_obj( sandbox=user.sandbox,
                    agreement=recurring_agreement, sku='RecurringFreePA' )
        self.assertFalse( free_recurring_pa.rules['one_time_use'] )

        self.l("Coupons")

        new_c = Coupon.objects.create_obj( **{
                'sandbox': user.sandbox,
                'code': 'TestDiscount',
                'unit_price': 7.78,
                '_access_period': '10 m',
                })
        c = Coupon.objects.coupon_search( user.sandbox, 'TestDiscount', pa=pay_pa )
        assert( new_c and c and c == new_c )
        self.assertTrue( c.available )

        c.price_adjust( pay_pa )
        self.assertTrue( pay_pa.access_price == Decimal('7.78') )

        new_c = Coupon.objects.create_obj( **{
                'sandbox': user.sandbox,
                'code': '1FREE',
                'unit_price': 0,
                })
        c = Coupon.objects.coupon_search( user.sandbox, '1FREE', pa=pay_pa )
        assert( new_c and c and c == new_c )
        self.assertTrue( c.available )
        c.price_adjust( pay_pa )
        self.assertTrue( pay_pa.access_free )


    def test_clone( self ):
        from mpframework.foundation.tenant.models.sandbox import Sandbox
        from mpframework.foundation.tenant.models.provider import Provider

        self.l("Testing cloning")
        p = Provider( name='ProvClone',
                      system_name='provclone', resource_path='provclone' )
        p.save()
        s_template = Sandbox.objects.get( id=20 )
        s = Sandbox.objects.clone_sandbox( s_template, p, 'NewTestSand', 'new_sand' )
        self.assertTrue( s.name == 'NewTestSand' )

        PA.objects.clone_sandbox_objects( s_template, s )
        Coupon.objects.clone_sandbox_objects( s_template, s )
