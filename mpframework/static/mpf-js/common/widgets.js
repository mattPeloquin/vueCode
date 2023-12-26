/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Shared Client UI widget code requiring Javascript support
    These don't have anything to do with server template widgets.
*/
(function() { 'use strict';

    mp.help_off = function() {
        return $(".mp_help_staff_toggle").hasClass('mp_off')
        }

    mp.set_watermark = function( selector, watermark ) {
    /*
        Support setting the placeholder value for Django form
        fields in the template, so creating form widget not necessary
    */
        const item = $( selector )
        if( item.length && watermark ) {
            item.attr( 'placeholder', watermark )
            }
        }

    mp.set_hover = function( element, target, css1, css2 ) {
    /*
        Javascript Hover
        Although CSS hover is default for framework, if hover needs to be
        triggered or more control is needed, use this mouse enter/leave.
        Also opens menu if it is target, to support highlighting menu items.
    */
        const menu = target && $( target ).closest(".mp_menu").length
        target = target || element
        $( element )
            .mouseenter( function() {
                menu && mp.menu_open( target, true )
                $( target ).addClass( css1 )
                css2 && $( target ).addClass( css2 )
                })
            .mouseleave( function() {
                menu && mp.menu_close( target, true )
                $( target ).removeClass( css1 )
                css2 && $( target ).removeClass( css2 )
                })
        }
    mp.set_highlight = function( element, target ) {
        mp.set_hover( element, target, "mp_effect_highlight" )
        }

    mp.show_wait_init = function() {
    /*
        Wait spinner
        Use the show_wait method to attach a spinner to items; use
        with #mp_wait_full to make a modal screen spinner.
    */
        // Setup CSS to use theme color
        const color = mp.style_get_css( 'es_theme_highlight', 'background-color' )
        mp.style_add( '.mp_spinner h1', { 'color': color } )
        mp.style_add( '.mp_spinner spinner spin1', {
                'border-top-color': color,
                'border-right-color': color,
                'border-bottom-color': + color,
                })
        mp.style_add( '.mp_spinner spinner spin2', {
                'border-right-color': color,
                ';border-bottom-color': color,
                ';border-left-color': color,
                })
        }

    mp.show_wait = function( items, show, msg ) {
        items.each( function() {
            if( show ) {
                if( !$(this).children(".mp_spinner" ).length ) {
                    const spinner =
                        $('<div class="es_spinner mp_spinner">' +
                                '<spinner>' +
                                    '<spin1></spin1><spin2></spin2>' +
                                    '</spinner></div>')
                            .appendTo( $(this) )
                    // Display optional message
                    if( msg ) {
                        $( '<h1>' + msg + '</h1>' ).prependTo( $( spinner ) )
                        }
                    }
                else {
                    $(this).find(".mp_spinner h1").html( msg )
                    }
                }
            else {
                $(this).find('.mp_spinner').remove()
                }
            })
        if( items[0] === _wait_full[0] ) {
            _wait_full.toggleClass( 'mp_hidden', !show )
            }
        }

    mp.show_wait_overlay = function( show, msg ) {
        mp.show_wait( _wait_full, show, msg )
        return _wait_full
        }
    const _wait_full = $("#mp_wait_full")

    jQuery.fn.extend({
        show_wait: function( msg ) {
            mp.show_wait( this, true, msg )
            return this
            },
        hide_wait: function() {
            mp.show_wait( this, false )
            return this
            },
        })

    mp.set_country_selector = function( element ) {
    /*
        Country selection field is not used frequently, so populate from
        a cached ajax call as needed vs. sending with every page.
    */
        // Only try to fill if country is visible
        element = $( element )
        if( element.length < 1 || !element.is(":visible") ) {
            return
            }
        // Retreive list of country options if not done already and set
        if( _country_options ) {
            element.html( _country_options )
            }
        else {
            mp.fetch({
                url: mpurl.api_widget_country_options,
                wait_indicator: element,
                finished: function( values ) {
                    _country_options = values["country_options"]
                    element.html( _country_options )
                    }
                })
            }
        }
    let _country_options = ''

    })();
