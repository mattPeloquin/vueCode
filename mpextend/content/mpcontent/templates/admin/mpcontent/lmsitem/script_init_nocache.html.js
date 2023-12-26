{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Add LMS package urls onto page

{%endcomment%}


{% if user.access_staff %}

    mpurl.api_package_metrics = '{% url 'api_package_metrics' %}';

{% endif %}
