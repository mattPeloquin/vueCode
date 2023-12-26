/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Audio item specializations
*/
(function() { 'use strict';

    mpp.Audio = mpp.Item.extend({
        })

    mpp.model_types( 'audio', mpp.Audio )

    _.extend( mpp.Audio.prototype, {

        set_initial_status: function() {
            // Override initial status to be start instead of complete
            this._set_initial_status( ['C','S'], 'S' )
            },

        })

    mpp.model_types( 'audio', mpp.Audio )

    })();
