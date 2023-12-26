/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Content Item model
*/
(function() { 'use strict';

    mpp.Item = mpp.ItemBase.extend({
    /*
        Represents content items that are accessed by user.
    */

        initialize: function() {
            mpp.ItemBase.prototype.initialize.apply( this, arguments )

            // Backbone events related to consuming content
            this.on( 'user_started', this.user_started, this )
                .on( 'user_progress', this.user_progress, this )
                .on( 'user_completed', this.user_completed, this )
            },

        // User events
        user_started: function() {
            // Set starting status for newly accessed content
            this.set_initial_status()
            },
        user_progress: function( value, force ) {
            // For items that use it, set progress data for update on server
            this.set( 'progress_data', value )
            this.update( force )
            },
        user_completed: function() {
            // Completion state is set for items that can be started/finished,
            // and any progress data is reset
            this.set( 'status', 'C' )
            this.set( 'progress_data', '' )
            this.update( true )
            },

        size: function() {
            return this.get('size')
            },

        // Values won't be sent over wire if empty
        defaults: function() {
            return _.extend( mpp.ItemBase.prototype.defaults.call( this ), {
                'scope': 'I',
                'action': 'action_viewer',
                'size': 0,
                'points': 1,
                'content_rev': 1,
                })
            },
        })

    mpp.Items = mpp.ContentBag.extend({
        _bag_type: "Items",
        model: mpp.Item,
        })

    })();
