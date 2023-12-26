/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

   Portal Type models

    Used for lookup, filtering, and some portal structure.
*/
(function() { 'use strict';

    mpp.Type = mpp.Content.extend({

        defaults: function() {
            return _.extend( mpp.Content.prototype.defaults.call( this ), {
                // Type is not passed from server
                'type_db': 'portaltype',
                })
            },
        })

    mpp.Types = mpp.ContentBag.extend({
        _bag_type: "Types",
        model: mpp.Type,
        // Only access through portal bootstrap
        url: '',
        })

    })();
