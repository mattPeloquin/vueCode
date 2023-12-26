/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Javascript logging support

*/
(function() { 'use strict';

    // Custom timer for compatibility - define and start default early
    mp.timers = {}
    mp.timer_set = function( mark ) {
        mp.timers[ mark ] = new Date().getTime()
        }
    mp.timer_set('START')
    mp.timer_delta = function( mark ) {
        mark = mark || 'START'
        return new Date().getTime() - mp.timers[ mark ]
        }

    // Core Logging methods
    mp.log_info = function() {
        mp.log_info_level && _log_msg.apply( this, arguments )
        }
    mp.log_info2 = function() {
        ( mp.log_info_level > 1 || mp.log_debug_level ) &&
            _log_msg.apply( this, arguments )
        }
    mp.log_debug = function() {
        mp.log_debug_level && _log_msg.apply( this, arguments )
        }

    // Highlight methods use event formatting and add color
    function _log_highlight( color, back, size ) {
        return function() {
            const msg = _log_event.apply( this, arguments )
            _log( '%c' + msg + ' m' + mp.timer_delta(),
                    'color:' + color + '; background:' + back + '; font-size:' + size )
            }
        }
    mp.log_error = _log_highlight('yellow', 'red', '10pt')
    mp.log_highlight = _log_highlight('yellow', '#6666DD', '9pt')
    mp.log_highlight2 = _log_highlight('blue', '#DDDDDD', '9pt')

    // Make it easy to time specific blocks
    mp.log_time_start = function( time_mark ) {
        mp.timer_set( time_mark )
        mp.log_highlight2( time_mark + ' start' )
        }
    mp.log_time_mark = function( time_mark ) {
        mp.log_highlight2( time_mark + ' ' + mp.timer_delta( time_mark ) )
        }

    // Phone home to server using special endpoint, usually sending log events to date
    mp.log_events = []
    mp.log_phone_home = function( type, items ) {
        mp.log_highlight("SENDING: " + type + " " + mp.request_info.tag)
        try {
            items = items || encodeURIComponent( mp.log_events.join('\n| ') )
            } catch( e ) { items = "items encoding error"}
        const xhr = new XMLHttpRequest()
        xhr.open( 'POST', mp.url_bmsg, true )
        xhr.setRequestHeader( 'x-requested-with', 'XMLHttpRequest' )
        xhr.setRequestHeader( 'content-type', 'application/x-www-form-urlencoded' )
        xhr.send( 'url=' + window.location.href + '&msg_type=' + type +
                    '&items=' + items + '&request_tag=' + mp.request_info.tag )
        }

    function _log_msg() {
        // Mark all logging with timestamp, and place into phone home events
        [].push.call( arguments, ' m' + mp.timer_delta() )
        _log.apply( this, arguments )
        _log_event.apply( this, arguments )
        }

    function _log_event() {
        // Build message from passed in arguments, with some special conversions
        let msg = ''
        for( var pos=0; pos < arguments.length; pos++ ) {
            let frag = arguments[ pos ]
            if( frag && frag.stack ) {
                frag = frag.stack
                }
            msg += frag
            }
        mp.log_events.push( msg )
        return msg
        }

    // Setup console workaround for consoles not present or derived from function (IE)
    const _mpconsole = window.hasOwnProperty('console') ? window.console : console
    const _log_fn = 'log' in _mpconsole &&
                    Function.prototype.bind.call( _mpconsole.log, _mpconsole )
    function _log() {
        _log_fn && _log_fn.apply( _mpconsole, arguments )
        }

    })();
