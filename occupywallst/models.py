r"""

    occupywallst.models
    ~~~~~~~~~~~~~~~~~~~

    Database definition.

    The most confusing thing here is that Google stores geographic
    coordinates as (lat, lng) but for some reason GeoDjango stores
    them as (lng, lat).  I've added some getters/setters to hopefully
    make this less confusing.

"""

from datetime import date, timedelta

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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
    need_ride = models.BooleanField(default=True, help_text="""
        Do they currently need a ride?  If so, display their position
        on the need a ride map.""")
    attendance = models.CharField(max_length=32, choices=ATTENDANCE_CHOICES,
                                  help_text="""
        Whether or not user is attending protest.""")
    notify_message = models.BooleanField(default=True, help_text="""
        Does user want an email when they get private messages?""")
    notify_news = models.BooleanField(default=True, help_text="""
        Does user want an email new articles are published?""")

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

    def __unicode__(self):
        return unicode(self.user)

    @models.permalink
    def get_absolute_url(self):
        return ('occupywallst.views.user_page', [self.user.username])

    position_lat = property(lambda s: s.position.y)
    position_lng = property(lambda s: s.position.x)
    position_latlng = property(
        lambda s: (s.position.y, s.position.x),
        lambda s, v: setattr(s, 'position', Point(v[1], v[0])))


class Article(models.Model):
    """A news article which gets listed on the main page.

    This table is also used to store threads on the forum when
    is_forum is True.
    """
    author = models.ForeignKey(User, help_text="""
        The user who wrote this article.""")
    title = models.CharField(max_length=255, help_text="""
        A one-line title to describe ride.""")
    slug = models.SlugField(unique=True, help_text="""
        A label for this article to appear in the url.  DO NOT change
        this once the article has been published.""")
    published = models.DateTimeField(help_text="""
        When was article was published?""")
    content = models.TextField(help_text="""
        The contents of the article.  For news articles this should be
        HTML and for threads this should be safe markup.""")
    comment_count = models.IntegerField(default=0, help_text="""
        Comment counter to optimize listing page.""")
    is_visible = models.BooleanField(default=False, help_text="""
        Should it show up on the main page listing and rss feeds?
        Set this to true once you're done editing the article and
        want it published.  This does not apply if is_forum is True.""")
    is_forum = models.BooleanField(default=False, help_text="""
        Indicates this a thread on the message board forum.""")
    is_deleted = models.BooleanField(default=False, help_text="""
        Flag to indicate should no longer be listed on site.""")

    objects = models.GeoManager()

    def __unicode__(self):
        if self.is_forum:
            return "Thread \"%s\" by %s" % (self.title, self.author.username)
        else:
            return "Article \"%s\" by %s" % (self.title, self.author.username)

    @models.permalink
    def get_absolute_url(self):
        """Returns absolute canonical path for article
        """
        if self.is_forum:
            return ('occupywallst.views.thread', [self.slug])
        else:
            return ('occupywallst.views.article', [self.slug])

    @models.permalink
    def get_forum_url(self):
        """Returns path to display article with forum design

        This is important because news articles are also forum threads
        and sometimes we want to display the article with all the
        design elements of the forum.
        """
        return ('occupywallst.views.thread', [self.slug])

    def delete(self):
        self.is_deleted = True
        self.save()

    def as_dict(self, moar={}):
        res = {'id': self.id,
               'title': self.title,
               'slug': self.slug,
               'content': self.content,
               'url': self.get_absolute_url(),
               'author': self.author.username,
               'published': self.published,
               'comment_count': self.comment_count,
               'is_visible': self.is_visible,
               'is_forum': self.is_forum}
        res.update(moar)
        return res

    @staticmethod
    def recalculate():
        for art in Article.objects.all():
            art.comment_count = (art.comments_set
                                 .filter(is_deleted=False,
                                         is_removed=False)
                                 .count())
            art.save()

    def comments_as_user(self, user):
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
                    .select_related("user", "user__userinfo")
                    .filter(article=self)
                    .order_by('-karma', '-published'))[:]
        if user.is_authenticated():
            for c in comments:
                c.upvoted = False
                c.downvoted = False
            comhash = dict([(c.id, c) for c in comments])
            blah = (CommentVote.objects
                    .filter(user=user, comment__article=self))
            for vote in blah:
                comid = vote.comment_id
                if comid in comhash:
                    if vote.vote == 1:
                        comhash[comid].upvoted = True
                    elif vote.vote == -1:
                        comhash[comid].downvoted = True
        for com in comments:
            if com.is_removed and com.user == user:
                com.is_removed = False
        return comments


class Comment(models.Model):
    """Users can leave comments on articles reddit style
    """
    article = models.ForeignKey(Article, editable=False, help_text="""
        The article to which this comment belongs.""")
    user = models.ForeignKey(User, editable=False, help_text="""
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

    replies = ()

    objects = models.GeoManager()

    def __unicode__(self):
        return "%s's comment on %s" % (self.user.username, self.article.slug)

    def delete(self):
        self.content = ""
        self.is_deleted = True
        self.save()

    def get_absolute_url(self):
        return "%s#comment-%d" % (self.article.get_absolute_url(), self.id)

    def upvote(self, user):
        assert user.is_authenticated()
        try:
            vote = CommentVote.objects.get(comment=self, user=user)
        except CommentVote.DoesNotExist:
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
        return vote

    def downvote(self, user):
        assert user.is_authenticated()
        try:
            vote = CommentVote.objects.get(comment=self, user=user)
        except CommentVote.DoesNotExist:
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
        return vote

    @staticmethod
    def recalculate():
        for ct in Comment.objects.all():
            ct.ups = CommentVote.objects.filter(comment=ct, vote=1).count()
            ct.downs = CommentVote.objects.filter(comment=ct, vote=-1).count()
            ct.karma = ct.ups - ct.downs
            ct.save()

    def as_dict(self, moar={}):
        res = {'id': self.id,
               'user': self.user.username,
               'published': self.published,
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
        except cls.DoesNotExist:
            return None

    @staticmethod
    def prune(days_old=30):
        """Removes old records to speed up database

        This does not affect karma fields in Comment table.
        """
        cutoff = date.today() - timedelta(days=days_old)
        CommentVote.objects.filter(time__lte=cutoff).delete()


class Message(models.Model):
    """One user sending a message to another.
    """
    from_user = models.ForeignKey(User, editable=False,
                                  related_name="messages_sent", help_text="""
        The user who sent the message.""")
    to_user = models.ForeignKey(User, editable=False,
                                related_name="messages_recv", help_text="""
        The user who received the message.""")
    published = models.DateTimeField(auto_now_add=True, help_text="""
        When was this message sent?""")
    content = models.TextField(help_text="""
        The contents of the message.""")
    is_read = models.BooleanField(default=False, help_text="""
        Has the user seen this message yet?""")
    is_deleted = models.BooleanField(default=False, editable=False,
                                     help_text="""
        Flag to indicate should no longer be listed on site.""")

    objects = models.GeoManager()

    def __unicode__(self):
        if self.address:
            return "message from %s to %s" % (
                self.user.username, self.address)
        else:
            return "%s is attending" % (self.user.username)

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


class Ride(models.Model):
    """Info about a person or bus driving to Event for carpooling
    """
    RIDETYPE_CHOICES = (
        ('car', 'Car'),
        ('bus', 'Bus'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, editable=False, help_text="""
        User who is driving to event.""")
    published = models.DateTimeField(auto_now_add=True, help_text="""
        When was ride posted on the site?""")
    ridetype = models.CharField(max_length=32, choices=RIDETYPE_CHOICES,
                                help_text="""
        What type of vehicle is being offered?""")
    title = models.CharField(max_length=255, help_text="""
        A one-line title to describe ride.""")
    depart_time = models.DateTimeField(help_text="""
        The time user plans to start driving to event.""")
    seats_total = models.IntegerField(default=0, help_text="""
        How many seats in vehicle does the user wish to fill?  This does
        not change when ride requests are accepted.""")
    seats_avail = models.IntegerField(default=0, help_text="""
        Counter for total number of seats currently available.  This changes
        when user accepts requests for a ride from other users.""")
    waypoints = models.TextField(help_text="""
        List of addresses intersected by driving route separated by newlines.
        Must contain at least two lines for origin and destination.  This may
        be updated to include people who will be picked up.""")
    route = models.MultiPointField(null=True, default=None, help_text="""
        The driving route coords Google gave us from waypoints.""")
    route_data = models.TextField(blank=True, help_text="""
        Google's goofy compressed version of route coords.""")
    info = models.TextField(blank=True, help_text="""
        A long description written by user in markup.""")
    is_deleted = models.BooleanField(default=False, editable=False,
                                     help_text="""
        Flag to indicate should no longer be listed on site.""")

    objects = models.GeoManager()

    class Meta:
        unique_together = ("user", "title")

    def __unicode__(self):
        if self.ridetype == 'other':
            return "%s's ride" % (self.user)
        else:
            return "%s's %s ride" % (self.user, self.ridetype)

    def delete(self):
        self.is_deleted = True
        self.save()

    def clean(self):
        if len(self.waypoint_list) < 2:
            raise ValidationError('Must have at least two waypoints')

    @property
    def waypoint_list(self):
        return [s.strip() for s in self.waypoints.split('\n') if s.strip()]


class RideRequest(models.Model):
    """List of pending/accepted/denied Ride requests

    This table if for requests sent *to* a user offering a ride.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    ride = models.ForeignKey(Ride, editable=False, unique=True,
                             related_name="requests", help_text="""
        The ride the user wants to get in on.""")
    user = models.ForeignKey(User, editable=False, unique=True, help_text="""
        The user who needs a ride to the event.""")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES,
                              help_text="""
        Current acceptance status of request.""")
    info = models.TextField(blank=True, help_text="""
        User explains why they think they deserve a ride.""")
    is_deleted = models.BooleanField(default=False, editable=False,
                                     help_text="""
        Flag to indicate should no longer be listed on site.""")

    objects = models.GeoManager()

    class Meta:
        unique_together = ("ride", "user")

    def __unicode__(self):
        return "%s wants seat in %s" % (self.user, self.ride)

    def delete(self):
        self.is_deleted = True
        self.save()

    @classmethod
    def fetch(cls, ride, user):
        if not ride or not user:
            return None
        try:
            return cls.objects.get(ride=ride, user=user)
        except cls.DoesNotExist:
            return None
