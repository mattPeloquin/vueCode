/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Customization and additions for ProxyApp display
*/
(function() { 'use strict';

    mpp.app_fixup = function( parent ) {
    /*
        Setup an embedded ProxyApp iframe on load
    */
        mp.run_when_ready(
            function() { return !!$( parent ).find("#mp_proxyapp")[0] },
            function app_ready() {
                try {
                    const app = $( parent ).find("#mp_proxyapp")[0]
                    mp.log_info("Fixing up proxy app: ", app)
                    $( app )
                        .on( 'load', function( event ) {
                            mp.log_info("APP LOADED: ", event)
                            mp.layout_resize()
                            })
                    }
                catch( e ) {
                    mp.log_error("Exception fixing up app", e)
                    }
                })
        }

    })();
