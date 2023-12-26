#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    SB option values shared between site, theme, and content
    This defines a superset of values in one location; many are
    shared across all scopes, but some are more narrow.
"""
from django import forms

from mpframework.common import constants as mc


class ContentOptionMixin( forms.ModelForm ):
    """
    To use as a mixin, must be a model form.
    """

    portal__hero_style = forms.CharField( required=False,
            label="Hero placement",
            help_text="Options for hero page presentation:<br>"
                "TEXT - height follows overlay text (default)<br>"
                "ASPECT - height follows image aspect ratio<br>"
                "MAX:33vh - aspect height up to max (px,em,etc)<br>"
                "CSS:max(25vh,15em) - height set to CSS value<br>"
                "FOLD - hero fills the home page portal<br>"
                "BACK - hero becomes the background<br>"
                "BACKFOLD - hero is background above the fold<br>"
                "NONE - hero is not shown" )
    portal__show_progress = forms.BooleanField( required=False,
            label="Show progress indicator",
            help_text="Show a progress indicator for the number of items "
                "completed in collections (weighted by points)." )
    portal__collection_no_bgimage = forms.BooleanField( required=False,
            label="Don't use site background",
            help_text="If the site has a background image, don't display it "
                "when showing collections." )
    portal__tabs_side = forms.BooleanField( required=False,
            label="Tabs on left side",
            help_text="For tabbed page layouts, show tabs to the left side." )
    portal__tabs_no_collapse = forms.BooleanField( required=False,
            label="Do not collapse tab menu",
            help_text="By default tab menus will collapse on smaller screen." )
    portal__collection_no_top = forms.BooleanField( required=False,
            label="Hide header",
            help_text="Hide collection's hero and header text." )
    portal__collection_footer = forms.BooleanField( required=False,
            label="Show footer panel",
            help_text="Show collection footer panel." )
    portal__collection_left = forms.BooleanField( required=False,
            label="Show panel on left",
            help_text="Show collection information panel, placed to the left." )
    portal__collection_right = forms.BooleanField( required=False,
            label="Show panel on right",
            help_text="Show collection information panel, placed to the right." )
    portal__expand_children = forms.BooleanField( required=False,
            label="Start children expanded",
            help_text="For expandable children displays, start expanded." )
    portal__expand_items = forms.BooleanField( required=False,
            label="Start items expanded",
            help_text="For expandable items displays, start expanded." )
    portal__item_font_size = forms.CharField( required=False,
            label="Item font size",
            help_text="Set the content item font size." )
    portal__card_width = forms.CharField( required=False,
            label="Card width",
            help_text="Set the display width for cards" )
    portal__card_height = forms.CharField( required=False,
            label="Card height",
            help_text="Set the total height for cards (image and text)" )
    portal__card_image_height = forms.CharField( required=False,
            label="Card image height",
            help_text="Height of image in the card" )
    portal__list_max_height = forms.CharField( required=False,
            label="List maximum height",
            help_text="Lists fill their container width and flex "
                "height based on image and text content.<br>"
                "Set this to limit maximum height." )
    portal__list_min_height = forms.CharField( required=False,
            label="List minimum height",
            help_text="Set this to max height to fix list height, or use "
                "to set a range of list height." )
    portal__css_classes = forms.CharField( required=False,
            label="Add CSS classes",
            help_text="Enter CSS class names to add to this content." )
    portal__item_styles = forms.CharField( required=False,
            widget=forms.Textarea(
                    attrs={'rows': 2, 'cols': mc.CHAR_LEN_UI_DEFAULT} ),
            label="Inject style into items",
            help_text="CSS styles to add to item style attribute." )
    portal__collection_styles = forms.CharField( required=False,
            widget=forms.Textarea(
                    attrs={'rows': 2, 'cols': mc.CHAR_LEN_UI_DEFAULT} ),
            label="Inject style into this collection",
            help_text="CSS styles to add to this collection's style attribute." )
    portal__nav_styles = forms.CharField( required=False,
            widget=forms.Textarea(
                    attrs={'rows': 2, 'cols': mc.CHAR_LEN_UI_DEFAULT} ),
            label="Inject style into nav elements",
            help_text="CSS to add to nav element style attributes." )


    # These are not used in theme defaults
    portal__item_order = forms.ChoiceField( required=False, choices=(
        ('',     u"Drag order"),
        ('name', u"Name"),
        ('tag',  u"Tag"),
        ('modified', u"Modified"),
        ('available', u"Available"),
        ),
        label="Display order for items",
        help_text="Default item order uses drag-and-drop placement below.<br>"
            "Select a different option to change order in the portal." )
    portal__hide_empty = forms.BooleanField( required=False,
            label="Hide child collections if empty",
            help_text="Select this to hide collections "
                "that contain no children or content items." )
    portal__no_play_next = forms.BooleanField( required=False,
            label="Do not automatically view next item",
            help_text="Default behavior is to try viewing the next item in a "
                "collection once the current item finishes (mostly for video, audio, LMS).<br>"
                "Uncheck to disable." )

    yaml_form_fields_extensions = [
        'portal__show_progress','portal__collection_no_bgimage',
        'portal__collection_no_top','portal__collection_footer',
        'portal__collection_left','portal__collection_right',
        'portal__tabs_side','portal__tabs_no_collapse',
        'portal__expand_children','portal__expand_items',
        'portal__item_font_size',
        'portal__card_width','portal__card_height',
        'portal__card_image_height',
        'portal__list_min_height','portal__list_max_height',
        'portal__item_styles',
        'portal__collection_styles', 'portal__nav_styles',
        # These items are not part of the preset fieldset groups below
        # as they are placed in specific locations in the admin
        'portal__hero_style',
        'portal__item_order',
        'portal__css_classes',
        'portal__hide_empty','portal__no_play_next',
        ]

    # Fields used only with groups of content (collections, panes, system)
    fieldset_collection = [
        ('portal__tabs_side','portal__tabs_no_collapse'),
        ('portal__collection_no_top','portal__collection_footer'),
        ('portal__collection_left','portal__collection_right'),
        ('portal__show_progress','portal__collection_no_bgimage'),
        ('portal__expand_children','portal__expand_items'),
        ('portal__collection_styles','portal__nav_styles'),
        ]

    # Fields that apply to individual content items
    fieldset_item = [
        'portal__item_font_size',
        ('portal__card_width','portal__card_height'),
        'portal__card_image_height',
        ('portal__list_max_height','portal__list_min_height'),
        'portal__item_styles',
        ]
