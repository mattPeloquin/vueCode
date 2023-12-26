{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Setup cacheable values for scriptiing

{%endcomment%}

{#-- These are only for UI behavior - NOT FOR SECURITY #}
mp.is_portal = {{ is_portal | jsbool }}
mp.is_portal_content = {{ is_portal_content | jsbool }}
mp.is_page_admin = {{ is_page_admin | jsbool }}
mp.is_popup = {{ is_popup | jsbool }}
mp.is_popup_close = {{ is_popup_close | jsbool }}
mp.user.is_authenticated = {{ user.is_authenticated | jsbool }}
mp.user.is_ready = {{ user.is_ready | jsbool }}
mp.user.has_test_access = {{ user.has_test_access | jsbool }}

mp.nav_deeplinker = '{{ url_deeplinker }}'

{#-- No separation of access_staff_view needed on client #}
mp.user.access_staff = {{ user.access_staff_view | jsbool }}
{% if user.access_staff_view %}
    mpurl.admin = '{% url 'staff_admin:index' %}'
{% endif %}

{#-- Avoid use of HTTP that can get hung up in some firewalls #}
mp.compatibility_on = {{ user.compatibility_on | jsbool }}

{#-- SPECIFIC site/theme sb_options are checked in client #}
mp.sb_options.site = {{ sb_options.site | json }}
mp.sb_options.portal = {{ sb_options.portal | json }}
mp.sb_options.text = {{ sb_options.text | json }}

mp.access_free_all = {{ access_free_all | jsbool }}
{% if is_portal %}
    mpp.access_free_items = {{ access_free_items | json }}
{% endif %}
