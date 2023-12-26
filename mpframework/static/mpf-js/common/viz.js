/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Hide/show visibility support
*/
(function() { 'use strict';

    mp.viz_set_toggle = function( toggle_switch, toggle_area, options ) {
    /*
        Hide/show toggle
        Provide click and key press support for UI elements that control
        visibility of other elements.
        By default stores state in preferences, which will restore on load.
        Key support only works if item can have focus.
        NOTE - switch and area can be a collection of jQuery elements,
        so make sure selectors are specific enough for the given scenario.
        NOTE - closing peers option only works when the switch is a sibling
        or parent of the target area.
    */
        options = options || {}
        const tswitch = $( toggle_switch )
        const tarea = $( toggle_area )
        if( !tswitch.length || !tarea.length ) {
            return
            }
        if( tswitch.hasClass('es_viz_toggle') ) {
            return
            }
        // Add initial CSS
        const switch_class = options.switch_class || ''
        const close_peers = tswitch.hasClass('mp_viz_close_peers')
        tswitch
            .addClass( 'es_viz_toggle ' + switch_class )
            .addClass( tarea.hasClass('mp_hidden') ?
                        'es_viz_collapsed' : 'es_viz_expanded' )
        tarea.addClass('es_viz_target')
        // Toggle element, store state, show/hide expand/collapse icons
        function mptoggle( _event ) {
            _mptoggle( tswitch, tarea )
            // Close other peers if only one should be open
            if( close_peers ) {
                const parent = $( tswitch ).parents(".mp_viz_peer_group").last()
                $( parent ).find(".es_viz_expanded").not( tswitch ).each( function() {
                    const area = mp.viz_find_area( $( this ) )
                    if( area.length ) {
                        _mptoggle( $( this ), area )
                        }
                    })
                }
            }
        function _mptoggle( swtch, area ) {
            if( options.viz_fn ) {
                options.viz_fn( swtch, area )
                }
            area.toggleClass('mp_hidden')
            swtch.toggleClass('es_viz_collapsed es_viz_expanded')
            if( options.switch_toggle_class ) {
                swtch.toggleClass( options.switch_toggle_class )
                }
            // Save state to local preferences by default
            if( !options.no_save ) {
                mp.preference_store( swtch.mpselector(), 'toggle_viz',
                            !area.hasClass('mp_hidden'), 'viz' )
                }
            }
         tswitch
            .on('click', mptoggle )
            .keydown( function( event ) {
                if(_.includes( [13, 39, 40], event.keyCode )) {
                    mptoggle()
                    }
                })
        // Add expansion icon
        // By default assume icon being added to line, but it optional
        // to allow for no icon or custom UI layout of switch
        if( !options.no_icon ) {
            tswitch.addClass('mp_flex_line')
            $('<span class="es_viz_icon"></span>')
                .prependTo( tswitch )
                .addClass( switch_class )
            }
        if( !options.no_pointer ) {
            tswitch.addClass('es_pointer')
            }
        // Set any preferences for items
        mp.preferences_init('viz')
        }

    mp.viz_find_area = function( swtch ) {
    /*
        Given a viz switch, find the area associated with it
    */
        let rv = $( swtch ).siblings(".es_viz_target")
        if( !rv.length ) {
            rv = $( swtch ).find(".es_viz_target")
            }
        return rv
        }

    mp.viz_add_toggle = function( element, options ) {
    /*
        Setup viz_toggle based on sibling relationship of
        mp_viz_switch and mp_viz_area.
    */
        $( element ).find(".mp_viz_switch").each( function() {
            const area = $( this ).siblings(".mp_viz_area")
            mp.viz_set_toggle( this, area, options )
            })
        }

    })();
