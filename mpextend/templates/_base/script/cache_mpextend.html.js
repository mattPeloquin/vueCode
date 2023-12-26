{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extend cached JS

{%endcomment%}

mpp.portal_content = '{{ portal_content }}'

{% if user.access_staff %}
    {% include 'content/easylinks.html.js' %}
{% endif %}

// Load service worker for PWA
if( !mp.is_iframe && 'serviceWorker' in navigator ) {
    window.addEventListener( 'load', function() {
        navigator.serviceWorker
            .register('{% url "sandbox_service_worker" %}').then(
            function( reg ) {
                // Registration was successful
                mp.log_info("ServiceWorker Registered", reg)
                },
            function( err ) {
                // registration failed :(
                mp.log_info("ERROR - ServiceWorker registration failed: ", err)
                }
            ).catch( function( err ) {
                mp.log_info("ERROR - ServiceWorker exception: ", err)
                })
         })
    }
else {
    mp.log_debug("No service workers")
    }
