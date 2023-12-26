#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tenant model tests
"""

from mpframework.testing.framework import ModelTestCase

from ..models.sandbox import Sandbox
from ..models.provider import Provider
from ..models.sandbox_host import SandboxHost


class ModelTests( ModelTestCase ):

    def test_main( self ):

        num_providers_at_start = Provider.objects.count()

        # Add new provider
        Provider( name='Test Provider',
                  system_name='testprov', resource_path='testprov' ).save()
        p1 = Provider.objects.get( system_name='testprov' )
        self.assertTrue( p1.name == 'Test Provider' )

        # Test provider manager
        self.assertTrue( Provider.objects.count() == num_providers_at_start + 1 )

        # Add new provider and sandbox
        p2 = Provider.objects.create_obj( name='ProvTest2', system_name='prov2test' )
        s = Sandbox( _provider=p2, name='SandboxTest', subdomain='sandtest' )
        s.save()
        self.assertTrue( s.name == 'SandboxTest' )
        s2 = Sandbox.objects.create_obj( _provider=p2, subdomain='SandboxTest2' )
        self.assertTrue( s2.subdomain == 'SandboxTest2' )

        # URL and host tests
        SandboxHost( sandbox=s, _host_name='test.host' ).save()
        h = SandboxHost.objects.get( _host_name='test.host' )
        self.assertTrue( h.host_name == 'test.host' )
        s = Sandbox.objects.get_sandbox_from_host('test.host')
        self.assertTrue( s.name == 'SandboxTest' )

        # Clone a sandbox
        s2 = Sandbox.objects.clone_sandbox( s, p2, 'NewTestSandS2', 'new_sand' )
        self.assertTrue( s2.name == 'NewTestSandS2' )


