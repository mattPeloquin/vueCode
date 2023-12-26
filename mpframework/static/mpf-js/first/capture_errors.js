/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Capture errors and phone home support
*/
(function() { 'use strict';

    /*
        Log uncaught exceptions and prevent default handling

        This can catch MPF comparability issues or bugs, but will also
        catch any problems in user-added HTML. These cases are all still
        logged, but try to proactive detect programming issues
        with _errors_fatal checks, as those get higher logging priority.
    */
    window.onerror = function( message, url, line, col, error ) {
        const msg = line + ":" + col + " " + url + " - " + message
        mp.log_error("ONERROR " + msg)

        // Add attribute for use with Selenium test scripts
        if( mp.testing ) {
            this.getElementsByTagName("body")[0]["JS-ERROR"] = msg
            }

        return true
        }

    // Check and report errors on startup
    mp._errors_fatal = {}
    function report_errors() {
        // Run any tests that were registered to test for fatal errors
        let errors = ''
        try {
            for( var key in mp._errors_fatal ) {
                try {
                    if( mp._errors_fatal.hasOwnProperty( key ) &&
                            mp._errors_fatal[ key ]() ) {
                        errors += key + ' '
                        }
                    }
                catch( e ) {
                    errors += e + ' '
                    }
                }
            }
        catch( e ) {
            errors += e
            }
        /*
            Error message priority
            FATAL if errors in loading window, LONG if longer, SUSPECT if shorter.
            Sampling from the wild has shown load errors that involve the
            browser temporarily stopping processing; for example restoring
            a large number of sessions, where the browser/device is overloaded.
            There are also cases where the report_errors timeout is triggered
            early, before the amount of time passed, which is probably a bot that
            has accelerated setTimeout for some reason.
        */
        let prefix = ''
        if( errors ) {
            const time = mp.timer_delta()
            if( time * 1.2 < mp.timeout_error ) {
                prefix = 'SUSPECT'
                }
            else if( mp.timeout_error * 1.4 > time ) {
                prefix = 'FATAL'
                }
            else {
                prefix = 'LONG'
                }

            // Always show refresh error overlay if a fatal error occurred
            const loading = document.getElementById('mp_loading')
            const error = document.getElementById('mp_loading_error')
            const wait = document.getElementById('mp_wait_full')
            loading && ( loading.style.display = 'none' )
            error && ( error.style.display = 'block' )
            wait && ( wait.style.display = 'none' )
            }

        // Send back any errors from the log that happened in loading time frame
        const log = mp.log_events.join('').toLowerCase()
        let first_error = log.indexOf('error')
        if( first_error === -1 ) {
            first_error = log.indexOf('exception')
            }
        if( first_error !== -1 ) {
            errors += log.substring( first_error, first_error + 32 )
            }

        errors && mp.log_phone_home( prefix + ' ' + errors )
        }
    setTimeout( report_errors, mp.timeout_error )

    // Load test makes sure the loading screen is not still showing
    mp._errors_fatal['LOAD'] = function() {
        const loading = document.getElementById('mp_loading')
        return loading && !loading.classList.contains('mp_hidden')
        }

    })();
