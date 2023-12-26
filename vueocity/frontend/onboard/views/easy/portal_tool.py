#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal tool - Portal UI permutations what-if exploration

    NOTE - the querystring links used to implement different portal combos
    ARE NOT CACHED, creation is NOT optimized, and THEY ARE NOT STICKY.
    This is intended for design experimentation and prototyping,
    NOT production hosting.
"""
import random
from django.conf import settings
from django.urls import reverse
from django.http import Http404
from django.utils.http import urlencode
from django.template.defaultfilters import slugify

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.ip_throttle import boost_ip
from mpframework.common.view import staff_required
from mpframework.common.cache import cache_rv
from mpframework.common.cache.template import template_no_page_cache
from mpframework.frontend.sitebuilder.models import Frame
from mpframework.frontend.sitebuilder.models import Theme
from mpframework.frontend.sitebuilder.models import TemplateCustom
from mpframework.frontend.sitebuilder.utils import get_themes
from mpframework.frontend.sitebuilder.utils import get_frames
from mpframework.frontend.portal.views import sandbox_portal
from mpextend.common.request_info import is_threat


_MODS = {
    'theme': lambda req, val: _get_theme( req, val ),
    'frame': lambda req, val: _get_frame( req, val ),
    # These options assume names are in RequestSkin and
    # in ThemeMixin with an _ prefix
    'style': lambda req, val: _get_template( req, val, 'B' ),
    'font': lambda req, val: _get_template( req, val, 'A' ),
    'color': lambda req, val: _get_template( req, val, 'C' ),
    'color2': lambda req, val: _get_template( req, val, 'C' ),
    'mixin': lambda req, val: _get_template( req, val, 'D' ),
    'mixin2': lambda req, val: _get_template( req, val, 'D' ),
    'mixin3': lambda req, val: _get_template( req, val, 'D' ),
    'default_panel': lambda req, val: _get_template( req, val, 'Q' ),
    'default_viewer': lambda req, val: _get_template( req, val, 'F' ),
    'default_nav': lambda req, val: _get_template( req, val, 'N' ),
    'default_node': lambda req, val: _get_template( req, val, 'R' ),
    'default_item': lambda req, val: _get_template( req, val, 'I' ),
    }


def easy_portal_random( request, option=None ):
    """
    Provide a random combo of UI options, building up from no theme.
    """
    boost_ip( request.ip )
    if request.sandbox.options['portal.no_random']:
        log.info2("SUSPECT - portal random disabled: %s -> %s",
                request.sandbox.subdomain, request.mpipname)
        raise Http404
    if is_threat( request.ip ):
        log.info2("SUSPECT - portal random threat IP: %s", request.mpipname)
        raise Http404

    mods = _random_mods( request )
    mix_match = True
    if option:
        mods = { option: mods.get( option ) }
        mix_match = False
    return easy_portal( request, mods=mods, mix_match=mix_match )

def easy_portal_next_theme( request, current_theme=None ):
    """
    Reset portal to first theme (per ID order) or next theme
    """
    themes = get_themes( request )
    mod = { 'theme': themes[0].name }
    found = False
    for theme in themes:
        if found:
            mod['theme'] = theme.name
            break
        if current_theme in [ str(theme.pk), slugify(theme.name) ]:
            found = True
    return easy_portal( request, mods=mod, mix_match=False )

@staff_required
def easy_portal_all( request, portal_url=None ):
    return easy_portal( request, portal_url=portal_url, all_options=True )

@template_no_page_cache
def easy_portal( request, portal_url=None, mods=None,
            mix_match=True, all_options=False ):
    """
    Manage querystring links for showing variations of a portal,
    which are displayed by modifying the request skin.

    To support stacking the different dimensions into query string links
    that can be easily cut/pasted from the UI, keep track of current
    modifications and pass back to the template to build out the string.
    """
    mix_match = request.GET.get( 'mix_match', mix_match )
    all_options = all_options and request.user.access_high
    # Apply modifications which are active
    # also reset any stashed values THIS REQUEST's instance has
    mods = request.GET if mods is None else mods
    mods, mod_models = _get_mods( request, mods )
    request.skin.clear()
    request.skin.set_mods( mod_models )

    # Create current query strings for all combinations
    # First do all current settings and defaults, then for each type of item
    # This makes it easy to setup the template with links that stack previous
    # changes while allowing override in the links of each type
    current_opts = {
        'all': _get_mod_qs( mods, '' ),
        'defaults': _get_mod_qs({ mod: None for mod in _MODS }),
        }
    for m in _MODS:
        current_opts[ m ] = _get_mod_qs( mods, m )

    # Get names for each current template selection, whether default or mod
    current_names = {}
    for m in _MODS:
        if m in [ 'theme', 'frame' ]:
            item = getattr( request.skin, m, None )
        else:
            item = request.skin.theme_accessor( m )
        name = item.name if item else ''
        current_names[ m ] = mods.get( m, name )

    # Override url_portal to keep portal tool up through nav/refreshes
    url_portal = reverse( 'easy_portal_all' if all_options else 'easy_portal' )

    log.debug("EASY portal current names: %s", current_names)
    log.debug2("EASY portal current options: %s", current_opts)
    context = {
        'no_robots': True,
        'url_portal': url_portal,
        'sb_portal': url_portal,
        'portal_tool': not bool( request.GET.get('hide_tool') ),
        'nav_no_scroll': True,
        'pt_mix_match': mix_match,
        'pt_current_opts': current_opts,
        'pt_current_names': current_names,
        'pt_current_qs': urlencode( current_names ),
        'pt_mod_names': mods,
        'pt_fonts': _fonts( request ),
        'pt_styles': _styles( request ),
        'pt_colors': _colors( request ),
        'pt_mixins': _mixins( request ),
        'pt_panels': _panels( request ),
        'pt_viewers': _viewers( request ),
        'pt_navs': _navs( request ),
        'pt_nodes': _nodes( request ),
        'pt_items': _items( request ),
        'pt_all_options': all_options,
        }
    return sandbox_portal( request, portal_url=portal_url, context=context )

@staff_required
def easy_portal_theme_save( request ):
    """
    Save current settings as existing or new theme depending on whether
    non-system theme of same name exists.
    Use current site theme or selected one for copy.
    """
    name = request.POST['theme_name']
    change_sandbox = request.POST.get( 'site', False )
    options = _options( request, {
        'name': name,
        'provider_optional': request.sandbox.provider,
        })
    # Copy/Create the new theme with options
    theme = options.pop('theme')
    if theme:
        if theme.is_system:
            change_sandbox = True
        if theme.is_system or theme.name != name:
            theme = theme.clone( **options )
        else:
            theme.update( **options )
    else:
        theme = Theme( **options )
    theme.save()
    if change_sandbox:
        request.sandbox.theme = theme
        request.sandbox.save()
    return easy_portal( request, mods={} )

@staff_required
def easy_portal_site_save( request ):
    """
    Save current settings for the site.
    Don't overwrite sandbox theme with empty; the only way to force a
    sandbox to system defaults is in the admin
    """
    options = _options( request, {} )
    if options.get( 'theme', False ) is None:
        options.pop('theme')
    request.sandbox.update( **options )
    request.sandbox.save()
    return easy_portal( request, mods={} )

def _fonts( request ): return _get_templates( request, 'A' )
def _styles( request ): return _get_templates( request, 'B' )
def _colors( request ): return _get_templates( request, 'C' )
def _mixins( request ): return _get_templates( request, 'D' )
def _panels( request ): return _get_templates( request, 'Q' )
def _viewers( request ): return _get_templates( request, 'F' )
def _navs( request ): return _get_templates( request, 'N' )
def _nodes( request ): return _get_templates( request, 'R' )
def _items( request ): return _get_templates( request, 'I' )

def _get_theme( request, name ):
    return Theme.objects.lookup_from_list( get_themes( request ), name )
def _get_frame( request, name ):
    return Frame.objects.lookup_from_list( get_frames( request, 'P' ), name )

@cache_rv( cache='template', keyfn=lambda r, tt:(
            '{}{}'.format( tt, r.user.staff_level ), r.sandbox.cache_group ) )
def _get_templates( request, template_type ):
    """
    Get templates based on staff level, or special case visitor
    with high staff level for demonstration.
    """
    staff_level = request.user.staff_level or mc.STAFF_LEVEL_HIGH
    return TemplateCustom.objects.template_list(
                request.sandbox, [ template_type ],
                TemplateCustom.has_access_Q( staff_level ),
                )
def _get_template( request, name, ttype ):
    return TemplateCustom.objects.lookup_from_list(
            _get_templates( request, ttype ), name )

def _random_mods( request ):
    return {
        'theme': '',
        'frame': random.choice( get_frames( request, 'P' ) ).name,
        'default_nav': random.choice( _navs( request ) ).name,
        'default_item': random.choice( _items( request ) ).name,
        'font': random.choice( _fonts( request ) ).name,
        'style': random.choice( _styles( request ) ).name,
        'color': random.choice( _colors( request ) ).name,
        'mixin': random.choice( _mixins( request ) ).name,
        }

def _options( request, options ):
    """
    Setup options for updating Themes or sites
    """
    _mods, mod_models = _get_mods( request, request.GET )
    # Theme can either be forced empty for random, or follows current
    options['theme'] = mod_models.pop( 'theme', request.skin.theme )
    # Translate the frame if present
    frame = mod_models.pop( 'frame', False )
    if frame is not False:
        options['frame_site'] = frame
    # The remaining options can just be transferred with _ prefix
    for key, model in mod_models.items():
        options[ '_' + key ] = model
    return options

def _get_mods( request, mod_dict ):
    """
    For each UI request modification in the query string, find the
    model it refers to and return both query string and models.
    """
    mods = {}
    mod_models = {}
    for mod_name, mod_get in _MODS.items():
        mod_value = mod_dict.get( mod_name, False )
        if mod_value is False:
            continue
        # Stash the current query string for this value to create built-up
        # qs lists that include multiple mods
        mods[ mod_name ] = mod_value
        try:
            # Use the _MODS accessor to get the model
            mod_models[ mod_name ] = mod_get( request, mod_value )
        except Exception as e:
            if settings.DEBUG:
                raise
            log.warning("SUSPECT - Portal %s: %s, %s -> %s",
                            mod_name, request.mpipname, mod_value, e)
    log.debug("Custom mods: %s -> %s, %s", request.mpipname, mods, mod_models)
    return mods, mod_models

def _get_mod_qs( mods, mod_name=None ):
    """
    Create query string fragment that contains the current state of the query
    string for every item EXCEPT the current one
    """
    queries = {}
    for mod, value in mods.items():
        if value and ( mod_name is None or mod != mod_name ):
            queries[ mod ] = value
    return urlencode( queries )
