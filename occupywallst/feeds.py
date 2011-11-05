r"""

    occupywallst.feeds
    ~~~~~~~~~~~~~~~~~~

    Tools for syndicating articles via RSS and stuff.

    Some delay is added before publishing content to allow people to
    sneak in ninja edits if necessary.  This is currently set to 15
    minutes for articles and 5 minutes for comments.

"""

from datetime import datetime, timedelta

from django.conf import settings
from django.utils.html import escape
from django.contrib.syndication.views import Feed
from django.utils.translation import ugettext_lazy as _

from occupywallst import models as db
from occupywallst.templatetags.ows import synopsis


class RSSNewsFeed(Feed):
    title = _("OccupyWallSt News")
    link = settings.OWS_CANONICAL_URL
    description = _("News and information relating to the Occupy Wall Street "
                    "movement")
    description_template = 'occupywallst/feed-article.html'
    delay = timedelta(seconds=60 * 15)

    def items(self):
        return (db.Article.objects
                .filter(is_deleted=False,
                        is_forum=False,
                        is_visible=True,
                        published__lt=datetime.now() - self.delay)
                .order_by('-published'))[:25]

    def item_title(self, article):
        return escape(article.title)

    def item_pubdate(self, article):
        return article.published

    def item_author_name(self, article):
        if article.author:
            return article.author.username
        else:
            return 'anonymous'

    def item_author_link(self, article):
        if article.author:
            return article.author.userinfo.get_absolute_url()
        else:
            return None


class RSSForumFeed(RSSNewsFeed):
    title = _("OccupyWallSt Forum")
    link = settings.OWS_CANONICAL_URL
    description = _("Public discussion posts pertaining to the Occupy Wall "
                    "Street movement")
    delay = timedelta(seconds=60 * 60 * 2)

    def items(self):
        return (db.Article.objects
                .filter(is_deleted=False,
                        is_forum=True,
                        is_visible=True,
                        published__lt=datetime.now() - self.delay)
                .order_by('-published'))[:25]


class RSSCommentFeed(Feed):
    title = "OccupyWallSt Comments"
    link = settings.OWS_CANONICAL_URL
    description = "All comments submitted to the Occupy Wall Street forum"
    description_template = 'occupywallst/feed-comment.html'
    delay = timedelta(seconds=60 * 60 * 2)

    def items(self):
        return (db.Comment.objects
                .filter(is_deleted=False, is_removed=False,
                        published__lt=datetime.now() - self.delay)
                .order_by('-published'))[:50]

    def item_title(self, comment):
        return escape(synopsis(comment.content))

    def item_pubdate(self, comment):
        return comment.published

    def item_author_name(self, comment):
        if comment.user:
            return comment.user.username
        else:
            return 'anonymous'

    def item_author_link(self, comment):
        if comment.user:
            return comment.user.userinfo.get_absolute_url()
        else:
            return None
