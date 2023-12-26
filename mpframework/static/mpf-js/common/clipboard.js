/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Copy-paste clipboard tools
*/
(function() { 'use strict';

    mp.init_clipboard = function( element ) {
    /*
        Add clipboard handling
    */
        element = element || window.document.body

        // Setup handler for clicks
        $( element ).on( 'click', ".mp_clipboard_button", _handler )

        // Add buttons to existing elements
        mp.init_clipboard_buttons( element )

        }

    mp.init_clipboard_buttons = function( element ) {
    /*
        Setup a clipboard button
    */
        $( element ).find(".mp_clipboard").each( function() {
            const e = $( this )
            let button_point = e.find(".mp_clipboard_display")
            if( !button_point.length ) {
                button_point = e
                e.addClass('mp_clipboard_inline')
                }
            const button = $('<div class="mp_clipboard_button"></div>')
            button_point.append( button )
            mp.init_tooltips( button[0], {}, mpt.CLIPBOARD_HELP )
            })
        }

    function _handler() {
    /*
        Do clipboard copy for button target
    */
        try {
            // Look up to closest parent, then look for target
            const parent = $( this ).parents(".mp_clipboard").first()
            let target = parent.find(".mp_clipboard_target").first()
            if( !target.length ) {
                target = parent.find(">:first-child")
                }
            // Copy the text from first element under parent/target
            const text = _.trim( target.text() )
            navigator.clipboard.writeText( text ).then(
                function() {
                    // Show message for success
                    const button = parent.find(".mp_clipboard_button")
                    mp.show_tooltip( button[0], mpt.CLIPBOARD_COPIED )
                    },
                function( error ) {
                    // Fail silently
                    mp.log_info(`Clipboard: ${ error }`)
                })
            }
        catch( e ) {
            mp.log_error("Exception copying to clipboard: ", this, e)
            }
        }

    })();

