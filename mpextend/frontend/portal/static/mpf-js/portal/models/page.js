/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Page item specializations
*/
(function() { 'use strict';

    mpp.Page = mpp.Item.extend({
        })

    mpp.model_types( 'protectedpage', mpp.Page )

    _.extend( mpp.Page.prototype, {

        defaults: function() {
            return _.extend( mpp.Item.prototype.defaults(), {
                'allow_print': '',
                })
            },

        })

    })();
