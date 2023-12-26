#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for test blocks
"""

class SystemTestBlock:
    """
    Base class for all test blocks

    Blocks abstract and encapsulate access to UI functionality, usually
    for specific things in the system (user, content) that
    typically map 1:1 with an admin editing screen.

    They hold state for the duration of a test case and provide:
        - Data-building actions
        - Configurability to run tests multiple ways
        - Access to the current state of data
        - Ability to verify that state against the UI
    """

    def __init__( self, stc, data=None, **kwargs ):

        # Each block is instantiated with a reference to the SystemTestCase
        # that is using it, which allows it to execute selenium actions.
        assert stc
        self.stc = stc

        # Flag to indicate if the block was created successfully
        self.created = bool( data )

        # Blocks hold data for their content, which should mirror what exists
        # in the system. If data is passed in, assume the block represents an item
        # already in the system - if not, create a new random item
        if data:
            self.data = data.copy()
        else:
            self.data = {}

        if kwargs.get( 'create', True ):
            self.create_item()

    def __str__( self ):
        # Show data for the block when converting to string for logging
        return str( self.data )

    # Placeholders for required methods in specialized classes

    def create_item( self, **kwargs ):
        # Create system item(s)
        self.stc.assertFalse("ERROR - called base class create_item")

    def go_edit( self ):
        # Go to the admin edit screen for the item
        self.stc.assertFalse("ERROR - called base class go_edit")

    # Data-driven admin methods

    def update_admin( self, data=None ):
        """
        Default update method for blocks, updates and saves and data on admin screen
        """
        self.go_edit()
        self.update_data( data )
        self.stc.get_id('mpsave').click()
        return self

    def update_data( self, data=None ):
        """
        Default update of an admin screen using data naming conventions
        for the IDs on the screen; only updates if value is different
        and input is visible on screen
        """
        if data:
            self.data.update( data )
        for key, value in self.data.items():
            field = self._get_field( key )
            if field and field.value != value:
                self.stc.l("Updating input: %s -> %s", key, value)
                field.send_keys( value )
        self.stc.wait_point()

    def verify_admin( self, items=None ):
        """
        Default verify admin functionality is to check all items in data
        """
        self.go_edit()
        self.verify_data( items )
        self.stc.wait_point()

    def verify_data( self, items ):
        """
        Make sure the user block's data is reflected in an input field
        on the current screen - if the field is visible.
        If the key name for the data doesn't exist on screen, as that can
        indicate the field isn't visible due to user/UI settings.
        If items is passed in, only names in that list are checked; otherwise
        all data that is in content items needs to match.
        """
        for key, value in self.data.items():
            if items and key not in items:
                continue
            field = self._get_field( key )
            if field:
                if key.startswith('image') or key.endswith('_file'):
                    # Need to check both input and enclosing image display, as one or the
                    # other may have the filename depending on whether file was just seleected.
                    # File fields mangle the name, so compare start and end
                    self.stc.l("Checking file: %s -> %s in %s", key, value, field.value)
                    value = value.split('.')
                    file_name = field.value
                    self.stc.assertTrue( file_name.startswith( value[0] ) )
                    self.stc.assertTrue( file_name.endswith( value[-1] ) )
                else:
                    self.stc.l("Checking field: %s -> %s in %s", key, value, field.value)
                    self.stc.assertTrue( value in field.value )

    def _get_field( self, key ):
        """
        Try to get field for the data item, including items that
        may be hidden such as textareas for editors
        """
        id = 'id_{}'.format( key )
        rv = self.stc.get_id( id, show_hidden=True, required=False, wait=0 )
        if not rv:
            self.stc.l("INPUT NOT FOUND: %s", key)
        return rv
