{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Cached injection for server information passed to Browser

    AUTH TEMPLATE FRAGMENT CACHED

    Do not add items that drive portal customization (e.g., pane options);
    add those to init_nocache.

{%endcomment%}


mpurl.reload_home = function() {
    window.location.replace('{% url 'site_home' %}')
    }

{% mp_include_files "_base/script" "cache" ".html.js" %}

{% mp_include_files "_base/script" "urls" ".html.js" %}
