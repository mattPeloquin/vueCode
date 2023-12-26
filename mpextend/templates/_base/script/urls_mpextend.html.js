{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extend URLs added by MPF bootstrap

{%endcomment%}

mpurl.api_pa_info = '{% url 'api_pa_info' %}'
mpurl.api_item_access = '{% url 'api_item_access' %}'
mpurl.api_user_item = '{% url 'api_user_item' %}'
mpurl.api_plans = '{% url 'api_plans' %}'
mpurl.api_tree_plan = '{% url 'api_tree_plan' %}'

mpurl.login_url_access = '{{ login_url_access }}'

mpurl.api_coupon_info = '{% url 'api_coupon_info' %}'

{% if user.is_authenticated %}
    mpurl.api_ui_state = '{% url 'api_user_ui_state' %}'
    {% if user.access_staff_view %}
        mpurl.api_update_version = '{% url 'api_update_version' %}'
        mpurl.map_tracking = '{{ static_url_resource }}/map_tracking.png'
    {% endif %}
{% endif %}

{% if is_portal %}
    mpurl.api_access_options = '{% url 'api_access_options' %}'
{% endif %}

{%comment%}
    Support login in popup for embedded iframe content
    If embedded send message to parent to open login window
    otherwise just open in place.
{%endcomment%}

mp.login = function( suffix ) {
    mp.login_action( mp.login_url(), suffix )
    }

mp.access_login = function( sku, coupon ) {
    mp.login_action( mp.access_login_url( sku ),
                coupon ? `coupon=${ coupon }` : '' )
    }

mp.login_action = function( url, suffix ) {
    suffix = suffix || ''
    if( mp.is_iframe ) {
        window.parent.postMessage({
            mp_event_login_url: `{{ site.main_host_ssl }}${ url }?_popup=1&${ suffix }`,
            }, '*' )
        }
    else {
        window.location.assign(`${ url }?${ suffix }`)
        }
    }

mp.login_url = function() {
    {% if is_portal %}
        {% if is_portal_content %}
            return mp.is_iframe ?
                '{% url 'login_popup' url_portal_kwargs.content_slug %}' :
                '{% url 'login_portal_content' url_portal_kwargs.content_slug %}'
        {% else %}
            return '{% url 'login_path' '' %}' + mp.local_nav.path
        {% endif %}
    {% else %}
        return '{% url 'login' %}'
    {% endif %}
    }

mp.access_login_url = function( sku ) {
    let url = '{% url 'login_sku' '' %}'
    {% if is_portal %}
        {% if is_portal_content %}
            url = mp.is_iframe ?
                '{% url 'login_popup_access' url_portal_kwargs.content_slug '' %}' :
                '{% url 'login_portal_content_access' url_portal_kwargs.content_slug '' %}'
        {% else %}
            url = '{% url 'login_access' '' %}'
        {% endif %}
    {% endif %}
    return url += sku
    }
