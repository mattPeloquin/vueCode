/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal plan models
*/
(function() { 'use strict';

    mpp.add_to_plan = function( plan_id, node_id ) {
    /*
        Support adding tree to plan on client with lazy creation
    */
        const plan = mpp.get_plan( plan_id )
        if( plan ) {
            plan.add( node_id )
            }
        // If a user doesn't have a plan yet, there won't be a plan
        // object on the client; so refresh to ensure sync with server.
        else {
            function finished() {
                window.location.reload()
                }
            add_node( node_id, 0, finished )
            }
        }

    mpp.Plan = Backbone.Model.extend({

        name: function() {
            return this.get('name');
            },

        /*
            Add/remove content from plans
            Client-side is coordinated with server if server op successful
            Manage cases where multiple ids could get added
        */
        add: function( node_id ) {
            const self = this
            function finished() {
                const nodes = self.get('nodes')
                nodes.indexOf( node_id ) === -1 && nodes.push( node_id )
                const vms = mpp.vm_trees().tops_plan_out().remove( node_match( node_id ) )
                vms.length && mpp.vm_trees().tops_plan_in().push( vms[0] )
                }
            add_node( node_id, self.id, finished )
            },

        remove: function( node_id ) {
            const self = this
            mp.fetch({
                url: mpurl.api_tree_plan,
                method: 'POST',
                data: {
                    action: 'REMOVE',
                    tree_id: node_id,
                    plan_id: self.id,
                    },
                finished: function() {
                    const nodes = _.filter( self.get('nodes'), function( node ) {
                        return node !== node_id
                        })
                    self.set( 'nodes', nodes )
                    const vms = mpp.vm_trees().tops_plan_in().remove( node_match( node_id ) )
                    vms.length && mpp.vm_trees().tops_plan_out().push( vms[0] )
                    }
                })
            },

        logname: function() {
            return "plan(" + this.id + ", " + this.cid + ")-" + this.get('name')
            },
        })

    mpp.Plans = mpp.ModelBag.extend({
        _bag_type: "Plan",

        model: mpp.Plan,
        url: mpurl.api_plans,

        })

    function add_node( node_id, plan_id, finished ) {
        // Shared code for adding tree to plan
        if( mp.user.is_ready ) {
            mp.fetch({
                url: mpurl.api_tree_plan,
                method: 'POST',
                data: {
                    'action': 'ADD',
                    'tree_id': node_id,
                    'plan_id': plan_id,
                    },
                finished: finished,
                })
            }
        }

    function node_match( node_id ) {
        // Factory for comparing requested collection node id in plan filters
        return function( item ) {
                return item && ( item.id == node_id )
                }
        }

    })();
