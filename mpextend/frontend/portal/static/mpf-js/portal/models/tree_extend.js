/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extend content trees with plan support
*/
(function() { 'use strict';

    const _Tree_initialize = mpp.Tree.prototype.initialize
    _.extend( mpp.Tree.prototype, {

        initialize: function() {
            const self = this
            _Tree_initialize.apply( self, arguments )

            _.extend( self._filter_groups, {
                'plan_in': self.in_plan,
                'plan_out': function() { return !this.in_plan() },
                })
            },

        /*
            Synchronize add/remove with the server
            Strategy is to assume good sync with server and success
        */
        in_plan: function( plan_id ) {
            // Is root in a given plan? (uses active plans by default)
            const plan = mpp.get_plan( plan_id )
            const plan_tree_ids = plan ? plan.get('nodes') : []
            return _.intersection( [ this.my_root() ], plan_tree_ids ).length > 0
            },
        plan_add: function( plan_id ) {
            if( !this.in_plan( plan_id ) ) {
                mpp.add_to_plan( plan_id, this.my_root() )
                }
            },
        plan_remove: function( plan_id ) {
            if( this.in_plan( plan_id ) ) {
                const plan = mpp.get_plan( plan_id )
                plan && plan.remove( this.my_root() )
                }
            },

        })

    })();
