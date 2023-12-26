/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    PortalItem extensions
*/
(function() { 'use strict';

    mpp.PortalItem = mpp.Item.extend({
        })

    mpp.model_types( 'portalitem', mpp.PortalItem )

    _.extend( mpp.PortalItem.prototype, {

        defaults: function() {
            const defaults = mpp.Item.prototype.defaults()
            return _.extend( defaults, {
                // No default state for portal items
                'status': 'no_state',
                // Make aliases for HTML fields mapped over text fields
                'html1': defaults.text3,
                'html2': defaults.text4,
                })
            },

        content_action: function() {
            // Do nothing when content is accessed
            },

        })

    })();
