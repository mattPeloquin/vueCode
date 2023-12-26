#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Per-request customizable UI settings
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.utils import safe_int
from mpframework.common.cache import cache_rv
from mpframework.common.cache import stash_method_rv
from mpframework.common.cache import clear_stashed_methods
from mpframework.common.cache.utils import make_hash
from mpframework.common.utils import SafeNestedDict

from .models import Theme
from .models import Frame
from .defaults import UI_DEFAULTS
from .defaults import frame_default


class RequestSkin:
    """
    RequestSkins are used for the standard portal and item/collection portals.
    They manage per-request values for theme/frame configurable UI options.
    The goal is easy reuse of templates and settings with a high level
    of customization when needed.

    Frames/VuePortals define the HTML structure of the response to specific
    request endpoints (such as portal, collection, item).

    Theme values (like color template) are derived from precedence checking
    of different "containers" at the content, request, theme, frame,
    sandbox, and system levels. Defaults can be set in different ways, and then
    overridden for different specialization scenarios.

    Each request has one RequestSkin, which manages all server side combining
    of theme options (some RequestSkin options can be overridden on the client
    by settings in content or panes).

    Each RequestSkin has:

        ONE Theme from the following precedence:
            0) URL query string
            1) Request mod
            2) Sandbox
            3) System default (no theme)

        ONE Frame from the following precedence:
            0) URL query string
            1) Request mod
            2) Sandbox
            3) Theme, based on Theme progression above
            4) System default (based on portal type)

        Most remaining Theme values are loaded as the FIRST specifc non-blank value
        in the order below (lower numbers trump higher ones):
            0a) Pane config in Frames (not in RequestSkin)
            0b) Values set in items/collections (not in RequestSkin)
            1) Request mods for specific values
            2) Sandbox
            3) Theme, based on Theme progression above
            4) Frame, based on Frame progression above
            5) System defaults (if any in code, or nothing)

    The idea is most values in these "containers" are set to blank, so will
    fall through to defaults, typically on the theme selected by the sandbox.
    Only some values can be set per-content, but they always override when present.
    Request mods take precedence because the point of them is to override the
    sandbox. Sandbox specific values override themes/frames to allow the Sandbox to
    easily modify an existing theme.

    sb_options and CSS combine values with progressive override:
        0) Start with system defaults
        1) Add Theme values
        2) Add Frame values
        3) Add Sandbox values
        4) Add content values (not in RequestSkin)
        5) Add pane values (not in RequestSkin)
    """

    # Value used to request default
    DEFAULT = "_default_"

    def __init__( self, sandbox ):
        """
        An initial skin is created for every screen-based (non-API) request.
        It defaults to using the values in the sandbox's frame_site selection,
        which may then be overridden in request middleware or views by updating
        frame, sandbox options, or request mods.
        """
        self.mods = {}
        self._frame = None
        self.frame_type = 'P'
        self.sandbox = sandbox

    def __str__( self ):
        return str( self.get_mods() )

    def set_theme( self, theme ):
        """
        Theme can be set in cached portal calls, but unlike the frame
        it is managed as a mod attribute.
        """
        if not isinstance( theme, Theme ):
            opts = { '_provider': self.sandbox.provider }
            if safe_int( theme ):
                opts['id'] = theme
            else:
                opts['name'] = theme
            theme = Theme.objects.get_quiet( **opts )
        if theme:
            self.mods['theme'] = theme
            clear_stashed_methods( self )
            log.debug("Set skin theme: %s", theme)

    def set_frame( self, frame ):
        """
        Update the skin with the given frame, frame name, or frame id.
        Used to set frame up for customized request skin.
        """
        frame_key = getattr( frame, 'id', frame )
        # Skip if default is requested
        if frame_key == self.DEFAULT:
            return
        # Skip if already set
        if self._frame:
            if frame_key in [ self._frame.pk, self._frame.name ]:
                return
        # Get frame object if needed
        if not isinstance( frame, Frame ):
            opts = { '_provider': self.sandbox.provider }
            if safe_int( frame_key ):
                opts['id'] = frame_key
            else:
                opts['name'] = frame_key
            frame = Frame.objects.get_quiet( **opts )
        # Set it if exists, otherwise just accept current
        if frame:
            self._frame = frame
            clear_stashed_methods( self )
            log.debug("Set skin frame: %s", frame)

    def set_mods( self, mods ):
        """
        Update skin state with a dict of mods
        """
        for name, mod in mods.items():
            if name == 'frame':
                self.set_frame( mod )
            else:
                self.mods[ name ] = mod

    def get_mods( self ):
        rv = self.mods.copy()
        if self._frame:
            rv['frame'] = self._frame
        return rv

    def clear( self ):
        clear_stashed_methods( self )
        self._frame = None

    @property
    @stash_method_rv
    def cache_key( self ):
        """
        This key defines all the settings of the skin. It is intended for use with
        a sandbox cache group, so doesn't include sandbox in the key.
        """
        frame = self.frame.name if self.frame else 'no_frame'
        mods = make_hash( self.mods ) if self.mods else ''
        return frame + mods

    def cache_template_key( self, user ):
        """
        Returns (very) simple string to uniquely identify variations on request
        skin values that must be considered for MPF template and CSS caching.
        """
        rv = ''
        rv += str( self.frame.pk ) if self.frame else ''
        if self.color2 and user.options['color2']:
            rv += 'C2'
        return rv

    @property
    @stash_method_rv
    def theme( self ):
        """
        Return theme used with the request.
        Due to overrides this should NOT be accessed to determin the
        settings for the skin.
        """
        rv = self.mods.get('theme')
        if not rv:
            rv = self.sandbox.theme
        return rv

    @property
    @stash_method_rv
    def frame( self ):
        """
        Return frame to use with the request.
        If set_frame called from url or request mods, return it, otherwise
        try to load from other locations, fall back to system.
        """
        if not self._frame:
            # Use cache to avoid DB hit to get the default frame for the site
            self._frame = self._default_frame()
        return self._frame

    @cache_rv( keyfn=lambda self:(
                '{}-{}'.format( self.frame_type, self.theme ),
                self.sandbox.cache_group ) )
    def _default_frame( self ):
        # Sandbox direct frame first
        frame = self.sandbox.frame_for_type( self.frame_type )
        # Then try theme from request mods or sandbox
        if not frame:
            if self.theme:
                frame = self.theme.frame_for_type( self.frame_type )
        # Last, grab system default
        if not frame:
            frame = frame_default( self.frame_type )
        return frame

    """
    Theme value accessors
    Check request mods, sandbox, frame, and theme values as described above.

    HACK - system defaults for required template values are placed here,
    which means name of template may be returned instead of template object.
    FUTURE - move defaults into settings
    """

    @property
    def login( self ):
        return self.theme_accessor('login') or 'login_default'

    # Server-side templates that return template object, none, or default
    @property
    def style( self ):
        return self.theme_accessor('style')
    @property
    def color( self ):
        return self.theme_accessor('color')
    @property
    def color2( self ):
        return self.theme_accessor('color2')
    @property
    def font( self ):
        return self.theme_accessor('font')
    @property
    def mixin( self ):
        return self.theme_accessor('mixin')
    @property
    def mixin2( self ):
        return self.theme_accessor('mixin2')
    @property
    def mixin3( self ):
        return self.theme_accessor('mixin3')

    # Object attributes rather than FKs to templates
    @property
    def background_image( self ):
        return self.theme_accessor('background_image').url or ''

    # Client-side templates, which are only accessed as names
    @property
    def default_panel( self ):
        return self._get_script_name( 'default_panel', 'panel_page' )
    @property
    def default_nav( self ):
        return self._get_script_name( 'default_nav', 'nav_card' )
    @property
    def default_node( self ):
        return self._get_script_name( 'default_node', 'node_list' )
    @property
    def default_item( self ):
        return self._get_script_name( 'default_item', 'item_list' )
    @property
    def default_viewer( self ):
        return self._get_script_name( 'default_viewer', 'viewer_full' )

    def _get_script_name( self, name, default='' ):
        value = self.theme_accessor( name )
        return value.script_name if value else default

    @stash_method_rv
    def theme_accessor( self, name ):
        """
        Return request skin values in precedence based on theme attribute name.
        Throw exceptions on bad theme attribute names, to treat as a bad url.
        """
        # Direct request mods trump all
        rv = self.mods.get( name )
        if not rv:
            name = '_' + name  # Container field name prefixed by underscore
            # Check direct sandbox
            rv = getattr( self.sandbox, name )
            # Check theme
            if not rv:
                theme = self.theme
                if theme:
                    rv = getattr( theme, name )
            # Check frame
            if not rv:
                rv = getattr( self.frame, name )
        return rv

    @property
    @stash_method_rv
    def sb_options( self ):
        """
        Combine default, sandbox, frame, and theme sb_options following the
        mod, frame, sandbox theme, sandbox precedence.
        Final sb_options applied in portal code can still overridden by
        sb_options in the pane or content.

        USING OPTIONS IN CODE
        SafeNestedDicts can be accessed several ways; MPF convention
        is to use full dot string, e.g., sb_options['optA.option_name']
        """
        rv = SafeNestedDict( UI_DEFAULTS )
        if self.theme:
            rv.update( self.theme.sb_options )
        rv.update( self.frame.sb_options )
        rv.update( self.sandbox.sb_options )
        return rv

    @property
    @stash_method_rv
    def css_head( self ):
        """
        Combine sandbox, frame, and theme CSS additions
        """
        rv = ''
        if self.theme:
            rv += self.theme.css_head
        rv += self.frame.css_head
        rv += self.sandbox.css_head
        return rv
