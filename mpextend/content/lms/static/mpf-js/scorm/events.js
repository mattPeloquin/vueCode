/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Handling of events from the embedded Scorm iframe that the
    MPF cares about, and map onto content item events

	MPF attempts to track inactivity (e.g., lesson left open in
	browser window). This is done via resetting activity on Scorm messages
	that are NOT known to occur on interval tiemrs.
*/
(function(mpl) { 'use strict';

    mpl.value_event_dispatch = function( name, value ) {
	/*
		Turn events into calls on methods in the mpl.event space
    */
        // Slice off "cmi."
        const dispatch_name = name.slice(4)
        try {
            // Call event handler, if registered
            mpl[ dispatch_name ]( value )
            }
        catch(e) {
            mp.log_debug("MPLMS SCORM IGNORE(", dispatch_name, "): ", value)
            }
        }

    // Commit event forces write back to DB
    mpl.commit = function() {

		// If client is not in idle state, send lesson data back to server
		// Scorm lessons are ususally set up to ping suspend data on a regular
		// basis, but if user leaves lesson open and hasn't been using it,
		// don't pass these messages along
		if( mp.idle() ) {
   	        mp.log_info("MPLMS Skipping SCORM commit due to inactivity")
			}
		else {
   	        mp.log_info("MPLMS SCORM COMMIT");
	        mpl.current_item.trigger('lms_commit')
			}
        }

    /*--------------------------------------------------------------
		Scorm events

	    Add functions to the mpl namespace that match the cmi.XXX set value
	    names, and they will be called on SetValue events.
    */

    mpl.success_status = function( value ) {
        if( value == 'passed' ) {
            mp.log_info("MPLMS SCORM PASSED: ", mpl.current_item.get('name'))
            mpl.current_item.trigger('lms_passed')
            }
        }

    mpl.completion_status = function( value ) {
        if( value == 'completed' ) {
            mp.log_info("MPLMS SCORM COMPLETED: ", mpl.current_item.get('name'))
            mpl.current_item.trigger('user_completed')
            }
        }

    // Capture suspend data events as progress data
    // Reset idle activity - suspend data is usually called relative to user activity
    mpl.suspend_data = function( value ) {
        mp.log_debug("MPLMS SCORM SUSPEND DATA: ", value)
        mp.idle_reset()
        mpl.current_item.trigger( 'user_progress', value )
        }

    // Reset idle and send server commit on these as it indicates the user is doing something
    mpl.location = function( value ) {
        mp.log_info("MPLMS location: ", value)
        mp.idle_reset()
        mpl.current_item.trigger( 'lms_commit', value )
        }

    // Don't do anything with these right now except log
    mpl.session_time = function( value ) {
        mp.log_info("MPLMS session_time: ", value)
        }

    })(window.mpl = window.mpl || {});
