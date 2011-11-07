r"""

    occupywallst.admin
    ~~~~~~~~~~~~~~~~~~

    Django admin gui customization.

"""

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.conf.urls.defaults import patterns
from django.core.exceptions import PermissionDenied
from django.contrib.admin import AdminSite as BaseAdminSite
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin

from occupywallst import models as db


class AdminSite(BaseAdminSite):
    def __init__(self, *args, **kwargs):
        BaseAdminSite.__init__(self, *args, **kwargs)
        self.register(db.User, UserAdmin)
        self.register(db.Group, GroupAdmin)
        self.register(db.Verbiage, VerbiageAdmin)
        self.register(db.NewsArticle, ArticleAdmin)
        self.register(db.ForumPost, ArticleAdmin)
        self.register(db.UserInfo, UserInfoAdmin)
        self.register(db.Comment, CommentAdmin)
        self.register(db.RideRequest, GeoAdmin)
        self.register(db.Ride, GeoAdmin)
        self.register(db.SpamText, admin.ModelAdmin)
        # message table intentionally excluded.  i don't want to tempt
        # myself or anyone else using the backend to read private
        # conversations.


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


class UserAdmin(BaseUserAdmin):
    def save_model(self, request, user, form, change):
        user.save()
        if db.UserInfo.objects.filter(user=user).count() == 0:
            userinfo = db.UserInfo()
            userinfo.user = user
            userinfo.save()


class ArticleTranslationInline(admin.StackedInline):
    model = db.ArticleTranslation
    extra = 1


class ArticleAdmin(GeoAdmin):
    date_hierarchy = 'published'
    list_display = ('title', 'author', 'published', 'comment_count',
                    'is_visible', 'is_deleted')
    list_filter = ('is_visible', 'is_deleted')
    search_fields = ('title', 'content', 'author__username')
    ordering = ('-published',)
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ('author',)
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


class CommentAdmin(GeoAdmin):
    date_hierarchy = 'published'
    list_display = (content_field(30), 'published', 'user', 'karma', 'ups',
                    'downs', 'is_removed', 'is_deleted')
    list_filter = ('is_removed', 'is_deleted')
    search_fields = ('content', 'user__username')
    ordering = ('-published',)

    def has_add_permission(self, request):
        return False


class UserInfoAdmin(GeoAdmin):
    list_display = ('user', 'country', 'region', 'attendance', 'need_ride')
    list_filter = ('attendance', 'need_ride', 'country', 'region')
    search_fields = ('user__username', 'user__email', 'info', 'country',
                     'region', 'city', 'address', 'zipcode')
    ordering = ('user__username',)

    def has_add_permission(self, request):
        return False
