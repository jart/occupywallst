r"""

    occupywallst.sitemaps
    ~~~~~~~~~~~~~~~~~~~~~

    Tell search engines where the content at.

"""

from datetime import datetime

from django.contrib import sitemaps

from occupywallst import models as db


class ArticleSitemap(sitemaps.Sitemap):
    changefreq = "daily"
    priority = 0.6

    def items(self):
        return (db.Article.objects
                .filter(is_deleted=False,
                        is_visible=True))

    def lastmod(self, obj):
        return datetime.now()


class UserSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.4

    def items(self):
        return (db.Article.objects
                .filter(is_deleted=False,
                        is_visible=True))

    def lastmod(self, obj):
        return datetime.now()
