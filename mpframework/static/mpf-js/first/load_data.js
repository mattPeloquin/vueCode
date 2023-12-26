/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Support asynchronous portal model/data load as early as possible.
*/
(function() { 'use strict';

    // Data placed into objects until it is ready for use
    mp.load_data = {}
    mp.load_json_data = function( objects ) {
        for( var group_name in objects ) {
            mp.load_data[ group_name ] = objects[ group_name ]
            }
        }

    // Make the calls to get data
    mp.raw_urls_load = function( urls ) {
        urls.forEach( function( url ) {
            fetch( url )
                .then( function( response ) {
                    mp.log_highlight2("RECEIVED: " + url )
                    return response.json()
                    })
                .then( data => mp.load_json_data( data ) )
            })
        }

    // Lightweight JSON parse wrapper
    mp.json_parse = function( data ) {
        let rv = {}
        try {
            rv = JSON.parse( data )
            }
        catch( e ) {
            mp.log_error("JSON EXCEPTION: ", e, " -> ", data)
            }
        return rv
        }

    })();
