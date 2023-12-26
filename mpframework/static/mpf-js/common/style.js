/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    CSS style fixups

    Although preference is to handle styles in CSS, when JS
    manipulation will simplify code, do style fixups here.
    This file has hard-coded dependencies on CSS names
*/
(function() { 'use strict';

    mp.style_get_css = function( selector, attribute ) {
    /*
        Grab CSS style attributes dynamically to support
        adding style like background color selectively.
    */
        let rv = _styles[ selector+attribute ] || ''
        if( !rv ) {
            try {
                const item = $(
                    "<div id='mp_style_DYNAMIC' class='" + selector + "'></div>"
                        ).appendTo("body")
                rv = item.css( attribute )
                item.remove()
                _styles[ selector+attribute ] = rv
                }
            catch( e ) {
                mp.log_error("Exception getting style: ", selector, " - ",
                        attribute, " - ", e)
                }
            }
        return rv
        }
    let _styles = {}

    mp.style_add_css = function( target, source, attribute ) {
    /*
        Add the extracted dynamic style to body
    */
        const attr = mp.style_get_css( source, attribute )
        mp.style_add( target, { attribute: attr } )
        }

    //-------------------------------------------------------------------
    // Dynamic style initialization

    mp.style_init = function() {
        mp.log_info2("Initial style init")

        // Staff page dynamic styling
        mp.is_page_admin && mp.init_admin_style()

        // Add MPF style to input elements
        $("input, select, textarea, .mp_checkbox label")
            .not( '.mp_input_no, .mp_button, .mp_button_flat, .mp_button_text,' +
                    '.es_button, .es_button_flat, .es_button_text,' +
                    ':input[type=submit], :input[type=checkbox], :input[type=image]')
            .addClass('mp_input')

        // Set initial help text state (assumes preferences loaded)
        $( mp.HELP_STAFF_SELECTOR ).toggleClass( 'mp_hidden', mp.help_off() )

        // Add tabstop for checkboxes
        $(".mp_checkbox label").attr( 'tabindex', 0 )

        // Update locale elements; call locale on string, and then on any integers
        $(".mp_locale_value").html( function( _index, old_html ) {
            let rv = ""
            _.each( old_html.toLocaleString('en').trim().split(" "), function( word ) {
                let number = parseInt( word )
                rv += ( _.isNaN( number ) ? word : number.toLocaleString('en') ) + " "
                })
            return rv
            })

        // :empty_if_whitespace functionality
        $(".mp_hide_empty").each( function() {
            if( !_.trim( $( this ).text() ) ) {
                $( this ).addClass('mp_hidden')
                }
            })
        }

    //-------------------------------------------------------------------
    // Dynamic Style support needed on an on-going basis

    mp.style_add = function( selector, css, index ) {
    /*
        Safely add or update style by picking last style sheet
        which is from the same origin.
        Returns index added or updated.
    */
        try {
            _stylesheet = _stylesheet || _create_stylesheet()
            // Check for existing rule if specific over 0 given
            if( !index ) {
                for( var i=0; i < _stylesheet.cssRules.length; i++ ) {
                    if( _stylesheet.cssRules[ i ].selectorText == selector ) {
                        index = i
                        break
                        }
                    }
                }
            // Update an existing rule
            if( index !== undefined ) {
                _stylesheet.cssRules[ index ].style.cssText = css
                }
            // Create new one
            else {
                let css_text = ''
                _.forOwn( css, function( value, key ) {
                    css_text += key + ':' + value + ';'
                    })
                const rule = selector + '{' + css_text + '}'
                index = _stylesheet.insertRule( rule )
                }
            return index
            }
        catch( e ) {
            mp.log_error("Cannot set dynamic styles: ", e)
            }
        }
    let _stylesheet = false
    function _create_stylesheet() {
        // Create new style sheet to avoid insertRule browser security
        // errors from adding to existing one
        const tag = document.createElement('style')
        const head = document.getElementsByTagName('head')[0]
        head.appendChild( tag )
        return tag.sheet
        }

    mp.style_add_highlight = function( listener, selector, style ) {
    /*
        Setup highlight using delegated event handler
    */
        style = style || 'es_theme_highlight'
        $( listener )
            .on( 'touchenter pointerenter focusin mouseover', selector,
                function() {
                    $(this).addClass( style )
                    })
            .on( 'touchleave pointerleave focusout mouseout', selector,
                function() {
                    $(this).removeClass( style )
                    })
        }

    mp.style_add_draggable = function( selector ) {
        $( selector ).draggable({
            helper: 'clone',
            containment: 'document',
            cursor: 'pointer',
            revert: 'invalid',
            revertDuration: 100,
            opacity: 0.7,
            distance: 10,
            })
        }

    mp.style_make_active = function( element, old_element, active_style ) {
    /*
        Support multi-select style elements with one active item in a group
    */
        active_style = active_style || "es_theme_current"
        // Mark the current selected item as active, and remove state from old one
        $( element ).addClass( active_style )
        old_element && $( old_element ).removeClass( active_style )

        // Preserve active state even when there are jQuery mouse events that remove active
        // Need to use a timer to ensure processing occurs after jQuery removed active style
        function preserve_active() {
                const el = this
                setTimeout( function() {
                    $( el ).addClass( active_style )
                    })
                }
        $( element ).on( 'mouseleave', preserve_active )
        $( old_element ).off('mouseleave')
        }

    })();
