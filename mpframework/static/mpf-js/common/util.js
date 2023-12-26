/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Utils needed early
*/
(function() { 'use strict';

    mp.rand_str = function() {
        // Convert rand float to base-36
        return Math.random().toString(36).substring(2, 15)
        }

    mp.safe = function( fn, default_result, context ) {
    /*
        Safe call wrapper -- assumes failure is benign and can be ignored

        There are areas of JS code where code can be kept simpler by avoiding
        Look-Before-You-Leap coding, and catching exceptions, e.g., accessing
        an object in an event whose type isn't guaranteed.

        This wrapper avoids try-catch blocks in the code, but only supports simple
        semantics for calling method and handling of failure.
    */
        let rv = typeof default_result === 'undefined' ? false : default_result
        try {
            context = context || this
            const fn_args = [].slice.call( arguments ).slice(3)
            rv = fn.apply( context, fn_args )
            }
        catch( e ) {
            mp.log_debug("mp.safe wrapper exception: ", fn, "\nargs: ",
                            fn_args, "\nerror: ", e, "\n", e.stack)
            }
        return rv
        }

    mp.safe_int = function( value ) {
        const i = parseInt( value )
        return isNaN( i ) ? 0 : i
        }
    mp.safe_array = function( values ) {
        return _.isArray( values ) ? values : (values ? [values] : [])
        }

    })();
