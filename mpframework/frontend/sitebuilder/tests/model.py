#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal tests
"""

from mpframework.testing.framework import ModelTestCase

from ..models import Frame
from ..models import TemplateCustom
from ..request_skin import RequestSkin


class ModelTests( ModelTestCase ):

    def test_main( self ):
        u = self.login_user()

        self.l("Frames")
        import yaml
        portal_yaml = """
            frame_template: testframe.html
            panes:
            - name: pane1
              template: tc1
              opt1: PaneOpt1
            - name: pane2
              template: tc2
            """
        portal_dict = yaml.safe_load( portal_yaml )
        options = {
            'portal': {
                'opt1': "PortalOpt1",
                }
            }
        f = Frame( name='test_portal', structure=portal_dict )
        f.sb_options.update( options )
        f.save()
        frame = Frame.objects.get( name='test_portal' )
        self.assertTrue( frame )

        self.l("RequestSkins")
        skin = RequestSkin( u.sandbox )
        self.assertTrue( skin )
        self.assertFalse( skin.mods )

        skin.set_frame( frame )
        self.assertTrue( skin.sb_options['portal.opt1'] == "PortalOpt1" )
        skin.set_frame( frame.pk )
        self.assertTrue( skin.sb_options['portal.opt1'] == "PortalOpt1" )
        skin.set_frame( frame.name )
        self.assertTrue( skin.sb_options['portal.opt1'] == "PortalOpt1" )

        ptc = frame.structure_context( skin )
        self.assertTrue( ptc )
        self.assertTrue( ptc['frame_template'] == 'testframe.html' )
        self.assertTrue( ptc['pane']['name'] == "pane1" )
        self.assertTrue( ptc['pane']['opt1'] == "PaneOpt1" )
        self.assertTrue( ptc['panes'][0]['name'] == "pane1" )
        self.assertTrue( ptc['panes'][1]['template'] == "tc2" )

    def test_template( self ):
        u = self.login_user()

        self.l("Testing custom templates")

        TemplateCustom( name='tc', code_prod='test code1' ).save()
        TemplateCustom( name='tc', code_prod='test code2',
                        provider_optional=u.provider ).save()

        tc1 = TemplateCustom.objects.get( name='tc', provider_optional=None )
        tc1a = TemplateCustom.objects.get_custom('tc')
        self.assertTrue( tc1.template_code() == 'test code1' )
        self.assertTrue( tc1a.template_code() == 'test code1' )

        tc2 = TemplateCustom.objects.get_custom( 'tc', u.sandbox )
        self.assertTrue( tc2.template_code() == 'test code2' )

        tc2.code_dev = "DEV test code2"
        self.assertTrue( tc2.template_code( True ) == 'DEV test code2' )

        TemplateCustom( name='tc3', code_prod='test code3',
                        provider_optional=u.provider, _all_sandboxes=False ).save()

        tc = TemplateCustom.objects.get_custom( 'tc3' )
        self.assertTrue( tc is None )
        tc = TemplateCustom.objects.get_custom( 'tc3', u.sandbox )
        self.assertTrue( tc is None )

        tc3 = TemplateCustom.objects.get( name='tc3' )
        tc3._sandboxes.add( u.sandbox )

        tc = TemplateCustom.objects.get_custom( 'tc3' )
        self.assertTrue( tc is None )

        tc3 = TemplateCustom.objects.get_custom( 'tc3', u.sandbox )
        self.assertTrue( tc3.template_code() == 'test code3' )

