/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal specific navigation
    Includes SPA page deep-link navigation, back-button, tabbed UI,
    and viewer support.

    All changes to portal URL should occur via set_path
    (directly or through change events).

    VIEWER URLs
    There can only be one viewer panel present at a time, defined by both the
    content item and the collection (if any) it is contained in.
    To accommodate special behavior related to sharing/reuse of the viewer
    and the different ways a viewer can be displayed, Viewer URLs add special
    handling to the nav.js routing, using a URL namespace prefixed by VIEWER_PATH.

    VIEWER URLS ARE NOT UPDATED IN URL BAR OR HISTORY

    HOME PAGE and NESTED URLS
    Navigation assumes there is 1 or more levels of nesting and that each
    nesting level has a home page.
*/
(function() { 'use strict';

    const VIEWER_PATH = 'vue'
    mpp.NAV_NO_CONTENT = '_'

    mpp.init_navigation = function() {
    /*
        One time startup initialization for portal
    */
        // Initialize navigation for any pre-defined ui nav items
        mp.nav_init()

        // Setup event handler for deeplink changes
        $( window ).on( 'popstate', function( event ) {
            mp.nav_set_path( window.location.pathname )
            return false
            })
        // Primary portal navigation, handling anchor clicks
        $( document ).on( 'click', ".mp_nav_anchor", function( event ) {
            event.preventDefault()
            mp.nav_set_path( $(this).attr('href') )
            $(this).blur()
            })
        // Direct returns to portal from previous addresses
        $( document ).on( 'click', ".mpp_back", function( _event ) {
            mpp.viewer_remove()
            mp.nav_set_path( mp.nav_current().path, true )
            return false
            })
        $( document ).on( 'click', ".mpp_parent", function( _event ) {
            mp.local_nav.panels[ mp.nav_current().parent_path ].child = ''
            mp.nav_set_path( mp.nav_current().parent_path, true )
            return false
            })
        }

    /*
        Extend mp.nav_current to track non-viewer previous URL
        This handles common use cases when going through many viewer
        URLs and want to return to previous spot.
    */
    mpp.nav_portal = function() {
        const current = mp.nav_current()
        return mp.nav_is_panel( current ) ? current : current.parent
        }

    mp.nav_is_panel = function( nav ) {
    /*
        Override to separate Viewer addresses from panels
    */
        return !viewer_path( nav.path )
        }

    mp.nav_set_path_extend = function( path, force ) {
    /*
        Handle path management related to the viewer.
        Returns whether setting path was successful
    */
        let rv = ''
        try {
            // For viewer address, start the request to access; when ajax returns
            // it will either show protected content in viewer or access dialog.
            // Always return true to prevent set_path default loading
            const viewer = viewer_path( path )
            if( viewer ) {
                rv = true
                if( mpp.viewer_request( viewer.type, viewer.item, viewer.tree ) ) {
                    const content_path = mp.nav_parent_path( path )
                    // Note the first content item in the path as the 'parent'
                    // of the viewer, so it won't be destroyed if stays under parent
                    mpp.viewer_content_path( content_path )
                    // Viewer request is going forward, make sure location is
                    // set in the nav (usually would be, but could be direct link)
                    mp.nav_select( content_path, force )
                    }
                }
            // Otherwise show the current path's panel(s)
            else {
                // Try new path, if successful, set as current
                rv = mp.nav_select( path, force )
                // If navigation has moved 'above' current viewer, remove it
                if( !rv || !_.startsWith( rv.path, mpp.viewer_content_path() ) ) {
                    mpp.viewer_remove()
                    }
                // Refresh to show current path
                mp.layout_resize_main()
                }
            }
        catch( e ) {
            mp.log_error("set_path exception: ", rv, "\n", e)
            mpp.viewer_remove()
            mp.layout_resize_main()
            }
        return rv
        }

    mp.nav_select_extend = function( nav ) {
    /*
        Add VM-specific behavior to nav selection
    */
        const path = nav.path
        // Setup current path for any observers
        set_current_panels( path )
        const panels = mpp.nav_path_current_panels()()
        const bottom = panels[ panels.length-1 ]
        // Note the current tree node or empty navigation placeholder
        // Path only tracks the tree top, so only change current node
        // if it isn't under current nav tree top or if the viewer
        // has loaded a specific node
        let node = mpp.vm_current.node()
        const tree_top = mpp.vm_trees().get_from_slug( path )
        if( tree_top ) {
            if( !tree_top.model.all_children().includes( mp.safe_int(node.id) ) ) {
                node = mpp.vm_current.node_set( tree_top )
                }
            }
        if( node ) {
            // Give tree node opportunity to do something
            if( bottom ) {
                node.navigate_init( bottom )
                }
            // Set browser title
            let title = mp.sandbox.name
            node.name && ( title = title + " - " + node.name )
            document.title = title
            }
        // Set the show breadcrumb observer based on deepest non-nested panel
        const show_breadcrumbs = bottom &&
                    bottom.dataset.no_breadcrumbs != 'true'
        mpp.vm_main.show_breadcrumbs( show_breadcrumbs )
        }

    mpp.navigate_start_point = function() {
    /*
        Determine the navigation starting point on portal load.
        ASSUMES ANY DYNAMIC mp.nav links/panels have been created.
    */
        let path = mp.nav_path_deeplink( window.location.pathname )
        // Was a specific path passed in?
        if( mpp.nav_to_path ) {
            path = mpp.nav_to_path
            }
        // Was content id was passed in page load
        else if( mpp.nav_to_content_id ) {
            path = find_content_path( mpp.nav_to_content_id )
            }
        // Use local saved path if no path or vueportal path
        else if( !path ) {
            path = mp.local_nav.path || ''
            }
        // If viewer, set address of item to return to as current;
        // it will be moved to previous address if successful
        const viewer = viewer_path( path )
        if( viewer ) {
            mp.nav_current( find_content_path( viewer.tree || viewer.item ) )
            }
        return mp.nav_set_path( path, true )
        }

    mpp.nav_set_path_content = function( id, force ) {
        return mp.nav_set_path( find_content_path( id ), force )
        }

    mpp.nav_content_address = function( id ) {
    /*
        Returns portal path to content or undefined if no
        match to content id
    */
        const content_path = find_content_path( id )
        if( content_path ) {
            return mp.nav_path_full( content_path )
            }
        }

    mpp.nav_set_panel = function( element, path, nested, vm ) {
        // Set portal panel up
        mp.nav_set_panel( element, path )
        $( element ).attr({
            'data-panel_name': vm && vm.name,
            'data-panel_nested': !!nested,
            })
        }

    mpp.nav_path = function( element, vm, ignore_parent ) {
    /*
        Determine element's panel path location based on relative location
        in nav_panel hierarchy and either vm content or element id.
    */
        // If the VM has a hard-coded path option, use it
        if( vm && vm.sb_option && vm.sb_option('portal.nav_path') ) {
            return vm.sb_option('portal.nav_path')
            }
        let path = mp.nav_panel_parent_path( element )
        // If an id is already associated with element add it
        if( ignore_parent ) {
            const frags = _.trim( path, mp.nav_deeplinker ).split( mp.nav_deeplinker )
            frags.pop()
            path = frags.join( mp.nav_deeplinker ) + mp.nav_deeplinker
            }
        // If an id is already associated, use it instead of VM slug
        const slug = element.id || ( vm && vm.get_slug ? vm.get_slug() : '' )
        return path + slug
        }

    mpp.nav_path_current_panels = function() {
    /*
        Return observable array of panel objects for non-nested elements
        in the current path.
    */
        return _current_panels
        }
    const _current_panels = ko.observableArray()

    function set_current_panels( path ) {
        _current_panels.removeAll()
        const panels = $( mp.nav_get_panel( path ) )
                .parents(".mp_nav_panel").addBack()
        panels.each( function() {
            if( this.dataset.panel_nested != 'true' ) {
                _current_panels.push( this )
                }
            })
        }

    mpp.start_content_viewer = function( item, tree ) {
    /*
        Content viewer
        See note above for how viewer URLs are managed separately.
        The viewer URL namespace is based on content and tree ids.
    */
        let path = viewer_make_address( item, tree )
        path = mp.nav_concat( mpp.nav_portal().path, path )
        // Force path if video is same to let viewer decide what to do
        mp.nav_set_path( path, true )
        }

    function find_content_path( id ) {
    /*
        Given a VM or content id, return the best path to display in the portal.
        Because of lazy instantiation of portals, this will return the
        path to the root collection of the item. Content items may still
        need to be scrolled into view, etc. to be seen.
    */
        let rv = ''
        if( id ) {
            id = id.id || id
            // Find the root for the id; try tree and then item lookup
            let root = mpp.vm_trees().get_id( id )
            if( root ) {
                root = root.my_root()
                }
            if( !root ) {
                const item = mpp.vm_items().get_id( id )
                const roots = item && item.model.roots()
                const root_model = roots && roots.length && roots[0]
                root = root_model && mpp.vm_trees().get_id( root_model.id )
                }
            if( root ) {
                // TBD - add code to find tab for content, or define a default
                const address = mpp.nav_portal().parent
                const path = mp.nav_concat( address.path, root.get_slug() )
                rv = mp.nav_path_full( path )
                }
            }
        return rv
        }

    /*
        Manage viewer path creation from VMs
        The viewer path encodes the item to be viewed, along with the
        tree it is displayed in (if there is one).
        To support duplicate slug paths, ID may be added to both the
        item and tree paths.
    */
    const ITEM_SEP = '+'
    // RegEx used to break down the viewer path
    // There are varying lengths of matches depending on whether there is tree
    const SLUG = '[^\\s/\\\\|+!%{}()\\[\\]]'
    const _address_re = new RegExp(
            SLUG + '*' + VIEWER_PATH + '\\' + ITEM_SEP +    // Any portal prefix
            '([a-zA-Z]+)' +                                 // Viewer type
            '\\' + ITEM_SEP + '('+SLUG+'+)' +               // Item slug
            '(?:\\' + ITEM_SEP + '('+SLUG+'+))?'            // Optional tree slug
            )
    function viewer_path( path ) {
        const info = _address_re.exec( path )
        if( info ) {
            return {
                type: info[1],
                item: mpp.vm_items().get_from_slug( info[2] ),
                tree: mpp.vm_trees().get_from_slug( info[3] ),
                }
            }
        }
    function viewer_make_address( item, node ) {
        if( !item ) {
            mp.log_info("Missing item, aborting viewer address")
            return ''
            }
        // Note that get slug may add id integer if dupe
        let rv = VIEWER_PATH + ITEM_SEP + item.type_db +
                    ITEM_SEP + item.get_slug()
        if( node && node.id ) {
            rv += ITEM_SEP + node.get_slug()
            }
        return rv
        }

    })();
