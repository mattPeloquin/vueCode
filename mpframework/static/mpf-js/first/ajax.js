/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Ajax call wrappers

	Some parts of this code are based on assumptions of use of
	MPF respond_api conventions in terms of handling
	success, error, and values response items
*/
(function() { 'use strict';

    mp.unpack_nested_json = function( obj ) {
    /*
        Try to unpack nested dictionaries in JSON
        This isn't intended to be foolproof, but should work on embedded JSON that
        is sent from server APIs
    */
        let rv = obj
        if( typeof obj !== 'object' ) {
            try {
                rv = JSON.parse( obj )
                }
            catch( e ) {
                mp.log_error("Problem parsing json, skipping:", mp.print_obj(obj))
                }
            }
        if( typeof rv === 'object' ) {
            for( var key in rv ) {
                // Recursively unpack items that look like dicts
                if( _.startsWith( rv[key], '{' ) ) {
                    rv[ key ] = mp.unpack_nested_json( rv[ key ] )
                    }
                }
            }
        return rv
        }

    mp.fetch = function( ajax ) {
    /*
        Convenience function for ajax calls

        Requires url to be explicitly passed.
        Defaults to asynchronous json GET with global options,
        with success handler in ajax.finished.
    */
        ajax.url = (ajax.url === 'CURRENT_URL') ? window.location.href : ajax.url

        // If ajax call isn't valid, may not make call to server
        if( !mp.ajax_validate( ajax ) ) return

        // Don't use jQuery global handlers
        ajax.global = false

		// Setup defaults
        ajax.timeout = ajax.timeout !== undefined ? ajax.timeout : mp.timeout_error
        ajax.async = ajax.async !== undefined ? ajax.async : true
        ajax.method = ajax.method !== undefined ? ajax.method : 'GET'
        ajax.wait_indicator = ajax.wait_indicator !== undefined ? ajax.wait_indicator : false

		// Support normal or json-wrapped data
        if( ajax.json_data ) {
            ajax.data = { json_data: JSON.stringify( ajax.json_data ) }
            }
        else {
            ajax.data = ajax.data !== undefined ? ajax.data : ''
            }

        // Set wait indicator -- if false none, if boolean true, use full screen, otherwise element
        let wait_item = null
        if( ajax.wait_indicator ) {
            wait_item = ajax.wait_indicator === true ? '#mp_wait_full' : ajax.wait_indicator
            mp.show_wait( $( wait_item ), true )
            }

        // Client-requested caching
        if( ajax.browser_cache ) {
            ajax.headers = {
                'cache-control': 'max-age=' + mp.sandbox.cache_age,
                }
            ajax.url = ajax.url + '/' + mp.sandbox.cache_group
            }

        // Register progress bar
        // For simplicity, always build custom xhr, since jQuery doesn't have progress hooks
        ajax.xhr = function () {
            const xhr = $.ajaxSettings.xhr()
            ajax.progress && ajax.progress( xhr )
            return xhr
            }

        // Fixup jqXHR with URL and add CSRF support for ajax
        ajax.beforeSend = function( jqXhr, settings ) {
            jqXhr.url = ajax.url
            mp.ajax_csrf_add( jqXhr, settings )
            }

        mp.log_info("Fetch ", ajax.method, ": ", ajax.url )

        return $.ajax( ajax )
            .then(
                function ajax_done( data, status, xhr ) {
                    // Call "finished" success handler if provided and no error
                    mp.show_wait( $( wait_item ), false )
                    mp.log_info("Fetch done: ", status, " -> ", xhr.url)
                    if( ajax.finished ) {
                        ajax.finished.call( this, data )
                        }
                    },
                function ajax_fail( xhr, status, error ) {
                    mp.show_wait( $( wait_item ), false )
                    if( ajax.failed ) {
                        ajax.failed.call( this, error )
                        }
                    else {
                        if( ajax.finished ) {
                            ajax.finished.call( this, {} )
                            }
                        mp.ajax_error( xhr, status, error )
                        }
                    })
        }

    mp.ajax_validate = function( ajax ) {
        if( mp.user.is_authenticated || _.includes( ajax.url, mpurl.public ) ) {
            return true
            }
        mp.log_error("AUTHENTICATION NEEDED: ", mp.print_obj(ajax))
        mpurl.reload_home()
        }

    mp.ajax_csrf_add = function( xhr, settings ) {
    /*
        For mutable ajax calls add the CSRF value into header
    */
        if( mp.is_csrf_request( settings.type ) ) {
            // Check for cross domain and send back to server for debug or attack info
            const csrf = this.crossDomain ?
                            'CROSS_DOMAIN:' + window.location.href :
                             mp.csrf
            xhr.setRequestHeader( 'x-csrftoken', csrf )
            }
        }

    mp.ajax_error = function( xhr, status, error ) {
    /*
        Central ajax handler for Backbone and MPF calls
        Handle common case of session timeout and other cases with
        a generic error that includes debugging logging
    */
        mp.log_error("AJAX ERROR: ", status, " -> ", xhr.url)
        try {
            // Server will respond with expired=True if session expired, but
            // also check if server responds with web page that wasn't caught,
            // which is probably login or error page
            const json = xhr.responseJSON
            if( ( json && json.expired ) ||
                _.startsWith( _.trimStart( xhr.responseText ), "<!DOCTYPE html>" ) )
                {
                mp.log_error("AJAX SESSION EXPIRED")
                }
            else if( error ) {
                let msg = [ mpt.AJAX_ERROR ]
                if( mp.log_debug_level ) {
                    mp.log_error( error.stack )
                    msg = msg + "\n" + error
                    }
                }

            mp.log_info("AJAX responseText: ", xhr.responseText.slice(0,128))
            }
        catch( e ) {
            mp.log_error("ERROR handling ajax_error:", e)
            }
        }

    })();
