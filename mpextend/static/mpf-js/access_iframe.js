/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extensions for accessing content in an embedded iframe

*/
(function() { 'use strict';
    if( mp.is_iframe ) {

        // Listeners for messages in iframe
        window.addEventListener( 'message', function events( event ) {
            if( event.data.mp_event_iframe_init ) {
                // Initialize embedded iframe
                const classList = window.document.body.classList
                classList.add('es_access_embed')
                const data = event.data.mp_event_iframe_init
                data.access_button && classList.add('es_access_button')
                data.access_popup && classList.add('es_access_popup')
                data.access_small && classList.add('es_access_small')
                data.access_large && classList.add('es_access_large')
                }
            })

        }
    })();
