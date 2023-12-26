/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Page/panel client-side routing/navigation

    Supports single page app views use a custom routing mechanism to hide/show
    panels that represent pages. Supporting SEO links and generation
    of automated sitemap are priorities.
    Extended by MPF's portal for content tree and viewer navigation,
    but this code is not portal specific.
*/
(function() { 'use strict';

    // Turn off automatic scrolling for back button
    history.scrollRestoration = 'manual'

    // Load current state from storage early so mp.local_nav available
    mp.local_nav = mp.local_get('nav')
    mp.local_nav.path = mp.local_nav.path || ''
    mp.local_nav.panels = mp.local_nav.panels || {}

    mp.nav_concat = function( left, right ) {
        return _.trim( left, mp.nav_deeplinker ) + mp.nav_deeplinker +
                _.trim( right, mp.nav_deeplinker )
        }

    /*----------------------------------------------------------------------
        Panels have a unique HTML element ID that is associated with an
        anchor and link via a url based on that ID:

        mp_nav_panel    Panel tied to a path/address by id
        mp_nav_anchor   Anchor link to a mp_nav_panel
        mp_nav_link     Nav element (tab, card, link), highlights current location

        mp_nav_link is separated from mp_nav_anchor to allow some flexibility
        in laying out DOM; they may be on same element.
        Child panels are expected to live inside their parent's DOM PANEL.
        Tab/Card panel hierarchy is built in URLs with the deeplinker token.

        NOTE - the element ID is a path that may have slashes, so need to escape
    */

    mp.nav_init = function() {
        // Stash the query string in case some links want to update
        if( mp.nav_query_preserve ) {
            mp.nav_query_string = window.location.toString().split('?')[1]
            mp.nav_query_list = mp.nav_query_string ?
                                        mp.nav_query_string.split('&') : []
            }
        }

   mp.nav_current = function( location ) {
    /*
        Get/Set current nav location from nav or path and
        initialize/maintain previous and parent locations
    */
        if( location ) {
            const next = location.fragments ? location : nav_obj( location )
            // Only overwrite previous nav if different
            if( _nav_current.path != next.path ) {
                _nav_previous = next
                }
            _nav_current = next
            }
        return _nav_current
        }
    mp.nav_previous = function( location ) {
        if( location ) {
            _nav_previous = location.fragments ? location : nav_obj( location )
            }
        return _nav_previous
        }

    mp.nav_parent_path = function( address, height ) {
        // Return parent with child(ren) removed
        height = height || -1
        return nav_slice( address, 0, height )
        }
    function nav_slice( address, start, end ) {
        let path = _.trim( address, mp.nav_deeplinker )
        path = path.split( mp.nav_deeplinker )
        return path.slice( start, end ).join( mp.nav_deeplinker )
        }

    // Setup a nav panel, wrap panels use of ID for path
    mp.nav_get_panel = function( path ) {
        return document.getElementById( path_id_fixup( path ) )
        }
    mp.nav_set_panel = function( element, path ) {
        // Make sure panel has class and id
        $( element )
            .addClass('mp_nav_panel mp_nav_hide')
            .attr( 'id', path_id_fixup( path ) )
        }

    // Setup navlink and wrap the use of ID to associate with panel
    // FUTURE - if multiple links for one panel needed, switch to data
    mp.nav_get_link = function( path ) {
        return document.getElementById( NAVLINK_ID_PREFIX + path_from_id( path ) )
        }
    mp.nav_set_link = function( element, path ) {
        // Make sure link container has class and id
        $( element ).addClass('mp_nav_link')
            .attr( 'id', NAVLINK_ID_PREFIX + path )
        // Setup the anchor (may be nested or at same level)
        $( element ).find(".mp_nav_anchor").addBack(".mp_nav_anchor").first()
            .attr( 'href', mp.nav_path_full( path ) )
        }

    mp.nav_panel_parent = function( element ) {
        // The element for the immediate parent nav panel, if any
        return $( element ).parent().closest(".mp_nav_panel")[0]
        }
    mp.nav_panel_parent_path = function( element ) {
        // Path down to element through parent nav panels
        const parent = mp.nav_panel_parent( element )
        return parent ? path_from_id( parent.id ) + mp.nav_deeplinker : ''
        }

    mp.nav_default = function( parent ) {
    /*
        Returns path of the default nav panel to use if none selected.
        If default value isn't present, try to use the first nav panel.
    */
        let rv = mp.request.nav_default
        if( !rv ) {
            rv = path_from_id( nav_panels( parent ).first().attr('id') )
            }
        return rv
        }

    mp.nav_home = function( selector ) {
    /*
        Find the nearest home for the element
    */
        return $( selector ).find(".mp_nav_home.mp_nav_panel")[0]
        }

    mp.nav_is_panel = function( nav ) {
    /*
        Overridable check for non-panel paths
    */
        return true
        }

    mp.nav_path_full = function( path ) {
    /*
        Returns guaranteed full deeplink address for path
        including any portal prefix.
    */
        path = _.trim( path, mp.nav_deeplinker )
        path = path_from_id( path )
        if( !_.startsWith( path, _nav_root ) ) {
            path = _nav_root + mp.nav_deeplinker + path
            }
        return mp.nav_deeplinker + path
        }
    const _nav_root = _.trim( mpurl.nav_root, mp.nav_deeplinker )

    mp.nav_path_deeplink = function( path ) {
    /*
        Returns deeplink path fragment if it exists.
        Nav code uses only the deeplink path; the nav_root is only used
        for anchor links and URLs.
    */
        if( _.startsWith( path, mpurl.nav_root ) ) {
            path = path.replace( mpurl.nav_root, '' )
            }
        return _.trim( path, mp.nav_deeplinker )
        }

    mp.nav_set_path = function( path, force ) {
    /*
        If current and requested path don't match, set the new path
        Returns path if it was known and successfully set.
    */
        let rv = path || mp.nav_default()
        // If portal prefix is present, remove
        rv = mp.nav_path_deeplink( rv )
        // Try to set the path
        rv = mp.nav_set_path_extend( rv, force )
        // If path not set, try saved last time (if not forced), then defaults
        if( !rv && !force && mp.local_nav.path ) {
            rv = mp.nav_set_path_extend( mp.local_nav.path )
            }
        if( !rv && path ) {
            rv = mp.nav_set_path( null, force )
            }
        return rv
        }

    mp.nav_set_path_extend = function( path, force ) {
    /*
        Default implentation just selects the panel, overridden in portal.
    */
        let rv = ''
        try {
            rv = mp.nav_select( rv ).path
            }
        catch( e ) {
            mp.log_error("set_path exception: ", rv, "\n", e)
            }
        return rv
        }

    mp.nav_select = function( path, force ) {
    /*
        Show nav_panel given by portal path, which is panel and any parents.
        Selects a child if necessary and applies any saved scrolling; assumes
        any lazy elements have been rendered out to allow searching for children.
        Returns the nav object that was shown if successful.
        If failure, nothing is returned and the caller should try another address.
    */
        // Don't incur expense of hiding and showing if already there
        if( !force && _nav_current.path == path ) {
            mp.log_info2("Already at: " + path)
            return _nav_current
            }
        // Store current display state
        if( _nav_current && !mp.request.nav_no_scroll ) {
            nav_local_info( _nav_current.path ).scroll =
                        $("body").scrollTop() || $("html").scrollTop()
            }
        // Hide current panels and any nav highlighting
        nav_panels().addClass('mp_nav_hide')
        nav_links().removeClass(['mp_nav_current','es_theme_current'])
        // Try to select the new panel
        const nav = nav_obj( path )
        let new_nav = nav_select( nav )
        // If that failed (maybe saved changed), try to set to parent
        if( !new_nav ) {
            if( nav.parent ) {
                new_nav = nav_select( nav.parent )
                }
            }
        // See if there is an additional child path to navigate down to
        // (i.e., is this address actually a panel, which are always leaves)
        if( new_nav ) {
            new_nav = nav_select_child( nav, new_nav )
            }
        if( !new_nav ) {
            return
            }
        path = new_nav.path
        mp.log_highlight("PATH CHANGE: " + path )
        // Make sure layout is fixed up
        mp.layout_resize()
        // Custom event for navigation
        $( document ).trigger( 'nav_select', new_nav )
        // Scroll to top or saved location
        if( !mp.request.nav_no_scroll ) {
            const navinfo = nav_local_info( path )
            $("html, body").scrollTop( navinfo.scroll || 0 )
            }
        // For nav panels capture the last path and change browser history
        // Add querystring back to history to preserve options, tracking, etc.
        if( mp.nav_is_panel( new_nav ) ) {
            mp.local_nav.path = path
            window.history.pushState( {}, '',
                        mp.nav_path_full( path ) + window.location.search )
            }
        // Optional fixup for code extensions
        if( mp.nav_select_extend ) {
            mp.nav_select_extend( new_nav )
            }
        return new_nav
        }

    // Prefix to isolate the nav panel ID namespace
    const NAV_ID_PREFIX = 'nav_'

    // Prefix to tie nav panels to their nav links, to allow mouse click
    const NAVLINK_ID_PREFIX = 'navlink_'

    function nav_panels( parent ) {
        // Return all panels for page or subset of page
        return safe_parent( parent ).find(".mp_nav_panel")
        }
    function nav_links( parent ) {
        // Return all links and tabs for page or subset of page under parent
        return safe_parent( parent ).find(".mp_nav_link")
        }

    function nav_local_info( panel ) {
        // Manage creating new local info storage for each panel's info
        mp.local_nav.panels[ panel ] = mp.local_nav.panels[ panel ] || {}
        return mp.local_nav.panels[ panel ]
        }

    function nav_select( nav ) {
        // Show panel and any parents.
        // Sets current path and returns the nav item if successful,
        // otherwise tries to set default if not.
        try {
            if( show( nav ) ) {
                // Save this location in parent if needed
                if( nav.parent ) {
                    nav_local_info( nav.parent_path ).child = nav.path
                    }
                mp.nav_current( nav )
                return nav
                }
            }
        catch( e ) {
            mp.log_error("Problem selecting: ", nav.path, "\n", e)
            const default_nav = nav_obj()
            if( default_nav.path != nav.path ) {
                return nav_select( default_nav )
                }
            }
        }

    function nav_select_child( nav, new_nav ) {
        // Given a nav target, see if there are required children
        // that must be selected to have a valid nav target
        try {
            // Check for existence of home panel
            const home_panel = mp.nav_home( nav.selector )
            let child_path = home_panel && path_from_id( home_panel.id )
            if( !child_path ) {
                const tabs = nav_links( nav.selector ).filter(".es_portal_tab")
                if( tabs.length ) {
                    // If there is saved location, try to use it
                    child_path = nav_local_info( new_nav.path ).child
                    if( child_path ) {
                        new_nav = nav_select( nav_obj( child_path ) )
                        }
                    // Otherwise try first child nav_link
                    if( !child_path || !new_nav ) {
                        child_path = path_from_element( tabs.first() )
                        }
                    }
                }
            if( child_path ) {
                new_nav = nav_select( nav_obj( child_path ) )
                }
            }
        catch( e ) {
            mp.log_error("Problem setting nav to child: ", path, "\n", e)
            }
        return new_nav
        }

    function show( nav ) {
    /*
        Show each level of the navigation tree and perform any updates.
        Returns true if the current navigation step was valid.
    */
        if( !nav ) {
            return true
            }
        // Some paths don't correspond to panels (e.g., viewer)
        if( !mp.nav_is_panel( nav ) ) {
            return true
            }
        // Recursively show parent
        if( !show( nav.parent ) ) {
            return
            }
        // Otherwise set nav_panel and tab selection
        const anchor = find_anchor( nav.path )
        if( anchor && anchor.length ) {
            $( anchor ).closest(".mp_nav_link")
                .addClass(['mp_nav_current','es_theme_current'])
            }
        // Find and show the given panel
        const panel = $( nav.selector )[0]
        if( !!panel ) {
            // Run initial handler if present
            const initial_handler = mp.nav_initial_handlers[ panel.id ]
            if( !!initial_handler ) {
                mp.nav_initial_handlers[ panel.id ] = false
                initial_handler( panel )
                }
            panel.classList.remove('mp_nav_hide')
            return !!panel
            }
        }
    mp.nav_initial_handlers = {}

    function nav_obj( path ) {
    /*
        Given nav path, return object with nav and panel components broken out
    */
        path = path || mp.nav_default()
        path = _.trim( path, mp.nav_deeplinker )
        const frags = path.split( mp.nav_deeplinker )
        let parent = ''
        if( frags.length > 1 ) {
            parent = frags.slice( 0, frags.length-1 ).join( mp.nav_deeplinker )
            }
        return {
            path: path,
            fragments: frags,
            selector: path ? path_id_selector( path ) : '',
            parent: parent && nav_obj( parent ),
            parent_path: parent,
            parent_selector: parent ? path_id_selector( parent ) : '',
            }
        }
    let _nav_current = nav_obj()
    let _nav_previous = nav_obj()

    function find_anchor( path ) {
        // Get tab anchor element based on href value
        const address = mp.nav_path_full( path )
        const selector = ".mp_nav_anchor[href='" + address + "']:first"
        return nav_links().find( selector ).addBack( selector )
        }

    function path_from_element( element ) {
        // Return address embedded in anchor under tab or card element
        // Note this removes any prefix before portal path
        let address = $( element ).closest(".mp_nav_link")
                    .find(".mp_nav_anchor").addBack(".mp_nav_anchor").first()
                    .attr('href')
        return mp.nav_path_deeplink( address )
        }
    function path_id_fixup( path ) {
        if( !_.startsWith( path, NAV_ID_PREFIX ) ) {
            path = NAV_ID_PREFIX + path
            }
        return path
        }
    function path_from_id( id ) {
        let rv = ''
        if( id ) {
            const re = new RegExp( '^(' + NAV_ID_PREFIX + ')' )
            rv = id.replace( re, '' )
            }
        return rv
        }
    function path_id_selector( path ) {
        // Turn panel path into escaped ID selector
        const prefix = '#' + ( _.startsWith( path, NAV_ID_PREFIX ) ? '' : NAV_ID_PREFIX )
        path = prefix + path
        return _.replace( path, /\//g, '\\/' )
        }

    function safe_parent( parent ) {
        try {
            parent = parent || document.body
            return $( parent )
            }
        catch( e ) {
            mp.log_error("Bad selector: ", parent)
            return $( document.body )
            }
        }

    })();
