#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content model tests
"""

from mpframework.testing.framework import ModelTestCase
from mpframework.foundation.tenant.models.provider import Provider
from mpframework.foundation.tenant.models.sandbox import Sandbox

from ..models import BaseItem
from ..models import PortalType
from ..models import PortalGroup
from ..models import PortalCategory
from ..models import Tree
from ..models import ProtectedFile


class ModelTests( ModelTestCase ):

    def test_clone( self ):
        self.l("Testing cloning")

        p = Provider( name='ProvClone',
                      system_name='provclone', resource_path='provclone' )
        p.save()
        s_template = Sandbox.objects.get( id=20 )
        s = Sandbox.objects.clone_sandbox( s_template, p, 'NewTestSand', 'new_sand' )
        self.assertTrue( s.name == 'NewTestSand' )

        BaseItem.objects.clone_sandbox_objects( s_template, s )
        items = list( BaseItem.objects.filter( sandbox=s ) )
        self.assertTrue( len(items) )
        self.wait_for_threads()

    def test_content( self ):
        provider = Provider.objects.get( pk=11 )

        self.l("Types, groups, and categories")
        PortalType( _provider=provider, _name='TestType', workflow='B' ).save()
        new_type = PortalType.objects.get( _provider=provider, _name='TestType' )
        self.assertTrue( new_type.name == 'TestType' )
        PortalGroup( _name='TestGroup', workflow='P' ).save()
        new_group = PortalGroup.objects.get( _provider=provider, _name='TestGroup' )
        self.assertTrue( new_group.name == 'TestGroup' )
        PortalCategory( _provider=provider, _name='TestCat', workflow='P' ).save()
        new_cat = PortalCategory.objects.get( _provider=provider, _name='TestCat' )
        self.assertTrue( new_cat.name == 'TestCat' )

        user = self.login_user()
        sandbox = user.sandbox

        self.l("File tests")
        self.assertTrue( len(ProtectedFile.objects.filter( sandbox=sandbox )) ==
                    len(ProtectedFile.objects.filter( user_filter=user )) )
        f = ProtectedFile.objects.create_obj( sandbox=sandbox,
                    content_file='Test.File', name='TestFile' )
        self.assertTrue( f.name == 'TestFile' )
        f._action = 'action_download'
        f.save()

        self.l("Unfiltered content vs. filter by user")
        self.assertTrue( len(Tree.objects.filter()) >
                            len(Tree.objects.filter( user_filter=user )) )
        self.assertTrue( len(Tree.objects.filter( sandbox=sandbox )) >
                            len(Tree.objects.filter( workflow__in='PB' )) )

        self.l("Test tree nodes")

        # t7 is a parent of t8 in test data
        t7 = Tree.objects.get_node( user, 1007 )
        t8 = Tree.objects.get_node( user, 1008 )
        self.assertTrue( t7 and t8 )
        t7_all = t7.all_items( model=ProtectedFile, user=user )
        t8_node = list(t8.all_node_items( model=ProtectedFile ))
        test_t7_in_t8 = [ bool(item in t7_all) for item in t8_node ]
        self.assertTrue( test_t7_in_t8 and all( test_t7_in_t8 ) )

        t1 = Tree.objects.get_node( user, 1001 )
        self.assertTrue( t1 )
        t1_all = t1.all_items( include_nodes=False )
        t1_node = t1.all_node_items()
        self.assertTrue( t1_all == list(t1_node) )

        self.l("Add/Remove items to tree nodes")

        f1 = ProtectedFile.objects.get( pk=1201 )
        f2 = ProtectedFile.objects.get( pk=1202 )
        t1.add_item( f1 )
        t1.add_item( f2 )
        t1.invalidate()
        t1_downcast = [ item.downcast_model for item in t1.all_items() ]

        self.assertTrue( len(t1_downcast) - len(t1_all) == 2 )

        t7.add_item( f )
        t8.add_item( f1, area='F' )
        t8.add_item( f2, area='S' )
        t8.add_item( f2, area='I' )
        t7.save()
        t8.save()
        t7_all = t7.all_items()
        t7_node = t7.all_node_items()
        t8_all = t8.all_items( user=user, include_nodes=False )
        t8_node = t8.all_node_items( user=user )
        self.assertTrue( len(t7_all) > len(t7_node) )
        self.assertTrue( len(t7_all) > len(t8_all) )
        self.assertTrue( len(t8_all) > len(t8_node) )

        self.l("Retire items and remove from sandboxes")
        f.sandboxes.remove( user.sandbox )
