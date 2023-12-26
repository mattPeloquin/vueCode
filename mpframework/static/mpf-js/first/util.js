/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Utils needed early
*/
(function() { 'use strict';

    mp.load_script = function( url, options ) {
    /*
        Load script from the given url
    */
        const node = document.createElement('script')
        node.src = url
        node.async = true
        _.extend( node, options )
        document.getElementsByTagName('head')[0].appendChild( node )
        }

    mp.is_csrf_request = function( type ) {
        return ! /^(GET|HEAD|OPTIONS|TRACE)$/.test( type )
        }

    mp.add_onload = function( new_onload_fn ) {
        const existing = window.onload
        if( existing ) {
            window.onload = () => {
                existing()
                new_onload_fn()
                }
            }
        else {
            window.onload = new_onload_fn
            }
        }

    // Debug utilities

    mp.debugger = function( stop ) {
        // Drop mp.debugger() into template code to force break
        if( stop || mp.debug ) {
            debugger
            }
        }
    mp.print_obj = function( obj ) {
        let rv = ""
        for( var item in obj ) {
            rv += item + ": " + obj[ item ] + "\n"
            }
        return rv
        }
    mp.html_obj = function( obj ) {
        let rv = ""
        for( var item in obj ) {
            rv += item + ": " + obj[ item ] + "<br>"
            }
        return rv
        }

    })();
