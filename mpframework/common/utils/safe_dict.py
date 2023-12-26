#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Dict that supports nesting values with chained calling
    (e.g., allows easy access into nested dicts in Yaml data).
"""


class SafeNestedDict( dict ):
    """
    Provides nested accesses to dict items by returning SafeNestedDicts
    or values instead of throwing exceptions.

    Get and set work as with a normal dict, except:

      - By default returns empty SafeNestedDict instead of None

      - Dotted names are resolved by trying to go into the dict:
           v = obj['a1.b'], v = obj.get('a1.b')

      - KeyError exceptions are never thrown; empty SafeNestedDict is returned
        to support chaining:  obj['a1']['b']

      - Update uses deep merging when called with a dict

      - set is used to update value for a dotted name
            obj['a1.b'] = v, obj.set( 'a1.b', v )

    The caller needs to either know the full nested name, or check
    for values along the way, as values only returned for end of the chain.
    """

    def __init__( self, *args ):
        self.update( *args )

    def __setitem__( self, key_path, value ):
        self.set( key_path, value )

    def __getitem__( self, key_path ):
        return self.get( key_path )

    def __contains__( self, key_path ):
        # Could do an optimized check instead of the get, but this
        # class should not be used for something performance critical
        return self.get( key_path, None ) is not None

    def __hash__( self ):
        # Since a SafeNestedDict is returned from get() if not present,
        # special case hashing for empty so it behaves like d.get(None)
        if not len(self):
            return hash(None)
        return super().__hash__()

    def pop( self, key_path, default=None ):
        """
        Create pop that defaults to none instead of raising key exception
        Starts at the end of key path, and walks back up, removing
        higher keys only if completely empty.
        """
        keys = self._safe_split( key_path )
        if not keys or not len(keys):
            return default
        if len(keys) == 1:
            return super().pop( keys[0], default )
        # Assume at this point that args[-1] is a dict node; pop if empty
        parent = self.get( '.'.join( keys[:-1] ), raw=True )
        rv = dict.pop( parent, keys.pop(-1), default )
        self._clean_empty_branch( parent, keys )
        return rv

    def _clean_empty_branch( self, node, keys ):
        # Clean up branch if empty
        if not node:
            node_key = keys.pop( -1 )
            parent = self if not keys else self.get( '.'.join( keys ), raw=True )
            if dict.pop( parent, node_key, None ):
                self._clean_empty_branch( parent, keys )

    def set( self, key_path, value ):
        """
        Set a dotted value name by converting into dict to update
        """
        keys = self._safe_split( key_path )
        keys.reverse()
        update_dict = { keys[0]: value }
        for key in keys[1:]:
            update_dict = { key: update_dict }
        self.update( update_dict )

    def update( self, *args ):
        for arg in args:
            if arg:
                if isinstance( arg, dict ):
                    SafeNestedDict._update( self, arg )
                else:
                    super().update( arg )

    @staticmethod
    def _update( orig, merge ):
        """
        Recurse into nested dicts to add/overwrite elements of merge to orig
        without overwriting any orig elements not in merge.
        Use dict.__getitem__ explicitly to avoid SafeNestedDict get.
        """
        for key in merge:
            merge_val = dict.__getitem__( merge, key )
            if key in orig:
                orig_val = dict.__getitem__( orig, key )
                if isinstance( merge_val, dict ) and isinstance( orig_val, dict ):
                    SafeNestedDict._update( orig_val, merge_val )
                    continue
            dict.__setitem__( orig, key, merge_val )

    def get( self, key_path, default='__SAFE_DEF__', raw=False ):
        """
        Ensure one of the following is returned:

            - A specific value from SafeNestedDict
            - A nested dict as a SafeNestedDict
            - An empty SafeNestedDict or default value

        If a dotted key_path is passed, drill into key_path until found.
        Handles non-string keys, even though they can't nest.
        """
        rv = SafeNestedDict() if default == '__SAFE_DEF__' else default
        try:
            keys = self._safe_split( key_path )
            # Only use raw return of dict if at leaf node
            node = self._safe_get( keys.pop( 0 ), raw and not len(keys) )
            if node is not None:
                if isinstance( node, SafeNestedDict ) and keys:
                    rv = node.get( '.'.join( keys ), default, raw )
                else:
                    rv = node
        except KeyError:
            pass
        return rv

    def _safe_get( self, key, raw ):
        """
        Return either the value or a nested dict
        """
        value = super().get( key )
        if not raw and isinstance( value, dict ) and not isinstance( value, SafeNestedDict ):
            return SafeNestedDict( value )
        return value

    @staticmethod
    def _safe_split( key ):
        """
        Returns list with elements from '.' delimited string. If key is not
        a string, returns single element list.
        """
        if isinstance( key, str ):
            return key.split('.')
        else:
            return [ key ]
