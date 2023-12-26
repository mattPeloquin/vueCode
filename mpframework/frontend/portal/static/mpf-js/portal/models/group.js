/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal group models

    Used for portal layout
*/
(function() { 'use strict';

    mpp.Group = mpp.Content.extend({

        defaults: function() {
            return _.extend( mpp.Content.prototype.defaults.call( this ), {
                // Type is not passed from server
                'type_db': 'portalgroup',
                // Values empty if not sent
                'script_name': '',
                'nav_template': '',
                'item_template': '',
                'html': '',
                })
            },
        })

    mpp.Groups = mpp.ContentBag.extend({
        _bag_type: "Groups",
        model: mpp.Group,
        // Only access through portal bootstrap
        url: '',
        })

    })();
