/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Shared code specific to portal apps
*/
(function() { 'use strict';

    // Override Backbone to fix up ajax Backbone overrides
    mp.run_when_ready(
        function() {
            return Backbone !== undefined && mp.ajax_error !== undefined
            },
        function backbone_fixup() {

            // Set emulation for backbone calls, to work around firewall issues
            Backbone.emulateHTTP = mp.compatibility_on

            // Pass ajax fixups to Backbone as sync options
            const backbone_sync_orig = Backbone.sync
            Backbone.sync = function( method, model, options ) {
                options = _.extend( {
                    beforeSend: mp.ajax_csrf_add,
                    error: mp.ajax_error,
                    }, options )
                backbone_sync_orig( method, model, options )
                }
            },
        { no_wait: true });

    mpp.get_template_name = function( name ) {
    /*
        Convert the script_name of templates to the client templates convention
    */
        return name ? 'template_' + name : ''
        }

    mpp.get_items_template_styles = function( name ) {
    /*
        Return CSS styles for items container based on the template.
        HACK - HARDCODING to tempplate naming conventions used to
        classify some common template groups, which cannot
        be determined until they are rendered.
        This helps set container items like flexbox gap, while
        users creating their own templates can ignore and
        use CSS rules directly.
    */
        let rv = {}
        rv[ 'es_' + name ] = true
        try {
            const template_type = name.split('_')[2]
            _template_types.forEach( function( type ) {
                if( _.startsWith( template_type, type ) ) {
                    rv[ 'es_items_' + type ] = true
                    }
                })
        } catch( e ) {
            // Do nothing since users could name templates anything
            }
        return rv
        }
    const _template_types = [
        'list',
        'card',
        'compact',
        ]

    mpp.item_trigger = function( event, data ) {
    /*
        Wrapper for sending current item event (e.g., from viewer iframe)
    */
        mp.log_info("Item event: ", mpp.vm_current.item().name,
                        " -> " + event + ", " + data )
        mpp.vm_current.item().model.trigger( event, data )
        }

    mpp.change_on_hover = function( parent, start_class, hover_class ) {
    /*
        Swap hover state between two classes under a parent
    */
        start_class = start_class || '.mp_hover_off'
        hover_class = hover_class || '.mp_hover_on'
        $( parent ).find( hover_class ).hide()
        $( parent ).hover(
            function() {
                $(this).find( start_class ).hide()
                $(this).find( hover_class ).show()
                },
            function() {
                $(this).find( start_class ).show()
                $(this).find( hover_class ).hide()
                }
            )
        }

    mpp.set_background = function( element, vm ) {
    /*
        Background is transparent by default, so falls through to the site
        theme background. Image may be defined by site or VM to override.
        If collection_no_bgimage is set, need to set background from transparent
        to theme in case underlying layer has an image.
    */
        if( vm && mpp.sb_option(
                'portal.collection_no_bgimage', element, vm ) ) {
            $( element ).addClass('es_theme_background')
            }
        else {
            let image = mp.request.bg_image
            if( vm && vm.id ) {
                if( vm.sb && vm.sb('bg_image') ) {
                    image = vm.sb('bg_image')
                    }
                }
            if( image ) {
                $( element ).attr( 'style',
                    "background-image: url('%img%');".replace('%img%', image ) )
                $( element ).addClass('es_background_image')
                }
            }
        }

    //-------------------------------------------------------------------
    // Shared content code

    mpp.css_toggle_init = function( panel ) {
    /*
        Optional toggling of a CSS class
    */
        const name = 'ctoggle_' + ( $( panel ).data('content_id') || 'global' )

        // Initialize for initial load; default state was setup in template options
        _toggle_update( panel, name, mp.local_ui[ name ] ||
                    mpp.sb_option( 'portal.content_toggle_default', panel ) )

        // Event handlers for state buttons
        $( panel ).on( 'click', '.mpp_toggle_A', function() {
            _toggle_update( panel, name, 'A' )
            mp.layout_resize()
            })
        $( panel ).on( 'click', '.mpp_toggle_B', function() {
            _toggle_update( panel, name, 'B' )
            mp.layout_resize()
            })
        }
    function _toggle_update( panel, name, toggle ) {
        // Switch the UI between text and pict modes
        // List view is baked into the code as the default if the default has
        // not been set by collection, options, or preferences
        mp.local_ui[ name ] = toggle
        const A = $( panel ).find(".mpp_toggle_A")
        const B = $( panel ).find(".mpp_toggle_B")
        if( 'A' == toggle ) {
            A.show()
            B.hide()
            mp.style_make_active( A, B )
            }
        else {
            A.hide()
            B.show()
            mp.style_make_active( B, A )
            }
        }

    /*
        Override content find tree to find closest tree id in portal
        by finding parent collection model.
    */
    const _content_find_tree_id = mp.content_find_tree_id
    mp.content_find_tree_id = function( element ) {
        const tree = mpp.get_model( $( element ).parents(".mp_tree_node").first() )
        if( tree ) {
            return tree.id
            }
        else {
            return _content_find_tree_id( element )
            }
        }

    //-------------------------------------------------------------------
    // Portal-only user support

    mpp.click_render_template = function( template ) {
    /*
        Dynamically create and insert HTML for a popup panel
    */
        function _click_handler( item, event ) {
            event.stopPropagation()
            if( item && item.type_db && item.id ) {
                if( !$( event.target ).find('div').length ) {
                    const _html =
                        _.template( $(`#template_${ template }`).html() )
                                ( item.model.toJSON() )
                    $( event.target ).replaceWith( _html )
                    }
                }
            }
        return _click_handler
        }

    mpp.check_user_level = function( user_level ) {
    /*
        Returns true if current user has access to the user_level
    */
        if( !user_level ) {
            return true
            }
        if( mp.user.is_ready ) {
            switch( user_level ) {
                case user_level == 'E':
                    return mp.user.extended_access
                case user_level == 'G':
                    return mp.user.group_admin
                case user_level == 'S':
                    return mp.user.access_staff
                }
            return true
            }
        }

    })();
