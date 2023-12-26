/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Category Models

    Although Categories are loaded like items, they are
    used to organize/filter items and can participate in
    the portal layout for some portal templates.
*/
(function() { 'use strict';

    mpp.Category = mpp.Content.extend({

        defaults: function() {
            return _.extend( mpp.Content.prototype.defaults.call( this ), {
                // Category type is not passed from server
                'type_db': 'category',
                })
            },
        })

    mpp.Categories = mpp.ContentBag.extend({
        _bag_type: "Categories",
        model: mpp.Category,
        // Only access through portal bootstrap
        url: '',
        })

    })();
