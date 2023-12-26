#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Collections block support for all content in collections
"""
from random import randint

from ..data import get_unique_dict
from ..data import get_unique_data
from ..data.content import *
from .content import ContentBlock


class CollectionsBlock( ContentBlock ):

    def __init__( self, stc, data=None, ctype=None, **kwargs ):
        """
        Add support for different types of content
        If type is provided, set here, it is assummed that either the content
        is already created with that type, or will only create that type
        """
        self.ctype = ctype
        super().__init__( stc, data, **kwargs )

    def create_item( self, data=None, min_collection_items=0, max_collection_items=16 ):
        """
        Create collection item, either from data or a new random item
        """

        # Open list on content screen and get available types
        self.stc.go_menu('content', 'collections')
        self.stc.go_anchor('Add Collection')

        # Generate data for new items
        if not data:
            data = get_unique_dict( CONTENT )

        self.update_data(data)

        self.add_collection_item( randint(min_collection_items, max_collection_items) )

        self.stc.get_id('mpsave').click()

        return self

    def add_collection_item( self, num_to_add=1 ):

        list_lengths = 0
        alt_length = 0

        for i in range(0, num_to_add):
            self.stc.get_css('.djn-add-item a').click()
            entry = self.stc.get_id(('id_tree_bi_items-{}-item-autolookup').format(i))

            no_entries = True
            suggested_entries = []
            tried_letters = []

            while no_entries:
                rand = randint(97, 123)

                while rand in tried_letters:
                    rand = randint(97, 123)

                letter = chr(rand)

                entry.send_keys(letter)
                self.stc.wait_point(1)
                UI_ID_num = i + 1 + list_lengths

                suggested_entries = self.stc.get_list_from_id(('ui-id-{}').format(UI_ID_num))

                if suggested_entries[0].text != "0 results":

                    if alt_length > 0:
                        list_lengths = list_lengths + alt_length
                        alt_length = 0

                    list_lengths = list_lengths + len(suggested_entries)
                    selection_number = randint(0, len(suggested_entries)-1)
                    suggested_entries[selection_number].click()
                    no_entries = False
                    break
                else:
                    tried_letters.append(rand)
                    alt_length = alt_length + 1

