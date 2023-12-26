/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

	Framework functionality for inactivity and activity tracking
*/
(function() { 'use strict';

    mp.idle_init = function() {
        _IDLE_CHECK_INTERVAL = parseInt( mp.options.timeout_idle / 4 ) || 600

        // Add activity event handlers
        mp.idle_set_handlers( document )

        // Start timer to check for inactivity
        window.setInterval( _activity_checker, _IDLE_CHECK_INTERVAL * 1000 )
        }

    mp.idle = function() {
    /*
        Returns true if no user activity has occurred within timeout period
    */
        const is_idle = _idle_seconds >= mp.options.timeout_idle
        //mp.log_debug("Checking for inactive: ", is_idle)
        return is_idle
        }

    mp.idle_set_handlers = function( obj ) {
    /*
        Set activity handlers for the given object
        (usually document or frame)
    */
        obj.onclick = mp.idle_reset
        obj.onkeypress = mp.idle_reset
        }

    mp.idle_reset = function() {
    /*
        Called on events to reset count to zero
    */
        if( _idle_seconds > 0 ) {
            //mp.log_debug("Resetting activity tracker; was at: ", _idle_seconds)
            _idle_seconds = 0
            }
        }

    // Seconds to count up inactivity
    let _IDLE_CHECK_INTERVAL = 0

    // Seconds since no activity has been tracked
    let _idle_seconds = 0

    // Timer function that tracks activity
    function _activity_checker() {
        _idle_seconds = _idle_seconds + _IDLE_CHECK_INTERVAL
        }

    })();
