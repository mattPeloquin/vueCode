/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Scripting load / ready wait support

    There are many ways to load Javascript. Due to various historical,
    performance, and flexibility reasons, MPF uses a custom approach for
    speed in production with easy dev debugging, while keeping loading robust
    and the code as small and simple as possible.

    This includes the run_when_ready support here along with:

     - Combine files in production using django-compressor. Use manually managed
     minimized files for larger libraries.

     - Use defer synchronous loading for most scripts at end of the page. Only
     minimum script for bootstrap (like these functions) is in head.

     - Minmize execution on load, i.e., make script loading set up classes
     and functions, wait to run scripts until everything is loaded.

     - Script execution is managed with run_when_ready blocks and jQuery
     holdReady for DOM readiness.

    THIS FILE IS TEMPLATE FRAGMENT CACHED

    FUTURE - may rework JS loading with modern ES6; more likely just keep as-is
    until new web/mobile client is built.
*/
(function() { 'use strict';

    mp.run_when_ready = function( ready_check, ready_fn, options, context, args ) {
    /*
        Wait until ready_check() returns true before running ready_fn()
        Check on increasing length interval, up tp max_trys.
    */
        context = context || this

        typeof options == 'string' && (options = { 'msg': options })
        options = options || {}
        const msg = options.msg || ( ready_check.name ? ready_check.name + "-" : "" ) +
                                    ( ready_fn.ready_name || ready_fn.name || "" )
        const max_trys = options.max_trys || 16
        const growth = ( options.growth !== undefined ) ? options.growth : 32
        let interval = options.interval || 32

        let trys = 0
        function run_if_ready() {
            trys++
            try {
                if( max_trys && ( trys > max_trys ) ) {
                    mp.log_highlight2("RUN_TIMEOUT: " + trys + " " + msg )
                    return
                    }
                if( ready_check( trys ) ) {
                    if( trys > 1 || !!options.no_wait ) {
                        // Run the function!
                        return _ready_fn( ready_fn, msg + ' - trys: ' + trys,
                                            context, args )()
                        }
                    else {
                        // If first time and ready, do one empty setTimeout
                        // to put function on queue
                        interval = 0
                        }
                    }
                setTimeout( run_if_ready, interval )
                interval += ( growth * trys )
                mp.log_debug("wait: " + msg + " " + interval + ", " + trys )
                }
            catch( e ) {
                mp.log_error( "RUN_EXCEPTION: " + msg + " - ", e )
                }
            }
        run_if_ready()
        }

    mp.run_when_ready_factory = function( name, ready_check, options ) {
    /*
        Returns a function that adds ready_fns to a list and uses only one
        timer to check ready_check. The modes/options are:

            Default - All ready_fns execute when ready_check passes, in
            the order they were added to the list. The list will reset itself
            after each ready check, so can be triggered multiple times.

            no_wait: true, ready_fns execute immediately if ready_check passed
            async: n, add timeout for n ms after ready_check passed
            done: function, called after list is executed

        To create a set of tasks that execute in a gauranteed order, add a
        a check to ready_check that is true only after all items are added.
    */
        let timer_set = false
        let ready_fns = []
        options = options || {}
        options.msg = options.msg || name

        function wait_fn( ready_fn, ready_msg, context, args ) {
            const msg = name + " " + ( ready_msg || ready_fn.name )
            // Run right away if ready and no wait
            if( options.no_wait && ready_check() ) {
                _run( _ready_fn( ready_fn, msg, context, args ) )
                }
            // Otherwise place in list to run
            else {
                ready_fns.push( _ready_fn( ready_fn, msg, context, args ) )
                mp.log_debug("waitset: " + msg + " -> " + ready_fns.length )
                // If this group hadn't had timer setup, do so
                if( !timer_set ) {
                    _set_timer()
                    }
                }
            }
        function _run( fn ) {
            options.async ? setTimeout( fn, options.async ) : fn()
            }
        function _set_timer() {
            timer_set = true
            // Run all the items in the list at this point, and reset
            function run_ready_list() {
                mp.log_debug("RUNNING: " + ready_fns.length + " " + options.msg )
                ready_fns.reverse()
                while( ready_fns.length ) {
                    const fn = ready_fns.pop()
                    _run( fn )
                    }
                timer_set = false
                options.done && options.done()
                }
            run_ready_list.ready_name = name
            mp.run_when_ready( ready_check, run_ready_list, options )
            }

        return wait_fn
        }

    function _ready_fn( ready_fn, msg, context, args ) {
    /*
        Wrap executing ready function with args and shared code
    */
        return function() {
            msg && mp.log_debug("RUN: " + msg)
            try {
                ready_fn.apply( context, args )
                }
            catch( e ) {
                mp.log_error("RUN_EXCEPTION " + msg + " - ", e)
                }
            }
        }

    /*
        Setup common global wait queues
    */
    mp.when_script_loaded = mp.run_when_ready_factory( "script_loaded",
            function() {
                return !!mp._loaded_script && (
                        mp._loaded_admin === undefined || !!mp._loaded_admin )
                },
            { no_wait: true, growth: 4, max_trys: 24 })

    mp.when_ui_loaded = mp.run_when_ready_factory( "ui_loaded",
            function() {
                return !!mp._loaded_ui
                },
            { no_wait: true, growth: 8, max_trys: 24 })

    mp.when_portal_ready = mp.run_when_ready_factory( "portal_ready",
            function() {
                return !!mpp._portal_ready
                },
            { no_wait: true, growth: 16, max_trys: 24 })

    })();
