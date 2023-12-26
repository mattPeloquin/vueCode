/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Custom staff menu

    Why custom? Most menu frameworks too bloated, and want to keep the
    menu needs pretty simple yet particular.
    Certainly should be revisited if the client is rewritten.
*/
(function() { 'use strict';

    // Delay before close after focus gone
    mp.MENU_CLOSE_DELAY = 200

    // Delay from open to first element
    const OPEN_CLOSE_DELAY = 400

    const MENU_ROWS =
            ".mp_menu > a.mp_menu_item," +
            ".mp_menu > .mp_menu_item > a," +
            ".mp_menu > .mp_menu_wrapper > a," +
            ".mp_menu_group > a.mp_menu_item," +
            ".mp_menu_group_icons > a.mp_menu_item," +
            ".mp_menu_sub > .mp_menu_item"

    mp.init_menus = function( areas, highlight ) {
    /*
        Simple menu that supports one-level drop down and
        coordinating top and side menus.
    */
        // jQuery delegated handlers are used since some menus are added dynamically
        $( areas )
            // Menus are recursive with mp_menu > mp_menu_item root label,
            // with mp_menu children underneath
            .on( 'mouseenter touchenter pointerenter focusin', ".mp_menu > .mp_menu_item", function() {
                $(this).find(".mp_menu:first").each( menu_show )
                })
            // Hide child menus
            .on( 'mouseleave touchleave pointerleave focusout', ".mp_menu", function() {
                $(this).each( menu_hide )
                })

        // Provide highlight on all dropdown menu items
        mp.style_add_highlight( areas, MENU_ROWS, highlight )

        // Top-level per row handlers for the anchor items in the menu
        $( areas ).find( MENU_ROWS ).addBack()
            .attr( 'draggable', false )
            // Keyboard support
            .focus( function() {
                mp.menu_open( this )
                })
            .blur( function() {
                mp.menu_close( this )
                })

        init_top_menu()
        }

    // Open/close top-level menu items programattically
    mp.menu_open = function( element ) {
        menu_show.apply( menu_parent( element ), arguments )
        }
    mp.menu_close = function( element ) {
        menu_hide.apply( menu_parent( element ), arguments )
        }

    // General menu support

    function menu_parent( element ) {
        return $( element ).parents(".mp_menu_item").last().children(".mp_menu").first()
        }

    function menu_show( keep_open ) {
        $(this).addClass("mp_menu_active")
        keep_open || menu_opened( this )
        }

    function menu_hide( no_delay ) {
        // Delay closing menu slightly on first call, in case mouse
        // is transitioning from top element to menu body
        // Call subsequently to check if mouse is outside body
        const item = this
        setTimeout( function() {
                menu_close( item ) || ( no_delay || menu_hide.apply( item ) )
                },
            no_delay || OPEN_CLOSE_DELAY )
        }

    function menu_opened( item ) {
        // Set timeout after menu open that will close the menu
        // if hover is lost, as it sometimes gets stuck
        setTimeout( function() {
                menu_close( item ) || menu_opened( item )
                },
            mp.MENU_CLOSE_DELAY )
        }

    function menu_close( item ) {
        // Close the menu if not hovering over it or immediate parent
        let hovering = !!$( item ).filter(":hover").length
        if( !hovering ) {
            const float = $( item ).closest(".mp_menu_float")
            if( float.length ) {
                hovering = !!float.find(".mp_menu_item:hover").length
                }
            else {
                hovering = !!$( item ).closest(".mp_menu_item:hover").length
                }
            }
        if( !hovering ) {
            $( item ).removeClass("mp_menu_active")
            return true
            }
        }

    // Keep track of current top-menu selection to put highlight state on it
    mp.menu_active_top = ''
    function init_top_menu() {
        // Set top-level menu item active when child used
        $("#mptopmenu").find( MENU_ROWS ).click( function() {
                $(this).closest("#mptopmenu > .mp_menu_item")
                    .each( _set_top_active )
                })
        // Set the default top level
        if( !mp.is_portal ) {
            $( _get_active( sessionStorage.getItem('mptopmenu') ) )
                .each( _set_top_active )
            }
        }
    function _set_top_active() {
        if( !mp.menu_active_top || !mp.menu_active_top.is( $(this) ) ) {
            $("#mptopmenu .mp_menu_active_staff").removeClass("mp_menu_active_staff")
            $(this).addClass("mp_menu_active_staff")
            sessionStorage.setItem( 'mptopmenu',
                        $(this).find("> a > .mp_menu_text").first().text() )
            mp.menu_active_top = $(this)
            }
        }
    function _get_active( text ) {
        let rv = null
        if( text ) {
            rv = $("#mptopmenu .mp_menu_header > a > .mp_menu_text:contains('" + text + "')").first()
                    .closest(".mp_menu_item")
            }
        return rv
        }

     })();
