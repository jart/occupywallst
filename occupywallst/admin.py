r"""

    occupywallst.admin
    ~~~~~~~~~~~~~~~~~~

    Django admin gui customization.

"""

from django.utils.html import escape
from django.utils.text import truncate_words
from django.contrib.admin import AdminSite as BaseAdminSite
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin

from occupywallst import models as db


class AdminSite(BaseAdminSite):
    def __init__(self, *args, **kwargs):
        BaseAdminSite.__init__(self, *args, **kwargs)
        self.register(db.User, UserAdmin)
        self.register(db.Group, GroupAdmin)
        self.register(db.NewsArticle, ArticleAdmin)
        self.register(db.ForumPost, ArticleAdmin)
        self.register(db.UserInfo, UserInfoAdmin)
        self.register(db.Comment, CommentAdmin)
        self.register(db.RideRequest, GeoAdmin)
        self.register(db.Ride, GeoAdmin)
        # message table intentionally excluded.  i don't want to tempt
        # myself or anyone else using the backend to read private
        # conversations.


class GeoAdmin(OSMGeoAdmin):
    default_lat = 39.95  # philadelphia
    default_lon = -75.16
    default_zoom = 2
    map_width = 750
    map_height = 500


class UserAdmin(BaseUserAdmin):
    def save_model(self, request, user, form, change):
        user.save()
        if not user.userinfo:
            userinfo = db.UserInfo()
            userinfo.user = user
            userinfo.save()


class ArticleAdmin(GeoAdmin):
    date_hierarchy = 'published'
    list_display = ('title', 'author', 'published', 'comment_count',
                    'is_visible', 'is_deleted')
    list_filter = ('is_visible', 'is_deleted')
    search_fields = ('title', 'content', 'author__username')
    ordering = ('-published',)


def comment_content(comment):
    return truncate_words(comment.content, 7) or '!BLANK!'
comment_content.short_description = 'Content'


class CommentAdmin(GeoAdmin):
    date_hierarchy = 'published'
    list_display = (comment_content, 'published', 'user', 'karma', 'ups',
                    'downs', 'is_removed', 'is_deleted')
    list_filter = ('is_removed', 'is_deleted')
    search_fields = ('content', 'author__username')
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
