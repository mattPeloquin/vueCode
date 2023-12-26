{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extensions portal ready script

{%endcomment%}


{#-- Check cases where select dialog is displayed immediately #}
{% if account_user.primary_account and portal_skus %}

    {#-- If coupon passed in, try to redeem it automatically in access #}
    {% if portal_coupon %}
        mp.access_coupon( '{{ portal_coupon.code }}', [
            {% for pa in portal_skus %}
                {{ pa.json | safe }},
            {% endfor %}
            ])
    {#-- If PA passed in, put focus on PA and default account #}
    {% else %}
        mp.access_dialog( [
            {% for pa in portal_skus %}
                {{ pa.json | safe }},
            {% endfor %} ],
            [ {{ account_user.primary_account.json | safe }} ]
            )
    {% endif %}
{% endif %}
