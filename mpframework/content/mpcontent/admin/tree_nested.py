#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Special nested tree pages that work with one tree.

    Previously support for the default MPTT tree view that shows all
    roots and leaves in changelist was used. This view proved confusing
    and had all sorts of issues with splitting trees across pagination,
    showing partial trees from searches, etc.
    The benefit of drag-dropping a sub collection from one tree to another
    is limited, and can be done with the top-tree drop down.
"""
from django.urls import re_path
from django.urls import reverse
from django.http import HttpResponseRedirect

from mpframework.common.utils import safe_int
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin

from ..models import Tree
from .tree import TreeForm
from .tree import TreeAdminBase


class NestedTreeForm( TreeForm ):
    class Meta:
        model = Tree
        exclude = ()

        labels = dict( TreeForm.Meta.labels, **{
            'parent': "Parent",
            })
        labels_sb = dict( TreeForm.Meta.labels_sb, **{
            })
        help_texts = dict( TreeForm.Meta.help_texts, **{
            'parent': "Select the parent for this child collection.<br>"
                      "To promote this collection to the top level, select no parent.",
            })
        widgets = dict( TreeForm.Meta.widgets, **{
            })


class TreeNestedStaffAdmin( StaffAdminMixin, TreeAdminBase ):
    """
    Show nested collection hierarchy FOR A SINGLE top-level collection.
    The TreeNested admin is ONLY valid when initialized with a url
    that defines the top-level tree being displayed.
    """
    form = NestedTreeForm

    def _set_tree( self, tree_id, request ):
        """
        Helper to stash the top tree a given request's admin page is for.
        """
        tree_id = safe_int( tree_id )
        if tree_id:
            request.mpstash['admin_tree'] = Tree.objects.get( id=tree_id )
            request.mpstash['admin_tree_top'] = request.mpstash['admin_tree'].my_top

    def save_model( self, request, obj, form, change ):
        """
        Set parent for new additions and invalidate parent and root by saving
        """
        parent = request.mpstash['admin_tree']
        if not change and parent:
            obj.parent = parent
            parent.save()
        super().save_model( request, obj, form, change )

    def formfield_for_foreignkey( self, db_field, request, **kwargs ):
        """
        Override TreeAdminBase to make the parent relate to the current top tree
        """
        if db_field.name == 'parent':
            tree = request.mpstash['admin_tree']
            kwargs['queryset'] = Tree.objects.filter( mptt_id=tree.mptt_id )
            db_field.default = tree.parent_id
        return super().formfield_for_foreignkey( db_field, request, **kwargs )

    def get_queryset( self, request ):
        """
        Return only collection rows for this tree
        """
        tree = request.mpstash.get('admin_tree')
        if not tree:
            return Tree.objects.none()
        qs = super().get_queryset( request )
        qs = qs.filter( mptt_id=tree.mptt_id )
        return qs

    def get_urls( self ):
        """
        Manage the special URLs for working on the children of one tree at a time
        """
        return [
            # Redirect this to base class, which will display all
            re_path( r'^[/]?$', self.admin_site.admin_view( self.changelist_view ),
                        name='mpcontent_treenested_changelist' ),

            # These are the valid screens for working with a nested tree under top
            re_path( r'^(?P<top_id>[\w]+)[/]?$', self.admin_site.admin_view( self.changelist_top ),
                        name='mpcontent_treenested_changelist_top' ),
            re_path( r'^(?P<tree_id>[\w]+)/change[/]?$',
                        self.admin_site.admin_view( self.change_view ),
                        name='mpcontent_treenested_change' ),
            re_path( r'^(?P<top_id>[\w]+)/add[/]?$',
                        self.admin_site.admin_view( self.add_view ),
                        name='mpcontent_treenested_add' ),
            ]

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )

        if request.user.access_high:
            # Remove items not used for children
            layout = rv[ self.fs_layout ][1]['fields']
            layout.remove( ('portal__collection_no_top','portal__collection_footer') )
            layout.remove( ('portal__collection_left','portal__collection_right') )
            layout.remove( ('portal__show_progress','portal__collection_no_bgimage') )

        return rv

    # Show views for only the top tree
    def changelist_top( self, request, top_id ):
        self._set_tree( top_id, request )
        return super().changelist_view( request,
                extra_context={ 'top_tree': request.mpstash.get('admin_tree_top') })

    def add_view( self, request, top_id ):
        self._set_tree( top_id, request )
        return super().add_view( request )

    def change_view( self, request, tree_id, form_url='' ):
        self._set_tree( tree_id, request )
        return super().change_view( request, tree_id )

    # Change/add returns go back to the nested tree changelist
    def _return_root( self, request, _obj ):
        redirect = self.response_redirect( request )
        if redirect:
            return redirect
        return HttpResponseRedirect(
                reverse( 'staff_admin:mpcontent_treenested_changelist_top',
                      kwargs={ 'top_id': request.mpstash['admin_tree_top'].pk } ) )
    def response_add( self, request, obj ):
        return self._return_root( request, obj )
    def response_change( self, request, obj ):
        return self._return_root( request, obj )

class TreeNested( Tree ):
    class Meta:
        proxy = True
        verbose_name = u"Child collection"

staff_admin.register( TreeNested, TreeNestedStaffAdmin )
