/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Additions to viewer functionality
*/
(function() { 'use strict';

    // Setup default width to look for aspect ratio on some viewers
    _.extend( mpp.viewer_content_width, {
        'default': function( iframe_html ) {
            const body = $( iframe_html ).find("body")
            let aspect = body.data('aspect_ratio')
            if( aspect ) {
                const width = Math.floor( aspect * body.height() )
                return width + 'px'
                }
            }
        })

    /*
        Insert viewer moves viewer block display into portal DOM.
        Do complete rebuild every time and move viewer to first
        visible current item.
    */

    // Play video or other item when viewer is launched?
    mpp.auto_play = true

    // Factory for two versions of viewer_insert
    function viewer_insert_factory( toggle_close ) {
        function viewer_insert_setup( _type, item, _tree ) {
            // If not closing viewer, carry on with with process
            const toggle_same = mpp.viewer_last_item() === item.model
            const stop_viewing = toggle_close && toggle_same &&
                        mpp.viewer_is_visible()
            // Always kibosh viewer to make open/close and moving around robust
            mpp.viewer_remove()
            if( !stop_viewing ) {
                // Returning false disables direct access viewer reuse
                return false
                }
            }
        return viewer_insert_setup
        }
    mpp.viewer_setups['viewer_insert'] = viewer_insert_factory( true )
    mpp.viewer_setups['viewer_panel'] = viewer_insert_factory( false )

    function viewer_insert_move( _access ) {
    /*
        If a viewer insert element is visible, use it now.
        If not, try navigating to current item and then to viewer.
    */
        const item_elements = mpp.vm_current.item().jQuery()
        if( item_elements.length ) {
            insert_placement( item_elements )
            }
        else {
            setTimeout( function() {
                // The portal location should be in previous
                mp.nav_set_path( mpp.nav_portal().path )
                mp.nav_set_path( mp.nav_previous().path )
                })
            }
        }
    mpp.viewer_moves['viewer_insert'] = viewer_insert_move

    function insert_placement( item_elements ) {
        // Place viewer after current visible elements for current item
        item_elements.each( function() {
            const item = $(this)
            if( item.is(":visible") ) {
                $( mpp.VIEWER_ELEMENT ).hide()
                const viewer = $( mpp.VIEWER_ELEMENT ).detach()
                item.after( viewer )
                return false
                }
            })
        }

    })();
