{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

	Inject user and display information that cannot be cached
    into the page for use by Javascript.

{%endcomment%}

{#-- Get/set state that may be sent from the server #}
mp.user.ui_state = {}
{% if user.ui_state %}
    mp.user.ui_state = mp.json_parse('{{ user.ui_state | safe }}')
    mp.log_info2("Loaded ui_state", mp.user.ui_state)
{% endif %}
mp.user.workflow = {{ user.workflow_filters | json }}
mp.user.extended_access = {{ user.extended_access | jsbool }}
mp.user.ga_admin = {{ ga_admin | jsbool }}
mp.user.email = '{{ user.email | default:"" }}'
mp.user.name = '{{ user.name }}'
mp.user.first = '{{ user.first_name }}'
mp.user.image = '{{ user.image_url }}'

mp.request.nav_default = '{{ request_frame.nav_default }}'
mp.request.bg_image = '{{ request_skin.background_image }}'
mp.request.nav_no_scroll = {{ nav_no_scroll | jsbool }}
{% if is_portal %}
    mp.request.default_panel = '{{ request_skin.default_panel }}'
    mp.request.default_viewer = '{{ request_skin.default_viewer }}'
    mp.request.default_nav = '{{ request_skin.default_nav }}'
    mp.request.default_node = '{{ request_skin.default_node }}'
    mp.request.default_item = '{{ request_skin.default_item }}'
{% endif %}
