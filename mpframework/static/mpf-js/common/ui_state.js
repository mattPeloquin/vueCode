/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Per-user UI state
*/
(function() { 'use strict';

    /*-------------------------------------------------------------------
        On ping timeout intervals, send information back to server
        about the state of the ui client

        This is only for active users, but to keep code as simple as
        possible, only consider that right before sending to server.

        Force is usually used for a refresh
    */

    mp.ui_state_send = function( force_time, force_send ) {
        if( force_time ) {
            _force_send && _force_send( force_send )
            }
        else {
            _normal_send && _normal_send( force_send )
            }
        }

    mp.ui_state_init = function() {
        // Called once at initialization
        // Options are available now, so setup debounce functions
        _force_send = _.throttle( _send_state_to_server, 1000 )
        _normal_send = _.throttle( _send_state_to_server, mp.options.timeout_ping * 1000 )
        }
    let _force_send = false
    let _normal_send = false

    // Take snapshot of state to only send if changed
    let _previous_state = null

    function _send_state_to_server( force_send ) {
        if( !mp.user.is_ready ) return

        // If state has changed, send to server
        const state = JSON.stringify( mp.user.ui_state )
        if( force_send || !(state == _previous_state) ) {

            mp.fetch({
                url: mpurl.api_ui_state,
                method: 'POST',
                json_data: mp.user.ui_state,
                finished: function() {
                    // If successful, note the state that was sent
                    _previous_state = state
                    },
                })
            }
        }

    })();
