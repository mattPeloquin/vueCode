#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tests for MPF Common code
"""
import unittest


class CommonTestCases( unittest.TestCase ):

    def test_common( self ):
        """
        Location for tests specific to utils in mpframework.common
        """

        print("URL utilities")
        from mpframework.common.utils import path_clean
        from mpframework.common.utils import join_urls

        self.assertTrue( 'safepath' == path_clean( 'safepath' ) )
        self.assertTrue( 'this/is/ a /_{]_~"%/path/' == path_clean( 'this\is/ a /<>{]|~"%/path//' ) )

        self.assertTrue( 'this/is/a/safe/path' == join_urls( 'this', 'is', 'a', 'safe/path' ) )
        self.assertTrue( '/singlepath' == join_urls( '/singlepath/' ) )
        self.assertTrue( '/singlepath/' == join_urls( '/singlepath/', prepend_slash=True, append_slash=True ) )
        self.assertTrue( 'singlepath' == join_urls( 'singlepath/' ) )
        self.assertTrue( 'singlepath/' == join_urls( 'singlepath/', preserve_slash=True ) )
        self.assertTrue( '/singlepath' == join_urls( '/singlepath' ) )
        self.assertTrue( 'singlepath' == join_urls( '/singlepath/', prepend_slash=False, append_slash=False ) )
        self.assertTrue( '1/2/' == join_urls( '/', '1/', '2/', preserve_slash=True ) )

        self.assertTrue( '/path_123-1231 \u01ea \xeb' ==
                    path_clean( '\path_123-1231 \u01ea \xeb' ) )
        self.assertTrue( 'path/1231/\u01ea\u01eb/\xeb\x00' ==
                    join_urls( 'path', 1231, '\u01ea\u01eb', '\xeb\x00' ) )

        print("SafeNestedDict")
        from mpframework.common.utils import SafeNestedDict

        a = SafeNestedDict()
        self.assertFalse( a )
        self.assertTrue( isinstance( a, dict ) )

        a.update({ 'key1': 111,
                   'key2': [ 'bob', 222 ],
                   'A': { 'Test A': 333.33,
                        'B': {
                            'name': 'Nest1',
                            'C': {
                                'name': 'Nest2',
                                'value': 'EndGoal',
                                },
                            },
                        },
                   66: { 667: 'Numbers as keys' },
                   })

        self.assertTrue( 'key1' in a )
        self.assertTrue( 66 in a )
        self.assertTrue( a['key1'] == 111 )
        self.assertFalse( a['bad'] )
        self.assertFalse( a['bad1']['bad2'] )
        self.assertTrue( 222 in a['key2'] )
        self.assertTrue( 'name' in a['A']['B']['C'] )
        self.assertTrue( 'EndGoal' in a['A']['B']['C'].values() )

        self.assertTrue( a.get('key1') == 111 )
        self.assertTrue( a.get('key1', 'default') == 111 )
        self.assertTrue( a.get('bad', 'default') == 'default' )
        self.assertTrue( a.get('bad', None) == None )
        self.assertTrue( a.get('A.Test A') == 333.33 )
        self.assertTrue( a['A.Test A'] == 333.33 )
        self.assertTrue( a['A.B.C.name'] == 'Nest2' )
        self.assertTrue( a['A.B.C.bad.bad'] != 'Nest2' )
        self.assertTrue( a.get('A.B.C.bad.bad', 'Nest2') == 'Nest2' )
        self.assertTrue( 'name' in a['A.B.C'] )
        self.assertTrue( 'EndGoal' in a['A.B.C'].values() )

        self.assertTrue( a.pop('Nothing') == None )
        self.assertTrue( a.pop('A.B.Nothing') == None )
        self.assertTrue( a.pop('1.2.Nothing') == None )
        self.assertTrue( a.pop('A.B.C.value') == 'EndGoal' )
        self.assertTrue( a.pop('A.B.C.name') == 'Nest2' )
        self.assertTrue( a.get('A.B.C', 'test') == 'test' )
        self.assertTrue( a.pop('A.B.name') == 'Nest1' )
        self.assertTrue( a.get('A.B', 'test') == 'test' )


if __name__ == '__main__':

    # Fixup the sys path so this file can import MPF modules correctly
    from os import sys, path
    framework_path = path.abspath( path.join( path.dirname(__file__), '..', '..'))
    sys.path[0] = framework_path

    # Initialize Django settings
    from mpframework.common.deploy.settings import setup_env_config
    setup_env_config( argv=sys.argv )

    # Run common tests
    unittest.main()
