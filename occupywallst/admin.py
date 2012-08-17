r"""

    occupywallst.admin
    ~~~~~~~~~~~~~~~~~~

    Django admin gui customization.

"""

from django.utils.html import escape
from django.utils.http import urlquote
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.conf.urls.defaults import patterns
from django.core.exceptions import PermissionDenied
from django.contrib.admin import AdminSite as BaseAdminSite
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin
import taggit.admin
from occupywallst import models as db

class GeoAdmin(OSMGeoAdmin):
    default_lat = 39.95  # philadelphia
    default_lon = -75.16
    default_zoom = 2
    map_width = 750
    map_height = 500


def content_field(maxlen):
    def _content_field(obj):
        if not obj.content:
            return '!BLANK!'
        elif len(obj.content) < maxlen:
            return obj.content
        else:
            return obj.content[:maxlen] + "..."
    _content_field.short_description = 'Content'
    return _content_field


def verbiage_type(verbiage):
    vt = 'Page' if verbiage.name.startswith('/') else 'Fragment'
    if verbiage.use_markdown:
        return 'Markdown ' + vt
    elif verbiage.use_template:
        return 'Template ' + vt
    else:
        return 'Plain-Text ' + vt


class VerbiageTranslationInline(admin.StackedInline):
    model = db.VerbiageTranslation
    extra = 1


class VerbiageAdmin(GeoAdmin):
    inlines = (VerbiageTranslationInline,)
    ordering = ('name',)
    search_fields = ('name', 'content')
    list_display = ('name', verbiage_type, content_field(125))


class PhotoInline(admin.TabularInline):
    model = db.Photo
    extra = 1
    fields = ('original_image', 'url', 'caption')


class CarouselAdmin(admin.ModelAdmin):
    inlines = [
        PhotoInline,
    ]


class UserAdmin(BaseUserAdmin):
    def get_urls(self):
        urls = super(UserAdmin, self).get_urls()
        admin_view = self.admin_site.admin_view
        my_urls = patterns('',
            (r'^(\d+)/shadowban/$', admin_view(self.view_shadowban)),
        )
        return my_urls + urls

    def view_shadowban(self, request, id_):
        if not self.has_change_permission(request):
            raise PermissionDenied()
        id_ = int(id_)
        obj = get_object_or_404(db.User, pk=id_)
        obj.userinfo.is_shadow_banned = not obj.userinfo.is_shadow_banned
        obj.userinfo.save()
        if obj.userinfo.is_shadow_banned:
            msg = 'ShadowBanned'
        else:
            msg = 'Un-ShadowBanned'
        self.log_change(request, obj, msg)
        messages.success(request, msg)
        return HttpResponseRedirect("../../../user/%d/" % (id_))

    def save_model(self, request, user, form, change):
        user.save()
        if db.UserInfo.objects.filter(user=user).count() == 0:
            userinfo = db.UserInfo()
            userinfo.user = user
            userinfo.save()


class ArticleTranslationInline(admin.StackedInline):
    model = db.ArticleTranslation
    extra = 1


def action_invisible(modeladmin, request, queryset):
    queryset.update(is_visible=False)
action_invisible.short_description = "Make article/thread invisible"


def action_visible(modeladmin, request, queryset):
    queryset.update(is_visible=True)
action_visible.short_description = "Make article/thread visible"


def user_column(obj):
    return '<a href="/admin/auth/user/%d/">%s</a>' % (
        obj.user.id, escape(obj.user.username))
user_column.short_description = 'User'
user_column.allow_tags = True


class ArticleAdmin(GeoAdmin):
    date_hierarchy = 'published'
    list_display = ('title', user_column, 'published', 'comment_count',
                    'is_visible', 'is_deleted')
    list_filter = ('is_visible', 'is_deleted')
    search_fields = ('title', 'content', 'author__username', 'ip')
    ordering = ('-published',)
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ('author',)
    actions = (action_invisible, action_visible)
    inlines = (ArticleTranslationInline,)

    def get_urls(self):
        urls = super(ArticleAdmin, self).get_urls()
        admin_view = self.admin_site.admin_view
        my_urls = patterns('',
            (r'^(\d+)/convert/$', admin_view(self.view_convert)),
        )
        return my_urls + urls

    def view_convert(self, request, id_):
        """Convert forum posts to news article and vice versa

        This is not as simple as it sounds.
        """
        if not self.has_change_permission(request):
            raise PermissionDenied()
        id_ = int(id_)
        article = get_object_or_404(db.Article, pk=id_)
        article.is_forum = not article.is_forum
        article.save()
        model = db.ForumPost if article.is_forum else db.NewsArticle
        msg = 'Coverted to ' + model._meta.verbose_name
        url = "../../../%s/%d/" % (model._meta.module_name, id_)
        obj = get_object_or_404(model, pk=id_)
        self.log_change(request, obj, msg)
        messages.success(request, msg)
        return HttpResponseRedirect(url)


def action_remove(modeladmin, request, queryset):
    queryset.update(is_removed=True)
action_remove.short_description = "Remove comments from forum"


def action_unremove(modeladmin, request, queryset):
    queryset.update(is_removed=False)
action_unremove.short_description = "Unremove comments from forum"


def words_column(obj):
    return len(obj.content.split())
words_column.short_description = 'Words'


class CommentAdmin(GeoAdmin):
    date_hierarchy = 'published'
    list_display = (content_field(30), user_column, 'karma', words_column,
                    'published', 'is_removed', 'is_deleted')
    list_filter = ('is_removed', 'is_deleted')
    search_fields = ('content', 'user__username', 'ip')
    ordering = ('-published',)
    actions = (action_remove, action_unremove)

    def has_add_permission(self, request):
        return False


class UserInfoAdmin(GeoAdmin):
    list_display = ('user', 'is_moderator', 'country', 'region', 'attendance', 'need_ride')
    list_filter = ('attendance', 'need_ride', 'country', 'region', 'is_moderator')
    search_fields = ('user__username', 'user__email', 'info', 'country',
                     'region', 'city', 'address', 'zipcode')
    ordering = ('user__username',)

    def has_add_permission(self, request):
        return False


class ListAdmin(GeoAdmin):
    list_display = ('name', 'created')

    def get_urls(self):
        urls = super(ListAdmin, self).get_urls()
        admin_view = self.admin_site.admin_view
        my_urls = patterns('',
            (r'^(\d+)/members/$', admin_view(self.view_members)),
            (r'^(\d+)/export/$', admin_view(self.view_export)),
        )
        return my_urls + urls

    def view_export(self, request, id_):
        if not self.has_change_permission(request):
            raise PermissionDenied()
        id_ = int(id_)
        mlist = get_object_or_404(db.List, pk=id_)
        content = "\n".join(m.email for m in mlist.members.all()) + "\n"
        resp = HttpResponse(content, content_type="text/plain")
        resp['Content-Disposition'] = \
            'attachment; filename=list-%d.txt' % (mlist.id)
        return resp

    def view_members(self, request, id_):
        mlist = get_object_or_404(db.List, pk=int(id_))
        return HttpResponseRedirect(
            "../../../listmember/?mlist_name=%s" % (urlquote(mlist.name)))


class ListMemberAdmin(GeoAdmin):
    date_hierarchy = 'created'
    list_display = ('email', 'mlist', 'created', 'ip')
    list_filter = ('mlist__name',)


class PledgeAdmin(admin.ModelAdmin):
    list_filter = ['is_public', 'streets', 'meet', 'social', 'donate',
                   'strike', 'organize', 'train', 'bank', 'occupy']
    list_display = ['name', 'email', 'zipcode', 'ip', 'created'] + list_filter
    search_fields = ['name', 'email', 'zipcode', 'ip']
    ordering = ['-created']


admin.site.register(db.Carousel, CarouselAdmin)
admin.site.register(db.Verbiage, VerbiageAdmin)
admin.site.register(db.NewsArticle, ArticleAdmin)
admin.site.register(db.ForumPost, ArticleAdmin)
admin.site.register(db.UserInfo, UserInfoAdmin)
admin.site.register(db.Comment, CommentAdmin)
admin.site.register(db.SpamText, admin.ModelAdmin)
admin.site.register(db.List, ListAdmin)
admin.site.register(db.ListMember, ListMemberAdmin)
admin.site.register(db.Pledge, PledgeAdmin)

