#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content block support for all content EXCEPT Collections and LMS
"""
from random import randint
from ..data import get_unique_dict
from ..data import get_unique_data
from ..data.content import *
from ._base import SystemTestBlock


class ContentBlock( SystemTestBlock ):
    """
    The support for different content types is done in a hacky way by special
    casing logic based on type when necessary because for now it requires
    less code -- if the special-cases get messy, refactor into type subclasses
    """

    def __init__( self, stc, data=None, ctype=None, **kwargs ):
        """
        Add support for different types of content
        If type is provided, set here, it is assummed that either the content
        is already created with that type, or will only create that type
        """
        self.ctype = ctype
        super().__init__( stc, data, **kwargs )

    def __str__( self ):
        return "{} {} tag:{} id:{}".format( self.ctype, self.data['_name'],
                                     self.data.get('tag'), self.data.get('tag') )

    def verify_portal( self ):
        if not self.created:
            self.stc.l("WARNING - tried to verify block that wasn't created")
            return True

        rv = False
        item = self.find_portal()
        if item:

            # TESTWORK NOW - what other checks besides existence can be run on portal data?
            rv = True

        return rv

    def find_portal( self ):
        """
        Find and return content HTML webelement if anywhere in portal
        """
        rv = None
        self.stc.go_portal()

        # TESTWORK - navigate around portal if needed; for some portal types
        # the HTML for items may not yet be created
        # (some JS viewmodels, which generate HTML, aren't made until page is navigated to)

        # First try by DB id, which may not be set yet
        # If it is set, it as always at the same div level as es_content
        db_id = self.data.get('db_id')
        if db_id:
            rv = self.stc.get_content_id( db_id )

        # Then try tag, which user can leave blank, and which is also at content level
        tag = self.data.get('tag')
        if not rv and tag:
            rv = self.stc.get_content_code( tag )

        # If those fail, get content with name embedded, which is a required value
        if not rv:
            rv = self.stc.get_content_text( self.data['_name'] )

        # If DB id hasn't been set yet, set from the EasyStyle CSS id
        if rv and not db_id:
            classes = rv.get_attribute('class').split(' ')
            for c in classes:
                if c.startswith('es_id_'):
                    self.data['db_id'] = c[6:]

        return rv

    def go_edit( self ):
        """
        Go to the admin content edit page randomly via different pathways
        """
        # TESTWORK NOW - add support for pagination/search when list is long
        rand = randint( 0, 1 )
        if rand:
            # Normal admin content-items screen
            self.stc.go_menu( 'content', 'content-items' )
            try:
                self.stc.go_anchor( self.data['_name'])
            except( Exception ):
                search = self.stc.get_id('changelist-search')
                search.send_keys( self.data['_name'] )
                self.stc.get_css('.search-button').click()
                self.stc.go_anchor( self.data['_name'] )
        else:
            self.stc.go_portal()
            item = self.find_portal()
            item.get_css('.mp_staff_content_edit').click()
        # TESTWORK - add support for special case items like LMS not in content-items

    def create_item( self, data=None ):
        """
        Create content item, either from data or a new random item
        """

        # Open list on content screen and get available types
        self.stc.go_menu('content', 'content-items')
        self.stc.get_css('.mp_staff_content_add').click()
        add_list = self.stc.get_css( '.mp_staff_content_add a', first=False )

        # Pick random type from the available list if not defined
        if not self.ctype:
            add = add_list[ randint( 0, len(add_list)-1 ) ]
            add_path = add.get_attribute('href').split('/')
            self.ctype = add_path[ -3 ]

        # Generate data for new items
        if not data:
            data = get_unique_dict( CONTENT )
            data['_name'] = '{} {}'.format( data['_name'], self.ctype )
            data.update( get_unique_data( CONTENT_TYPES[ self.ctype ] ) )

        # Open the add page for item and fill out
        add_button = None
        for add in add_list:
            if '/{}/'.format( self.ctype ) in add.get_attribute('href'):
                add_button = add
                break
        if add_button:
            add_button.click()
            self.update_data( data )
            self.stc.get_id('mpsave').click()
            self.stc.l("CONTENT CREATED: %s", self)
            self.created = True

        return self

    # HACK - Provide polymorphism for the main download file data type, to support
    # cases like product where the content type specialization is about accessing a file
    _file_mappings = [ 'content_file', 'video_file', 'audio_file' ]
    @property
    def file_mapping( self ):
        rv = None
        type_data = CONTENT_TYPES.get( self.ctype )
        for key in type_data:
            if key in self._file_mappings:
                rv = ( 'id_' + key, self.data[ key ] )
                break
        return rv

