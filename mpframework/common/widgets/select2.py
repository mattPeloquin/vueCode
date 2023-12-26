#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for API/Model Select2 controls
"""
from django.forms.widgets import Widget


class mpSelect2( Widget ):
    """
    The widget just puts an empty select in template, assumes
    all setup is through Select2
    """
    input_type = 'select'
    template_name = 'admin/widgets/select2.html'
