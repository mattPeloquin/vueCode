/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Javascript dialogs

    vex.js was originally used, and several packages like sweetalert2 were
    considered, but ultimately MPF needs are narrow compared to these
    packages. The amount of code necessary to bend them to MPF
    needs was about the same as building dialogs into MPF.
*/
(function() { 'use strict';

    mp.dialog_html = function( template, options ) {
    /*
        Open dialog with HTML string or selector to element to get HTML from.
    */
        options = _.extend( {}, mp.dialog.options, options )
        options.body = _.isString( template ) ? template : $( template ).html()
        return mp.dialog.open( options )
        }

    mp.dialog_open = function( text, title, options ) {
        options = _.extend( {}, mp.dialog.options, options )
        options.body =
            '<div class="es_dialog_text">' +
                text +
                '</div>'
        if( title ) {
            options.body = '<h2>' + title + '</h2>' + options.body
            }
        return mp.dialog.open( options )
        }

    mp.dialog_error = function() {
        const msg = $.makeArray( arguments ).join("<br>")
        return mp.dialog_open( msg )
        }

    mp.dialog = {
    /*
        Dialog is a global object to allow default modifications
    */
        options: {
            modal: true,
            },
        open: function( options ) {

            // Setup the dialog
            const template = $("#template_dialog").html()
            const wrapper = $( template ).appendTo("body")
            if( options.modal ) {
                wrapper.addClass('es_dialog_modal')
                }

            // Fill the content and center
            const dialog = wrapper.find(".es_dialog_body")
            dialog.html( options.body )
            const box = wrapper.find(".es_dialog_box")
            const space = $( window ).height() - box.height()
            const top = space < 1 ? 0 : space / 2
            wrapper.css({ 'top': top + 'px' })

            // Handle post processing
            if( options.after_open ) {
                options.after_open( dialog )
                }
            dialog.close = function() {
                wrapper.remove()
                }

            return dialog
            }
        }

    // Event handlers
    $( document ).on( 'click', ".es_dialog_wrapper", function() {
            $( this ).remove()
            })
    $( document ).on( 'click', ".es_dialog_box", function( event ) {
            event.stopPropagation()
            })
    $( document ).on( 'click', ".es_dialog_close", function() {
            $( this ).parents(".es_dialog_wrapper").remove()
            })

    })();
