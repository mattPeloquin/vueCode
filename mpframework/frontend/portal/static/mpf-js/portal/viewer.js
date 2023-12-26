/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal viewer

    Create viewer elements that display content in an iframe in
    various ways depending on content type and options.
    The "viewer" is the parent element holding the iframe, it is
    rendered dynamically from client templates, which allows different
    viewer designs to be specified in site and content options.

    Results may include players (e.g., video, LMS) and VM views
    (e.g., html, proxies), so the code here must not make assumptions
    about content types or iframe contents.

    A key viewer responsibility is to responsively size the
    viewer based on its content, page size, and location in page.
    The viewer element may be full screen over the portal, or
    embedded in portal layout in different locations.

    Viewers have a limited set of events they will listen for in
    the iframe which can be used to indicate completion of an item or
    storing local state. Content can use these to interact with MPF.

    The default is to rebuild the viewer for each content display, which
    ensures compatibility and switching between different content types.

    To maximize performance and usability, there are optimizations
    to avoid unnecessary DOM element recreation, which helps both in
    responsiveness of display and browser dynamics such as maintaining
    fullscreen or casting between videos.
    Note the when an iframe is moved in the DOM it reloads, which is a
    headache for optimization.

    ASSUMES ONE VIEWER IS ACTIVE AT A TIME on a page/tab.
    "Open in new tab" option supports multiple open content views,
    in which case this viewer framework is NOT used.
*/
(function() { 'use strict';

    // HACK - Used to detect an unmodified Iframe
    const IFRAME_DEFAULT_HEIGHT = 150
    // HACK - when comparing heights, account for small deviances
    const HEIGHT_FUDGE = 4
    // HACK - avoid scroll bars when fixing nav panel height
    const HEIGHT_SCROLL = 25

    const MAX_VERTICAL_VIEW_HEIGHT = 0.7
    const MAX_AUX_HEIGHT = 0.5

    // Default location for viewer, and DOM location under which
    // all viewers must live
    mpp.VIEWER_ELEMENT = 'viewer'
    const VIEWER_PARENT = 'main_page'

    mpp.viewer_is_visible = function() {
        return $( mpp.VIEWER_ELEMENT ).is(":visible")
        }

    /*
        Keep track of the current/previous item model for optimizations
    */
    mpp.viewer_last_item = function() {
        return _viewer_item
        }
    let _viewer_item = false

    /*
        When viewer is open, keep track of the path it was opened
        in so navigation can manage lifetime
    */
    mpp.viewer_content_path = function( path ) {
        if( path ) {
            path = path.split('/')
            while( path.slice(-1)[0][0] === mpp.NAV_NO_CONTENT ) {
                path.pop()
                }
            if( path ) {
                _viewer_content_path = path.join('/')
                }
            }
        return _viewer_content_path
        }
    let _viewer_content_path = ''

    /*
        Override vm_current to optimize viewer creation.
        The viewer template is determined by viewer for the current item
        and observable listening to current node changes will cause the
        viewer template to only be reset when it actually changes,
        which avoids unnecessary screen DOM rendering.
        Insertable viewers are also handled here.
        HACK - insert detected based on insert tag present on the current page
    */
    // Store original item_set
    const _item_set = mpp.vm_current.item_set
    // Add viewer-specific logic to current VM holder
    _.extend( mpp.vm_current, {
        // Keep track of previous viewer for optimization
        item_set: function( item ) {
            _item_set.call( this, item )
            _prev_viewer = _viewer( this.get_prev_item_node_root('viewer') )
            },
        // Viewer name and template name to use with the current item
        viewer_type: function() {
            const insert = insert_override()
            if( insert ) {
                return $( insert ).data('viewer_type')
                }
            return _viewer( this.get_item_node_root('viewer') )
            },
        get_viewer_template: function() {
            return insert_override() ? 'viewer_insert' :
                        _viewer( this.get_item_node_root('viewer') )
            },
        // Observable for viewer template to load, updated with current node
        viewer_template: ko.observable( mpp.get_template_name( _viewer() ) ),
        })
    function _viewer( viewer ) {
        return viewer || mp.request.default_viewer
        }
    let _prev_viewer = false

    // When node changes, update observable with current viewer
    mpp.vm_current.node.subscribe( function() {
        mpp.vm_current.viewer_template(
            mpp.get_template_name( mpp.vm_current.get_viewer_template() )
            )
        })

    mpp.viewer_remove = function() {
    /*
        Remove contents of viewer to ensure content is gone and
        when viewer is moved around, old pieces aren't left.
    */
        $( mpp.VIEWER_ELEMENT ).hide()
            .each( function() {
                ko.removeNode( this )
                })
        _prev_viewer = null
        _viewer_content_path = ''
        mp.layout_resize_set()
        }

    mpp.viewer_request = function( type, item, node ) {
    /*
        Start process to show content in viewer BEFORE access requested.
        request is made. Called each time content item is changed.
    */
        mp.log_info2("Content view requested: ", type, item, node)
        try {
            if( item ) {
                // Unless setup says not to carry on, call access handler with
                // default viewer display as the launcher
                const node_id = node && node.id
                const direct_access = viewer_setup_current( type, node_id )
                if( direct_access !== undefined ) {
                    const access_handler = mpp.access_handlers_get( type )
                    if( access_handler( item, node_id, default_launcher, direct_access ) ) {
                        set_current_item( item, node )
                        return true
                        }
                    }
                }
            mp.log_info("Content view did not proceed: ", type, item, node)
            }
        catch( e ) {
            mp.log_error("Exception starting viewer: ", e)
            }
        }

    function viewer_setup_current( type_db, node_id ) {
    /*
        Each time new content is played turn off the current content.
        Depending on the viewer type and whether the viewer can be reused,
        this can mean different things. Typically if the content and
        viewer are the same, it will be left in place to optimize screen
        experience, fullscreen, casting, etc.
        Returns true or false to continue access, undefined to stop access
    */
        const item = mpp.vm_current.item()
        const viewer_type = mpp.vm_current.viewer_type()

        // If there is a special handler for viewer, use it
        const setup_fn = mpp.viewer_setups[ viewer_type ]
        if( setup_fn ) {
            return setup_fn( type_db, item, node_id )
            }

        // Otherwise do default viewer setup
        // If viewer type is different, wipe out entire viewer
        if( _prev_viewer != viewer_type ) {
            mpp.viewer_remove()
            return false
            }
        if( mpp.viewer_is_visible() ) {
            // If viewer is same and visible and item hasn't changed do nothing
            if( _viewer_item === item.model ) {
                return
                }
            // If viewer access type is same, try reusing
            if( _viewer_item.get('type_view') == item.model.get('type_view') ) {
                return true
                }
            }
        // Otherwise leave viewer in place, but remove iframe to setup
        // for new content load and be responsive to click
        iframe_remove()
        return false
        }
    mpp.viewer_setups = {}

    function set_current_item( item, node ) {
    /*
        Make sure current item is set to the requested one - this may
        already be set from user selection, but not when linking directly.
    */
        if( item ) {
            mpp.vm_current.item_set( item )
            mpp.vm_current.node_set( node )
            }
        else {
            mpp.vm_current.item_clear()
            }
        }

    function insert_override() {
    /*
        Test the current nav page for a viewer insert tag, check
        both up and down from current panel since some structures may
        have a visible viewer with tabs, etc. that are navigable.
    */
        if( mpp.nav_portal() ) {
            let insert = []
            let nav_portal = mpp.nav_portal()
            while( nav_portal && !insert.length ) {
                insert = $( nav_portal.selector ).find('.mpp_viewer_insert_here')
                nav_portal = nav_portal.parent
                }
            return insert && insert[0]
            }
        }

    function default_launcher( access ) {
    /*
        The default callback for starting up the viewer after a request call.
        Bind the template for the viewer and create the iframe if
        not already available, set the src to content,
        do any post processing, and show if needed.
    */
        if( access.item.id != mpp.vm_current.item().id ||
                !( access.access_url || access.direct ) ) {
            mp.log_info("Viewing aborted, no access: ", access)
            _viewer_item = false
            return
            }
        try {
            mp.log_info2("Displaying viewer: ", access)

            create_viewer()
            move_viewer( access )
            iframe_load( access )

            // Set the current playing item
            _viewer_item = access.item
            }
        catch( e ) {
            mp.log_error("Exception launching viewer: ", access, " - ", e)
            }
        // If there were errors, still try to let them play, might be non-fatal
        return true
        }

    function create_viewer() {
    /*
        Dynamically create viewer DOM node from current viewer_template
    */
        if( !$( mpp.VIEWER_ELEMENT ).length ) {
            const viewer = document.createElement('viewer')
            viewer.setAttribute( 'data-bind',
                        "template: { name: viewer_template }" )
            $( VIEWER_PARENT ).append( viewer )
            mpp.ko_binding_apply( viewer, mpp.vm_current )
            }
        }

    function move_viewer( access ) {
    /*
        Handle special cases for moving viewer after creation.
    */
        // If there is a viewer insert tag present, place the viewer there
        // (leave if already created)
        const viewer_insert = insert_override()

        if( viewer_insert ) {
            let viewer = $( viewer_insert ).find( mpp.VIEWER_ELEMENT )
            if( !viewer.length ) {
                viewer = $( mpp.VIEWER_ELEMENT ).detach()
                $( viewer_insert ).append( viewer )
                }
            }
        // Otherwise check for movement extension based on type
        else {
            const move_fn = mpp.viewer_moves[ mpp.vm_current.viewer_type() ]
            if( move_fn ) {
                move_fn( access )
                }
            }
        }
    mpp.viewer_moves = {}

    function iframe_load( access ) {
    /*
        Create viewer iframe with given access session/url if
        iframe doesn't already exists (if it does, assume it is same type)
    */
        const viewer_panel = $( mpp.VIEWER_ELEMENT ).find(".mpp_viewer_box")
        let access_url = access.access_url

        // Handle reuse case if content supports it
        if( access.direct ) {
            const iframe = viewer_panel.find("iframe")[0]
            if( iframe ) {
                if( access.item.access_direct ) {
                    const reused = access.item.access_direct( access, iframe )
                    if( reused ) {
                        return
                        }
                    }
                iframe_remove()
                }
            access_url = access.direct.default_url
            }

        // Create new iframe
        viewer_panel.append( $( '<iframe>', {
                src: access_url,
                allow: 'fullscreen',
                }) )
         viewer_panel.find("iframe").on( 'load', iframe_onload )
        }

    function iframe_remove() {
        $( mpp.VIEWER_ELEMENT ).find(".mpp_viewer_box > iframe").remove()
        }

    function iframe_onload() {
    /*
        Perform setup for the iframe from the parent script context
    */
        $( mpp.VIEWER_ELEMENT ).show().hide_wait()
        const iframe = this
        try {
            iframe_init( iframe )
            }
        catch( e ) {
            if( e.name == 'SecurityError' ) {
                mp.log_info("Unable to update viewer iframe: ", iframe)
                mp.log_debug( e )
                }
            else {
                mp.log_error("Exception initializing viewer iframe:", e)
                }
            }
        try {
            iframe_viewer_init( iframe )
            }
        catch( e ) {
            mp.log_error("Exception initializing viewer iframe:", e)
            }
        }

    function iframe_init( iframe ) {
    /*
        Setup internals for the iframe
    */
        const iwindow = iframe.contentWindow
        const idoc = iframe.contentDocument

        // Setup error handlers
        iwindow.onerror = function( e ) {
            mp.log_error( e )
            }
        idoc.DisplayError = function( message ) {
            mp.log_error( message )
            }
        idoc.onerror = function( message ) {
            mp.dialog_error( message )
            }

        // Disable browser controls for non-staff
        if( !mp.user.access_staff ) {
            $( iwindow ).bind( 'contextmenu', function( event ) {
                event.preventDefault()
                })
            $( idoc.body ).addClass('mp_select_off')
            idoc.oncopy = function() { return false }
            idoc.oncut = function() { return false }
            }

        // Inactivity detection inside frame
        mp.idle_set_handlers( idoc )

        // Run content script setup inside iframe for content type
        switch( _viewer_item.get('type_db') ) {
            case 'video':
                mpp.video_fixup( idoc.body )
                break
            case 'proxyapp':
                mpp.app_fixup( idoc.body )
                break
            case 'lmsitem':
                mpp.lms_fixup( idoc.body )
                break
            }
        }

    function iframe_viewer_init( iframe ) {
    /*
        Handle display of viewer based on iframe
    */
        const viewer = $( iframe ).parents( mpp.VIEWER_ELEMENT )
        const full = !!viewer.find(".mpp_viewer_fullscreen").length

        // Setup resize viewer based on iframe content
        mp.layout_resize_set( function() {
            // Adjust viewer height
            const item = ko.unwrap( mpp.vm_current.item )
            content_size_adjust( viewer, iframe, item.type_db )
            // If embedded, call main layout, if full fixup whats needed
            if( full ) {
                mp.fixup_responsive_css()
                }
            else {
                mp.layout_resize_main()
                }
            return viewer[0]
            })

        mp.layout_resize()
        viewer.hide_wait()
        }

    /*----------------------------------------------------------------
        Responsive height support
    */

    function content_size_adjust( viewer, iframe, type_db ) {
    /*
        Viewer iframe calls this when resized to set viewer_panel height.
        Responsive viewer_panel height for the various MPF viewers and
        content types is tricky. In general viewer layout should be driven
        by the HEIGHT of the CONTENT at a GIVEN WIDTH.
        Content height is not always available, so defaults are used as needed,
        and explicit CSS height is also supported.
        Type specializations can register handlers to set the height
        based on their viewer DOM structure.
    */
        const iframe_html = $( iframe ).contents().find("html")[0]

        // Call specific or default handler to get height element
        // Set the height using that value
        const height_adj = mpp.viewer_content_height[ type_db ] ||
                    mpp.viewer_content_height['default'] ||
                    _default_content_height
        const height = viewer_height_adj( viewer, height_adj( iframe_html ) )

        // Then get the width value
        const width_adj = mpp.viewer_content_width[ type_db ] ||
                    mpp.viewer_content_width['default'] ||
                    _default_content_width
        const width = viewer_width_adj( viewer, width_adj( iframe_html ) )

        viewer_fixups( iframe_html, height, width )
        mp.log_debug("Set viewer size to: ", width, ", ", height)
        }

    // Register handlers for height and width
    // Handlers return either element to use as basis, explicit value,
    // nothing to use defaults
    mpp.viewer_content_width = mpp.viewer_content_width || {}
    mpp.viewer_content_height = mpp.viewer_content_height || {}
    function _default_content_width( iframe_html ) {
        // Force use of default; override in extensions by
        // defining mpp.viewer_content_width['default']
        }
    function _default_content_height( iframe_html ) {
    /*
        Default handler checks for height set explicitly in wrapper
        (vs. the height set by MPF fixup), e.g., with videojs.
        If no height (or default iframe height found, return undefined
        to force default height from viewer_height_adj.
        Looking inside the iframe is left to content-specific items like LMS;
        trying to look into iframe content in general manner was feasible,
        but usually results in less than optimal scroll bar setup. Better
        to provide a smaller viewport to scroll over frame if needed.
    */
        const content = $( iframe_html )
                    .find(".es_page_content:not(.mpp_height_adjusted)")
        if( !is_iframe_default_height( content ) ) {
            return content[0]
            }
        }

    function viewer_width_adj( viewer, width_adj ) {
    /*
        Width defaults are simpler than height; normally try to fill
        container width or set viewer box to width that children follow.
    */
        let width = '100%'
        const box = $( viewer ).find(".mpp_viewer_box")
        if( width_adj && box.hasClass('mpp_viewer_width') ) {
            width = width_adj
            }
        box.width( width )
        $( viewer ).find(".es_viewer_wrapper").width( width )
        return box.width()
        }

    function viewer_height_adj( viewer, height_input ) {
    /*
        Sets viewer panel height and returns the current height in pixels
        This handles shared code for a number of different scenarios, based
        on what the viewer_content_height handlers return.
            1) If panel has height from original CSS, it is kept
            2) If an element is provided, height layout is based on that
            3) If no height provided or set, defaults are used
    */
        // If original height set in CSS (height set and no marker) do nothing
        const orig_height = viewer.find(
                    ".mpp_viewer_box:not(.mpp_height_adjusted)").height()
        if( orig_height ) {
            return orig_height
            }
        // Get fullscreen or panel height viewer is displayed in since if nav or other
        // items are shown with iframe need to constrain their height for force scrolling
        const full = fullscreen_height( viewer.find(".mpp_viewer_fullscreen") )
        let height = full
        if( height_input ) {
            height = $( height_input ).height()
            }
        let panel_height = full
        const panel = viewer.parents(".mp_viewer_panel")
        if( panel.length ) {
            panel_height = panel.height() - HEIGHT_SCROLL
            }
        const panel_avail = viewer.find(".es_viewer_full").length ||
                mp.layout_is_horizontal() ?
                    panel_height :
                    panel_height * MAX_VERTICAL_VIEW_HEIGHT
        if( panel_avail ) {
            height = height || panel_avail
            height = Math.floor( Math.min( height, panel_avail ) )
            }
        // Fall back to defaults if not available
        if( !height ) {
            _.forOwn( _height_defaults, function( value, key ) {
                if( viewer.find( key ).length ) {
                    height = value()
                    return false
                    }
                })
            if( !height ) {
                height = '100%'
                }
            }
        // Set the viewer height to fit into visible area
        // add marker to note this was not in original CSS
        viewer.find(".mpp_viewer_box")
            .height( height )
            .css({ 'min-height': height })
            .addClass('mpp_height_adjusted')
        // If nav panel is sharing screen height with viewer, adjust it too
        // The items surrounding the viewer iframe can be inside the viewer
        // element or the panel; make convenient jquery item for both.
        const view_frame = viewer.add( panel )
        const viewer_nav = view_frame.find(".mpp_viewer_nav")
        const aux = view_frame.find(".mpp_viewer_aux")
        if( viewer_nav.length ) {
            if( mp.layout_is_horizontal() ) {
                viewer_nav.height( panel_height )
                }
            else {
                // For vertical, need to adjust remaining height between nav and aux
                const remaining_height = Math.floor( panel_height - height - HEIGHT_SCROLL )
                aux.css({ 'height': '' })
                let aux_height = aux.height() || 0
                aux_height = Math.min( aux_height, remaining_height * MAX_AUX_HEIGHT )
                aux.height( Math.floor( aux_height ) )
                const nav_top = panel.find(".es_viewer_top_nav").height() || 0
                viewer_nav.height( Math.floor(
                            remaining_height - aux_height - nav_top ) )
                }
            }
        return height
        }

    const _height_defaults = {
        '.mpp_viewer_insert': function() { return '66vh' },
        '.mpp_viewer_popup': function() { return '66vh' },
        '.mpp_viewer_overlay': function() { return '90vh' },
        '.mpp_viewer_fullscreen': function() { return '95vh' },
        }

    function viewer_fixups( iframe_html, height, width ) {
    /*
        Adjustments to viewer CSS needed for every resize
    */
        const content = $( iframe_html ).find(".es_page_content")

        // If there is iframe embedded under viewer, set it's height
        // to match the given wrapper height to keep both in sync
        const iframe = content.find("iframe").first()
        iframe.height( height )

        // HACK - for boundary cases where size of viewer is close to panel size,
        // toggle hiding overflow on to work around cycling resizing seen
        // in videojs and Wistia clients
        const threshold = content.height() - height
        $( iframe_html )
            .toggleClass( 'mp_overflow_none', threshold < 6*HEIGHT_FUDGE )
        }

    function fullscreen_height( panel ) {
        // Return fullscreen height minus return/banner, or 0 if not fullscreen
        let height = 0
        if( panel.height() ) {
            const top_bar = panel.find(".es_viewer_top_bar")
            height = panel.height() - ( top_bar.height() || 0 )
            }
        return height > 0 ? height : 0
        }

    function is_iframe_default_height( element ) {
    /*
        HACK - assume close to WWW spec height is an uninitialized iframe.
    */
        element = $( element )
        return element.length && element.height() &&
               element.height() > IFRAME_DEFAULT_HEIGHT - HEIGHT_FUDGE &&
               element.height() < IFRAME_DEFAULT_HEIGHT + HEIGHT_FUDGE
        }

    })();
