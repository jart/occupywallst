r"""

    occupywallst.models
    ~~~~~~~~~~~~~~~~~~~

    Database definition.

"""

from datetime import date, timedelta

from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UserInfo(models.Model):
    """Extra DB information to associate with a Django auth user
    """
    user = models.OneToOneField(User, editable=False, help_text="""
        Reference to Django auth user.""")
    info = models.TextField(blank=True, help_text="""
        Some profile or "about me" information.""")
    need_ride = models.BooleanField(default=True, help_text="""
        Do they currently need a ride?  If so, display their position
        on the need a ride map.""")

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


class Article(models.Model):
    """A news article which gets listed on the main page.
    """
    author = models.ForeignKey(User, help_text="""
        The user who wrote this article.""")
    title = models.CharField(max_length=255, help_text="""
        A one-line title to describe ride.""")
    slug = models.SlugField(unique=True, help_text="""
        A label for this article to appear in the url.""")
    published = models.DateTimeField(help_text="""
        When was article was published?""")
    content = models.TextField(help_text="""
        The contents of the article.""")
    comment_count = models.IntegerField(default=0, editable=False,
                                        help_text="""
        Comment counter to optimize listing page.""")
    is_visible = models.BooleanField(default=True, help_text="""
        Should it show up on the main page listing?""")
    is_deleted = models.BooleanField(default=False, editable=False,
                                     help_text="""
        Flag to indicate should no longer be listed on site.""")

    objects = models.GeoManager()

    def __unicode__(self):
        return "\"%s\" by %s" % (self.title, self.author.username)

    @models.permalink
    def get_absolute_url(self):
        return ('occupywallst.views.article', [self.slug])

    def delete(self):
        self.is_deleted = True
        self.save()

    @staticmethod
    def recalculate():
        for art in Article.objects.all():
            art.comment_count = (self.comments
                                 .filter(is_deleted=False,
                                         is_removed=False)
                                 .count())
            art.save()


class Comment(models.Model):
    """Users can leave comments on articles reddit style
    """
    article = models.ForeignKey(Article, editable=False,
                                related_name="comments", help_text="""
        The article to which this comment belongs.""")
    # parent = models.ForeignKey(Comment, null=True, blank=True, editable=False,
    #                            help_text="""
    #     Is this responding to another person's comment?""")
    published = models.DateTimeField(help_text="""
        When was article was published?""")
    content = models.TextField(blank=True, help_text="""
        The contents of the message.""")
    ups = models.IntegerField(default=0, editable=False, help_text="""
        The count of upvotes received.""")
    downs = models.IntegerField(default=0, editable=False, help_text="""
        The count of downvotes received.""")
    karma = models.IntegerField(default=0, editable=False, help_text="""
        Must equal ups minus downs.""")
    is_removed = models.BooleanField(default=False, editable=False,
                                     help_text="""
        Flag to indicate a moderator removed the comment.""")
    is_deleted = models.BooleanField(default=False, editable=False,
                                     help_text="""
        Flag to indicate user deleted thier comment.""")

    objects = models.GeoManager()

    def __unicode__(self):
        return "%s commented on %s" % (self.title, self.author.username)

    def delete(self):
        self.is_deleted = True
        self.save()

    def get_absolute_url(self):
        return "%s#comment%d" % (self.article.get_absolute_url(), self.id)

    def upvote(self, user):
        assert user.is_authenticated()
        vote, c = CommentVote.objects.get_or_create(comment=self, user=user)
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
        vote, c = CommentVote.objects.get_or_create(comment=self, user=user)
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
        return "%+d for %s by %s" % (self.vote, self.comment, self.user)

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
    from_user = models.ForeignKey(User, editable=False, unique=True,
                                  related_name="messages_sent", help_text="""
        The user who sent the message.""")
    to_user = models.ForeignKey(User, editable=False, unique=True,
                                related_name="messages_recv", help_text="""
        The user who received the message.""")
    content = models.TextField(blank=True, help_text="""
        The contents of the message.""")
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
        self.is_deleted = True
        self.save()


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
