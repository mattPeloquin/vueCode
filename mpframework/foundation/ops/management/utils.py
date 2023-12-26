#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code shared across MPF Django commands
"""

from mpframework.common.utils.paths import join_paths


def template_file_render( path, context_dict ):
    """
    Returns content of template file rendered using Django template engine
    """
    from django.template import Template
    from django.template import Context

    with open( path, 'r' ) as template_file:
        template = Template( template_file.read() )
        context = Context( context_dict )
        return template.render( context )

def template_file_write( path, file_name, in_suffix, out, context_dict ):
    """
    Use Django template engine to create new file
    """
    input_name = file_name + '.' + in_suffix
    output_path = out if '.' in out else join_paths( path, file_name + '.' + out )

    file_content = template_file_render( join_paths(path, input_name), context_dict )

    with open( output_path, 'w' ) as conf_file:
        conf_file.write( file_content )

    return output_path
