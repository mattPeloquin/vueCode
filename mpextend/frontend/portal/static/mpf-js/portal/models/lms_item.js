/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    LmsItem specializations
*/
(function() { 'use strict';

    mpp.LmsItem = mpp.Item.extend({
        })

    mpp.model_types( 'lmsitem', mpp.LmsItem )

   _.extend( mpp.LmsItem.prototype, {

        initialize: function() {
            mpp.Item.prototype.initialize.apply( this, arguments )

            // Events for integrating with the mpLMS wrapper
            this.on( 'lms_started', this.lms_started, this )
                .on( 'lms_passed', this.lms_passed, this )
                .on( 'lms_commit', this.lms_commit, this )
            },

        set_initial_status: function() {
            // Override initial status to be start instead of complete
            this._set_initial_status( ['C','S'], 'S' )
            },

        // Store events and send to server via throttled update
        lms_started: function() {
            mp.layout_resize()
            this.user_started()
            },
        lms_passed: function() {
            // FUTURE - decide whether to do anything besides complete with LMS Passed
            this.set( 'status', 'C' )
            this.update()
            },
        lms_commit: function() {
            this.update()
            },
        })

    })();
