r"""

    occupywallst.models
    ~~~~~~~~~~~~~~~~~~~

    Database definition.

    The most confusing thing here is that Google stores geographic
    coordinates as (lat, lng) but for some reason GeoDjango stores
    them as (lng, lat).  I've added some getters/setters to hopefully
    make this less confusing.

"""

import re
import socket
import logging
import functools
from hashlib import sha256
from datetime import date, timedelta

from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, LineString
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import smart_str
from django.template.defaultfilters import slugify

from imagekit.models import ImageSpec
from taggit.managers import TaggableManager

from occupywallst.utils import jsonify
from occupywallst import geo


logger = logging.getLogger(__name__)
rng = open('/dev/urandom')


def base36(amt=7):
    choices = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join([choices[ord(b) % 36] for b in rng.read(amt)])

def mangle_comments(comments, user, ip=None, article=None):
    comments = comments[:]
    for c in comments:
        c.upvoted = False
        c.downvoted = False
    if user and user.id:
        comhash = dict([(c.id, c) for c in comments])
        if article:
            blah = (CommentVote.objects
                    .filter(user=user, comment__article=article))
        else:
            blah = (CommentVote.objects
                    .filter(user=user, comment__in=comments))
        for vote in blah:
            comid = vote.comment_id
            if comid in comhash:
                if vote.vote == 1:
                    comhash[comid].upvoted = True
                elif vote.vote == -1:
                    comhash[comid].downvoted = True
    if user and user.id:
        for com in comments:
            if com.is_removed:
                if com.user == user:
                    com.is_removed = False
    if ip:
        for com in comments:
            if com.ip == ip:
                com.is_removed = False
    # if user and user.id and user.userinfo.can_moderate():
    #     for com in comments:
    #         com.is_removed = False
    return comments


def memoize(method):
    """Memoize decorator for methods taking no arguments
    """
    @functools.wraps(method)
    def _memoize(instance):
        key = method.__name__ + '__memoize'
        if not hasattr(instance, key):
            res = method(instance)
            setattr(instance, key, res)
        else:
            res = getattr(instance, key)
        return res
    return _memoize


class Carousel(models.Model):
    """Stores a collection of photos, to be displayed in order
    """
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return unicode(self.name)


class Photo(models.Model):
    """Stores a photo for a carousel
    """
    carousel = models.ForeignKey(Carousel, help_text="""
        The carousel to which this photo belongs.""")
    caption = models.TextField()
    url = models.URLField()
    original_image = models.ImageField(upload_to='photos')
    formatted_image = ImageSpec(image_field='original_image', format='JPEG')

    def get_absolute_url(self):
        if self.formatted_image:
            return self.formatted_image.url
        else:
            return ''

    def as_dict(self, moar={}):
        res = {'id': self.id,
               'caption': self.caption,
               'url': self.url,
               'image_url': self.get_absolute_url()}
        res.update(moar)
        return res


class List(models.Model):
    """Mailing lists model"""
    name = models.CharField(max_length=255, unique=True,
                            verbose_name="List Name")
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Mailing List"
        verbose_name_plural = "Mailing Lists"


class ListMember(models.Model):
    """Stores confirmed emails for a mailing list"""
    mlist = models.ForeignKey(
        List, related_name="members", verbose_name="Mailing List")
    email = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(
        max_length=255, verbose_name="IP Address", help_text="""
        Storing the IP is important so we can reverse geocode it and send
        people local-based alerts.""")

    class Meta:
        unique_together = ("mlist", "email")
        verbose_name = "Mailing List Member"
        verbose_name_plural = "Mailing List Members"

    def __unicode__(self):
        return self.email


class ListConfirm(models.Model):
    """Stores confirmation codes for mailing list to verify email"""
    mlist = models.ForeignKey(List)
    email = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=255)

    @staticmethod
    def prune(days_old=5):
        """Remove old records"""
        thresh = date.today() - timedelta(days=days_old)
        ListConfirm.objects.filter(created__lte=thresh).delete()


class Verbiage(models.Model):
    """Stores arbitrary website content fragments in Markdown

    See also: :py:func:`occupywallst.context_processors.verbiage`
    """
    name = models.CharField(max_length=255, unique=True, help_text="""
        Arbitrary name for content fragment.  If this starts with a '/'
        then it'll be mapped to that URL on the website.""")
    content = models.TextField(blank=True)
    use_markdown = models.BooleanField(default=True, help_text="""
        If checked, your content will be parsed as markdown with
        HTML allowed.""")
    use_template = models.BooleanField(default=False, help_text="""
        If checked, your content will be run through the Django
        template engine.""")

    class Meta:
        verbose_name_plural = "Verbiage"

    def clean(self):
        if self.use_template and not self.name.startswith('/'):
            raise ValidationError('template content name must start with /')
        if self.name.startswith('/') and not self.name.endswith('/'):
            raise ValidationError('names starting with / must end with /')
        if self.use_markdown and self.use_template:
            raise ValidationError("you can't use both markdown and template")

    def save(self):
        super(Verbiage, self).save()
        for language in [None] + [a for a, b in settings.LANGUAGES]:
            cache.delete(Verbiage._make_key(self.name, language))

    def get_absolute_url(self):
        if self.name.startswith('/'):
            return self.name
        else:
            return '.'

    @staticmethod
    def _make_key(name, language=None):
        key = 'verbiage_%s_%s' % (name, language)
        return sha256(smart_str(key)).hexdigest()

    @staticmethod
    def get(name, language=None):
        key = Verbiage._make_key(name, language)
        res = cache.get(key)
        if res is None:
            verb = Verbiage.objects.get(name=name)
            try:
                verb = verb.translations.get(language=language)
            except ObjectDoesNotExist:
                pass
            if verb.use_markdown:
                from occupywallst.templatetags.ows import markup_unsafe
                res = markup_unsafe(verb.content)
            elif verb.use_template:
                from django.template import Template
                res = Template(verb.content)
            else:
                res = verb.content
            cache.set(key, res)
        return res


class VerbiageTranslation(models.Model):
    verbiage = models.ForeignKey(Verbiage, related_name='translations')
    language = models.CharField(max_length=255, choices=settings.LANGUAGES)
    content = models.TextField(blank=True)
    name = property(lambda self: self.verbiage.name)
    use_markdown = property(lambda self: self.verbiage.use_markdown)
    use_template = property(lambda self: self.verbiage.use_template)

    class Meta:
        unique_together = ("verbiage", "language")

    def save(self):
        super(VerbiageTranslation, self).save()
        cache.delete(Verbiage._make_key(self.name, self.language))


class UserInfo(models.Model):
    """Extra DB information to associate with a Django auth user
    """
    ATTENDANCE_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('maybe', 'Maybe'),
    )

    user = models.OneToOneField(User, editable=False, help_text="""
        Reference to Django auth user.""")
    info = models.TextField(blank=True, help_text="""
        Some profile or "about me" information.""")
    need_ride = models.BooleanField(default=False, help_text="""
        Do they currently need a ride?  If so, display their position
        on the need a ride map.""")
    is_moderator = models.BooleanField(default=False, help_text="""
        Does user have moderation privileges?""")
    attendance = models.CharField(max_length=32, choices=ATTENDANCE_CHOICES,
                                  default="maybe", help_text="""
        Whether or not user is attending protest.""")
    notify_message = models.BooleanField(default=True, help_text="""
        Does user want an email when they message or comment response.""")
    notify_news = models.BooleanField(default=True, help_text="""
        Does user want an email new articles are published?""")
    is_shadow_banned = models.BooleanField(default=False, help_text="""
        If true, anything this user posts will be automatically removed.""")
    karma = models.IntegerField(default=0, editable=False)

    position = models.PointField(null=True, blank=True, help_text="""
        Aproximate coordinates of where they live to display on the
        attendees map.""")
    formatted_address = models.CharField(max_length=256, blank=True,
                                         help_text="""
        Full address google reverse geocode gave us on position.""")
    country = models.CharField(max_length=2, blank=True, help_text="""
        ISO country code that google reverse geocode gave us on position.""")
    region = models.CharField(max_length=128, blank=True, help_text="""
        State/region that google reverse geocode gave us on position.""")
    city = models.CharField(max_length=128, blank=True, help_text="""
        City that google reverse geocode gave us on position.""")
    address = models.CharField(max_length=256, blank=True, help_text="""
        Street address that google reverse geocode aproximated on position.""")
    zipcode = models.CharField(max_length=16, blank=True, help_text="""
        Postal code that google reverse geocode gave us on position.""")

    objects = models.GeoManager()

    class Meta:
        verbose_name = 'User Info'
        verbose_name_plural = 'User Infos'

    def __unicode__(self):
        return unicode(self.user)

    @models.permalink
    def get_absolute_url(self):
        return ('occupywallst.views.user_page', [self.user.username])

    position_lat = property(lambda s: s.position.y if s.position else None)
    position_lng = property(lambda s: s.position.x if s.position else None)
    position_latlng = property(
        lambda s: (s.position.y, s.position.x) if s.position else None,
        lambda s, v: setattr(s, 'position', Point(v[1], v[0])))

    def can_moderate(self):
        return self.user.is_staff or self.is_moderator

    def as_dict(self, moar={}):
        res = {'id': self.user.id,
               'username': self.user.username,
               'date_joined': self.user.date_joined,
               'url': self.user.get_absolute_url(),
               'info': self.info}
        res.update(moar)
        return res


class Notification(models.Model):
    """User notifications

    This table allows you to tell users in realtime when someone
    responds to their comments or sends them a private message.

    There are two types of notifications:

    1. User notifications which persist in the database until a user
       clicks the notification to mark it as read.

    2. Broadcast notifications which are published transiently to all
       people currently using the site, even if they're not logged in.

    """
    user = models.ForeignKey(User)
    published = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField()
    message = models.TextField()
    url = models.TextField()

    objects = models.GeoManager()

    def __unicode__(self):
        return unicode(self.user)

    @models.permalink
    def get_absolute_url(self):
        return ('notification', [self.id])

    def as_dict(self):
        return {'id': self.id,
                'published': self.published,
                'message': self.message,
                'is_read': self.is_read,
                'url': self.get_absolute_url()}

    @staticmethod
    def send(user, url, message):
        if not user or not user.id:
            return
        for notify in user.notification_set.filter(is_read=False):
            if notify.message == message:
                return  # don't send multiple of same notification
        notify = Notification()
        notify.user = user
        notify.message = message
        notify.url = url
        notify.save()
        Notification.publish({'type': 'ows.notification',
                              'dest': 'user.' + notify.user.username,
                              'msg': notify.as_dict()})

    @staticmethod
    def broadcast(msg, dest='all'):
        Notification.publish({'type': 'ows.broadcast',
                              'dest': dest,
                              'msg': msg})

    @staticmethod
    def publish(msg):
        data = jsonify(msg)
        addr = settings.OWS_NOTIFY_PUB_ADDR
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(data, addr)
        except Exception, e:
            logger.warning('notification publish failed: %s', e)
        finally:
            sock.close()


class Article(models.Model):
    """A news article which gets listed on the main page.

    This table is also used to store threads on the forum when
    is_forum is True.
    """
    author = models.ForeignKey(User, null=True, blank=True, help_text="""
        The user who wrote this article.""")
    title = models.CharField(max_length=255, help_text="""
        A one-line title to describe article.""")
    slug = models.SlugField(unique=True, help_text="""
        A label for this article to appear in the url.  DO NOT change
        this once the article has been published.""")
    published = models.DateTimeField(help_text="""
        When was article was published?""")
    killed = models.DateTimeField(auto_now_add=True, help_text="""
        When was the last comment made?""")
    content = models.TextField(blank=True, help_text="""
        The contents of the article in Markdown.""")
    comment_count = models.IntegerField(default=0, editable=False,
                                        help_text="""
        Comment counter to optimize listing page.""")
    allow_html = models.BooleanField(default=False, help_text="""
        Should the markdown parser allow HTML?  If a non-staff user
        posted this, they will lose the ability to edit.""")
    is_visible = models.BooleanField(default=False, help_text="""
        Should it be listed on the website and syndicated?""")
    is_forum = models.BooleanField(default=False, editable=False, help_text="""
        Indicates this a thread on the message board forum.""")
    is_deleted = models.BooleanField(default=False, help_text="""
        Flag to indicate should no longer be shown on site.""")
    ip = models.CharField(max_length=255, blank=True)

    # hacks to make method naming more compatible with other models :(
    is_removed = property(
        lambda self: not self.is_visible,
        lambda self, val: setattr(self, 'is_visible', not val))
    user = property(
        lambda self: self.author,
        lambda self, val: setattr(self, 'author', val))

    objects = models.GeoManager()
    tags = TaggableManager()

    @classmethod
    def objects_as(cls, user):
        qset = cls.objects.filter(is_deleted=False)
        if user and user.is_authenticated():
            qset = qset.filter(Q(is_visible=True) | Q(author=user))
        else:
            qset = qset.filter(is_visible=True)
        return qset

    def __unicode__(self):
        name = self.author.username if self.author else 'anonymous'
        if self.is_forum:
            return "Thread \"%s\" by %s" % (self.title, name)
        else:
            return "Article \"%s\" by %s" % (self.title, name)

    def full_text(self):
        return self.title + ' ' + self.content

    @models.permalink
    def get_absolute_url(self):
        """Returns absolute canonical path for article"""
        if self.is_forum:
            return ('forum-post', [self.slug])
        else:
            return ('article', [self.slug])

    @models.permalink
    def get_forum_url(self):
        """Returns non-canonical url to view article on forum"""
        return ('forum-post', [self.slug])

    def delete(self):
        self.author = None
        self.title = "[DELETED]"
        self.content = "[DELETED]"
        self.is_deleted = True
        self.save()

    def as_dict(self, moar={}):
        res = {'id': self.id,
               'title': self.title,
               'slug': self.slug,
               'content': self.content,
               'url': self.get_absolute_url(),
               'author': self.author.username if self.author else 'anonymous',
               'published': self.published,
               'comment_count': self.comment_count,
               'is_visible': self.is_visible,
               'is_forum': self.is_forum}
        res.update(moar)
        return res

    @staticmethod
    def recalculate():
        for art in Article.objects.all():
            art.comment_count = (art.comment_set
                                 .filter(is_deleted=False,
                                         is_removed=False)
                                 .count())
            art.save()

    def comments_as_user(self, user, ip=None):
        """Return comments with respect to a user's votes

        This fetches all comments for this article as well as all
        votes cast by user on this article.  It then adds the
        pseudo-fields ``upvoted`` and ``downvoted`` to each comment to
        let us know how the user already voted.

        This also temporarily removes the ``is_removed`` flag if user
        is the person who posted the comment.  We don't want trolls to
        know if their comments are being removed.

        The result will include deleted comments so be sure not to
        render them!
        """
        comments = (Comment.objects
                    .select_related("article", "user", "user__userinfo")
                    .filter(article=self)
                    .order_by('-karma', '-published'))[:]
        return mangle_comments(comments, user, ip=ip, article=self)

    def translate(self, lang):
        """Mangles title and content with translated text if available

        Destroys save method so you can't shoot yourself in the foot.
        """
        if getattr(self, '__translated', False):
            return
        self.save = None
        try:
            trans = ArticleTranslation.objects.get(article=self, language=lang)
        except ObjectDoesNotExist:
            pass
        else:
            self.content = trans.content
            self.title = trans.title
        self.__translated = True

    @property
    def taggies(self):
        if not hasattr(self, "_taggies"):
            self._taggies = self.tags.all()[:]
        return self._taggies


class ArticleTranslation(models.Model):
    article = models.ForeignKey(Article)
    language = models.CharField(max_length=255, choices=settings.LANGUAGES)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)

    class Meta:
        unique_together = ("article", "language")


class NewsArticleManager(models.GeoManager):
    def get_query_set(self):
        qset = super(NewsArticleManager, self).get_query_set()
        return qset.filter(is_forum=False)


class NewsArticle(Article):
    """View of Article table that doesn't show forum posts"""
    objects = NewsArticleManager()

    class Meta:
        proxy = True
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"

    def save(self, *args, **kwargs):
        self.is_forum = False
        return super(NewsArticle, self).save(*args, **kwargs)


class ForumPostManager(models.GeoManager):
    def get_query_set(self):
        qset = super(ForumPostManager, self).get_query_set()
        return qset.filter(is_forum=True)


class ForumPost(Article):
    """View of Article table that doesn't news articles"""
    objects = ForumPostManager()

    class Meta:
        proxy = True
        verbose_name = "Forum Post"
        verbose_name_plural = "Forum Posts"

    def save(self, *args, **kwargs):
        self.is_forum = True
        return super(ForumPost, self).save(*args, **kwargs)


class Comment(models.Model):
    """Users can leave comments on articles reddit style"""
    article = models.ForeignKey(Article, editable=False, help_text="""
        The article to which this comment belongs.""")
    user = models.ForeignKey(User, null=True, blank=True, editable=False,
                             help_text="""
        Who posted this comment?""")
    published = models.DateTimeField(auto_now_add=True, help_text="""
        When was article was published?""")
    parent_id = models.IntegerField(null=True, blank=True, editable=False)
    content = models.TextField(blank=True, help_text="""
        The contents of the message.""")
    ups = models.IntegerField(default=0, help_text="""
        The count of upvotes received.""")
    downs = models.IntegerField(default=0, help_text="""
        The count of downvotes received.""")
    karma = models.IntegerField(default=0, help_text="""
        Must equal ups minus downs.""")
    is_removed = models.BooleanField(default=False, help_text="""
        Flag to indicate a moderator removed the comment.""")
    is_deleted = models.BooleanField(default=False, help_text="""
        Flag to indicate user deleted thier comment.""")
    ip = models.CharField(max_length=255, blank=True)

    replies = ()

    objects = models.GeoManager()

    @classmethod
    def objects_as(cls, user):
        qset = cls.objects.filter(is_deleted=False)
        if user and user.is_authenticated():
            qset = qset.filter(Q(is_removed=False) | Q(user=user))
        else:
            qset = qset.filter(is_removed=False)
        return qset

    def __unicode__(self):
        name = self.user.username if self.user else 'anonymous'
        return "%s's comment on %s" % (name, self.article.slug)

    def full_text(self):
        return self.content

    def delete(self):
        self.user = None
        self.content = ""
        self.is_deleted = True
        self.save()

    def get_absolute_url(self):
        return "%s#comment-%d" % (self.article.get_absolute_url(), self.id)

    def get_forum_url(self):
        return "%s#comment-%d" % (self.article.get_forum_url(), self.id)

    def upvote(self, user):
        if user and user.id:
            try:
                vote = CommentVote.objects.get(comment=self, user=user)
            except ObjectDoesNotExist:
                vote = CommentVote(comment=self, user=user)
            if vote.vote == 1:
                return vote
            elif vote.vote == -1:
                self.downs -= 1
            vote.vote = 1
            vote.save()
        self.ups += 1
        self.karma = self.ups - self.downs
        self.save()

    def downvote(self, user):
        if user and user.id:
            try:
                vote = CommentVote.objects.get(comment=self, user=user)
            except ObjectDoesNotExist:
                vote = CommentVote(comment=self, user=user)
            if vote.vote == 1:
                self.ups -= 1
            elif vote.vote == -1:
                return vote
            vote.vote = -1
            vote.save()
        self.downs += 1
        self.karma = self.ups - self.downs
        self.save()

    @property
    def is_worthless(self):
        return self.karma <= settings.OWS_WORTHLESS_COMMENT_THRESHOLD

    @staticmethod
    def recalculate():
        for ct in Comment.objects.all():
            ct.ups = CommentVote.objects.filter(comment=ct, vote=1).count()
            ct.downs = CommentVote.objects.filter(comment=ct, vote=-1).count()
            ct.karma = ct.ups - ct.downs
            ct.save()

    def as_dict(self, moar={}):
        res = {'id': self.id,
               'user': self.user.username if self.user else 'anonymous',
               'published': self.published,
               'parent_id': self.parent_id,
               'content': self.content,
               'ups': self.ups,
               'downs': self.downs,
               'karma': self.karma}
        res.update(moar)
        return res


class CommentVote(models.Model):
    """Tracks up/downvotes of a comment

    If needed this table can be cleared periodically to make the
    database less slow.
    """
    comment = models.ForeignKey(Comment, editable=False, help_text="""
        The comment for which this vote was cast.""")
    user = models.ForeignKey(User, editable=False, help_text="""
        The user who cast this vote.""")
    time = models.DateTimeField(auto_now_add=True, editable=False,
                                help_text="""
        The time at which this vote was cast.""")
    vote = models.IntegerField(help_text="""
        May be: 1 for an upvote, -1 for a downvote.""")

    class Meta:
        unique_together = ("comment", "user")

    def __unicode__(self):
        return "%s voted %+d: %s" % (self.user, self.vote, self.comment)

    @classmethod
    def fetch(cls, comment, user):
        if not comment or not user:
            return None
        try:
            return cls.objects.get(comment=comment, user=user)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def prune(days_old=30):
        """Removes old records to speed up database

        This does not affect karma fields in Comment table.
        """
        cutoff = date.today() - timedelta(days=days_old)
        CommentVote.objects.filter(time__lte=cutoff).delete()

    def as_dict(self, moar={}):
        res = {'id': self.id,
               'user': self.user.username if self.user else 'anonymous',
               'time': self.time,
               'comment': self.comment.id,
               'vote': self.vote}
        res.update(moar)
        return res


class Message(models.Model):
    """One user sending a message to another"""
    from_user = models.ForeignKey(User, editable=False,
                                  related_name="messages_sent", help_text="""
        The user who sent the message.""")
    to_user = models.ForeignKey(User, editable=False,
                                related_name="messages_recv", help_text="""
        The user who received the message.""")
    published = models.DateTimeField(auto_now_add=True, help_text="""
        When was this message sent?""")
    content = models.TextField(blank=True, help_text="""
        The contents of the message.""")
    is_read = models.BooleanField(default=False, help_text="""
        Has the user seen this message yet?""")
    is_deleted = models.BooleanField(default=False, editable=False,
                                     help_text="""
        Flag to indicate should no longer be listed on site.""")

    objects = models.GeoManager()

    def __unicode__(self):
        return "message from %s to %s" % (
            self.from_user.username,
            self.to_user.username)

    def delete(self):
        self.content = ""
        self.is_deleted = True
        self.save()

    def as_dict(self, moar={}):
        res = {'id': self.id,
               'from_user': self.from_user.username,
               'to_user': self.to_user.username,
               'published': self.published}
        res.update(moar)
        return res


class SpamText(models.Model):
    """
    This table is used to automatically removed user submitted content
    containing certain spammy phrases.
    """
    text = models.TextField()
    is_regex = models.BooleanField(default=False, help_text="""
         Should text be interpreted as a perl-compatible regular
         expression?""")

    def __unicode__(self):
        return "%s%s" % (self.text, ' (regex)' if self.is_regex else '')

    def match(self, msg):
        if self.is_regex:
            expr = re.compile(self.text, re.I | re.S)
        else:
            expr = re.compile(re.escape(self.text), re.I)
        return expr.search(msg) is not None

    @staticmethod
    def is_spam(msg):
        for spamtext in SpamText.objects.all():
            if spamtext.match(msg):
                return True
        return False

class Pledge(models.Model):
    name = models.CharField(max_length=40)
    email = models.EmailField()
    zipcode = models.CharField(max_length=10, blank=True)
    ip = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)

    streets = models.BooleanField()
    meet = models.BooleanField()
    social = models.BooleanField()
    donate = models.BooleanField()
    strike = models.BooleanField()
    organize = models.BooleanField()
    train = models.BooleanField()
    bank = models.BooleanField()
    occupy = models.BooleanField()

    def clean(self):
        """Used by admin to verify input data is correct"""
        if not any([self.streets, self.meet, self.social, self.donate,
                    self.strike, self.organize, self.train, self.bank,
                    self.occupy]):
            raise ValidationError('You need to pledge at least one thing')

    def describe_pledges(self):
        res = []
        if self.donate:   res.append('donate')
        if self.occupy:   res.append('start an occupation')
        if self.organize: res.append('organize their workplace')
        if self.meet:     res.append('go to a meeting')
        if self.streets:  res.append('show up for an action')
        if self.social:   res.append('promote #occupy media')
        if self.strike:   res.append('not work during a general strike')
        if self.train:    res.append('attend a training')
        if self.bank:     res.append('join a credit union')
        if not res:
            return 'do nothing'
        elif len(res) == 1:
            return res[0]
        elif len(res) == 2:
            return ' and '.join(res)
        else:
            return '%s, and %s' % (", ".join(res[:-1]), res[-1])
