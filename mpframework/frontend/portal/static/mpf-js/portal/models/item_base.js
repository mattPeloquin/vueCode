/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Shared code for item and tree models
*/
(function() { 'use strict';

    /*
        Update -- only send subset of data
        Throttle calls to server to update models using timeout
        Note it is possible timeout value isn't loaded, so have a default
    */
    function _update( item ) {
        mp.log_info("UPDATE MODEL", item.logname())
        const attrs = {
            id: item.id,
            status: item.get('status'),
            progress_data: item.get('progress_data'),
            }
        Backbone.Model.prototype.save.call( item, attrs, { patch: true } )
        }
    const _timeout = mp.options.timeout_ping
    const _update_fast = _.throttle( _update, 1000 )
    const _update_normal = _.throttle( _update, _timeout * 1000, 
                                        { leading: false, trailing: true } )

    mpp.ItemBase = mpp.Content.extend({
    /*
        Base model for items and trees
    */
        initialize: function() {
            const self = this
            mpp.Content.prototype.initialize.apply( self, arguments )

            _.extend( self._filter_groups, {
                'upcoming': self.upcoming,
                'previous': function() {
                    return this.get('available') && !this.upcoming()
                    },
                'no_date': function() {
                    return !this.get('available')
                    },
                })
            },

        set_initial_status: function() {
        /*
            For basic items, once access granted, set to accessed
            This should be overridden for content that has start/completion
            semantics like videos and lms.
        */
            this._set_initial_status( ['C','A'], 'A' )
            },
        _set_initial_status: function( valid_status, status ) {
            if( valid_status.indexOf( this.get('status') ) < 0 ) {
                this.set( 'status', status )
                }
            },

       upcoming: function() {
            return this.get('available') > Date.now()
            },

        update: function( force ) {
        /*
            Send status updates on this model back to server
        */
            if( mp.user.is_ready ) {
                force ? _update_fast( this ) : _update_normal( this )
                }
            },

        // Values won't be sent over wire if empty
        defaults: function() {
            return _.extend( mpp.Content.prototype.defaults.call( this ), {
                // Values empty if not sent from server
                'portal_type_id': '',
                'portal_group_id': '',
                'portal_categories': [],
                'item_template': '',
                'progress_data': '',
                // Values set during user data bootstrap
                'status': '',
                'portal_type': '',
                'portal_group': '',
                'html1': '',
                'html2': '',
                'html3': '',
                })
            },
        _lazy_attrs: [ 'html1', 'html2', 'html3' ],

        _dynamic_defaults: function() {
            mpp.Content.prototype._dynamic_defaults.apply( this )
            // Helper to set names from items pass by id
            if( this.get('portal_type_id') ) {
                const type = mpp.models.types.get( this.get('portal_type_id') )
                type && this.set( 'portal_type', type.get('name') )
                }
            if( this.get('portal_group_id') ) {
                const group = mpp.models.groups.get( this.get('portal_group_id') )
                group && this.set( 'portal_group', group.get('name') )
                }
            },
        })

    })();
