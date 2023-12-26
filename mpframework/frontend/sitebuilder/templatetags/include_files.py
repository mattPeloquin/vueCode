#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Include a set of template snippets based on file naming conventions
"""
import os
from django.template import Library
from django.template import Template
from django.template import TemplateDoesNotExist
from django.template.loader import get_template

from mpframework.common import log
from mpframework.common.deploy.platforms import all_platforms


# Load the template tag into Django's custom tag registry
register = Library()

# There's no potential UI customization for the template code, used in
# implementation, so just hard code here
_INCLUDE_FILE_TEMPLATE = Template("""
    {% for file in include_files %}
        {% include file %}
    {% endfor %}
    """)


@register.inclusion_tag( _INCLUDE_FILE_TEMPLATE, takes_context=True )
def mp_include_files( context, path, prefix, extension ):
    """
    Include set of platform files for the current sandbox context, like:

       {% mp_include_files "pathX/pathY" "fileZ" ".html" %}

    Looks for include files in all platform template locations, appending
    the platform name like:

        "pathX/pathY/fileZ_mpframework.html"

    """
    return include_files( context, path, all_platforms(), prefix, extension )

@register.inclusion_tag( _INCLUDE_FILE_TEMPLATE, takes_context=True )
def include_files( context, path, names, prefix, extension ):
    """
    Include template snippets

    Use to load a set of multiple files across the template folders
    where each file has a name like "xxx_yyy.html" where

        xxx == fixed file prefix
        yyy == suffix that changes, such as platform names

    {% include_files "template_folder" ["name1", "name2"] "prefix" ".html" %}
    Will do a get_template on:

        "template_folder/prefix_name1.html"
        "template_folder/prefix_name2.html"

    Return the entire template context, so template fragments can assume all
    variables are available.
    """
    files_to_add = []

    for name in names:
        filename = os.path.join( path, '%s_%s%s' % (prefix, name, extension) )

        log.detail3("Getting template file: %s", filename)
        try:
            get_template( filename )
            files_to_add.append( filename )
        except TemplateDoesNotExist:
            # If the template file doesn't exist, don't try to load, to
            # provide a silent fail on includes, as they are optional
            log.detail3("include_files -- Template doesn't exist: %s", filename)

    log.debug2("Including templates: %s", files_to_add)
    context.update({ 'include_files': files_to_add })

    return context
