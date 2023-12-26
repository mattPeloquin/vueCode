/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Item ViewModel extensions
*/
(function() { 'use strict';

    const _ItemVMs_init = mpp.ItemVMs.init
    mpp.ItemVMs.init = function( self, models ) {
        _ItemVMs_init( self, models )

        // Status groupings
        self.accessor_ko( 'in_progress', function() {
                return self.vm_attr({ status: ['S'] })
                })
        self.accessor_ko( 'remaining', function() {
                return self.vm_attr({ status: [''] })
                })
        self.accessor_ko( 'completed', function() {
                return self.vm_attr({ status: ['C','A'] })
                })

        }

    const _user_access_action = mpp.ItemVM.prototype.user_access_action
    _.extend( mpp.ItemVM.prototype, {

        render_nav: function( element ) {
        /*
            Support item templates that use nav elements
            (i.e., their display is a nav address)
        */
            return this.sb_option( 'portal.render_nav', element ) ||
                this.RENDER_NAV_TEMPLATES.includes(
                        this.sb( 'item_template', element ) )
            },
        // HACK - Support default item nav panel templates
        RENDER_NAV_TEMPLATES: [
            'item_panel',
            ],

        user_access_action: function( node ) {
            if( !_user_access_action.call( this, node ) ) {
                return
                }

            // Add current tree node at this point to plan if available
            const current_node = mpp.vm_current.node().model
            current_node && current_node.plan_add &&
                current_node.plan_add( mpp.plan_default )

            // Send message to enclosing window about action
            if( mp.is_iframe ) {
                window.parent.postMessage({
                    mp_event_user_access: {
                        node: node && node.slug,
                        name: this.name,
                        slug: this.slug,
                        }
                    }, '*' )
                }

            },

        })

    })();
