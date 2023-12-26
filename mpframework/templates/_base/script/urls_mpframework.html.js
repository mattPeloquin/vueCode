{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Urls added via MPF bootstrap mechanism

{%endcomment%}

mpurl.nav_root = '{{ url_portal }}'

mpurl.public = '{{ url_public }}'
mpurl.api_content_full = '{% url 'api_content_full' %}'
mpurl.api_country_options = '{% url 'api_country_options' %}'

{#-- Media urls can change based on compatibility settings #}
mpurl.media_url = '{{ media_url }}'
mpurl.content_media_url = '{{ content_media_url }}'
mpurl.user_media_url = '{{ user.media_url }}'
mpurl.compat_url = function( url ) {
    {% if user.use_compat_urls %}
        return url && url.replace( '{{ static_url_orig }}', '{{ static_url_new }}' )
    {% else %}
        return url
    {% endif %}
    }

{% if user.access_staff_view %}

    mpurl.api_autolookup = '{% url 'api_autolookup_model' %}'
    mpurl.api_item_add = '{% url 'api_item_add' %}'

{% endif %}
