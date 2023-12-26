#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base mixins for Admin classes
"""
from django.contrib.admin.views.main import ChangeList


class BaseChangeList( ChangeList ):
    """
    MPF admin use this ChangeList as a conduit for providing
    additional information into templates.
    """
    def __init__( self, request, *args ):
        self.request = request
        super().__init__( request, *args )

    def mp_css( self ):
        """
        Generate dict of column names and css classes to add to headers and fields
        """
        small_hide = self.model_admin.get_list_hide_small( self.request )
        med_hide = self.model_admin.get_list_hide_med( self.request )
        col_small = self.model_admin.get_list_col_small( self.request )
        col_med = self.model_admin.get_list_col_med( self.request )
        col_large = self.model_admin.get_list_col_large( self.request )
        col_xlarge = self.model_admin.get_list_col_xlarge( self.request )
        text_small = self.model_admin.get_list_text_small( self.request )
        text_xsmall = self.model_admin.get_list_text_xsmall( self.request )

        shared = {
            key: ('mpr_hide_small ' if key in small_hide else '') +
                    ('mpr_hide_med ' if key in med_hide else '') +
                    ('mp_col_small ' if key in col_small else '') +
                    ('mp_col_med ' if key in col_med else '') +
                    ('mp_col_large ' if key in col_large else '') +
                    ('mp_col_xlarge ' if key in col_xlarge else '')
                for key in set( small_hide + med_hide +
                            col_small + col_med + col_large + col_xlarge )
            }
        fields = shared.copy()
        fields.update({
                key: ('mp_textsmall ' if key in text_small else '') +
                        ('mp_textxsmall ' if key in text_xsmall else '')
                    for key in set( text_small + text_xsmall )
                    })
        fields.update( self.model_admin.list_field_css )

        return {
            'headers': shared,
            'fields': fields,
            }
