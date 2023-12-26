/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Video item specializations
*/
(function() { 'use strict';

    mpp.Video = mpp.Item.extend({
        })

    mpp.model_types( 'video', mpp.Video )

    _.extend( mpp.Video.prototype, {

        set_initial_status: function() {
            // Override initial status to be start instead of complete
            this._set_initial_status( ['C','S'], 'S' )
            },

        access_direct: function( access, iframe ) {
        /*
            Support reusing the iframe video element
        */
            const iwin = iframe.contentWindow
            if( iwin.mpv && iwin.mpv.update_video ) {
                iwin.mpv.update_video( access )
                return true
                }
            },

        })

    })();
