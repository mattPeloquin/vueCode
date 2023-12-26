/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Javascript and jQuery extensions
*/
'use strict';

// Standard public domain addition for DST detection
Date.prototype.stdTimezoneOffset = function() {
    const jan = new Date( this.getFullYear(), 0, 1 )
    const jul = new Date( this.getFullYear(), 6, 1 )
    return Math.max( jan.getTimezoneOffset(), jul.getTimezoneOffset() )
    };
Date.prototype.dst = function() {
    return this.getTimezoneOffset() < this.stdTimezoneOffset()
    };

(function($) {

    // Make jQuery ready wait until MPF is ready
    $.holdReady( true )

    $.fn.change_val = function( value ) {
        // Change both internal dom value and default HTML value
        return $(this).attr( 'value', value ).val( value )
        }

    $.fn.is_screen_positioned = function() {
        return _.includes( ['fixed', 'absolute'], $(this).css("position") )
        }

    $.fn.mpselector = function( ignore, match ) {
    /*
        Return a fairly specific selector string for FIRST jQuery object.
        Don't add class names provided in ignore list.
    */
        if( !this.length ) {
            return
            }
        ignore = ignore || [ 'mp_hidden' ]
        match = match || [ 'es_id_' ]
        const item = this[0]
        const parent = $( item ).parent()[0]
        let rv = add_classes( parent, ignore, match )
        $( parent ).parents("pane, panel, tool, section, item").each( function() {
            rv = add_classes( this, ignore, match ) + ' ' + rv
            })
        rv =  rv + ' > ' + add_classes( item, ignore, match )
        return rv
        }
    function add_classes( item, ignore, match ) {
        // Check for unique id
        if( item.id ) {
            return '#' + item.id
            }
        // Then try to come up with a reasonable length match
        // with a focus on looking for specifc match classes
        let rv = ''
        if( item.classList && item.classList.length ) {
            _.every( item.classList, function( name ) {
                // Return for specific content for first match class
                _.every( match, function( m ) {
                    if( _.startsWith( name, m ) ) {
                        rv += '.' + name
                        return false
                        }
                    return true
                    })
                // Otherwise grab the first class
                if( !rv && !_.includes( ignore, name ) ) {
                    rv += '.' + name
                    }
                return true
                })
            }
        return rv
        }

    })( window.jQuery );
