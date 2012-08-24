from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, LineString
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from occupywallst import geo
from rideshare import settings


class Ride(models.Model):
    """Info about a person or bus driving to Event for carpooling"""
    RIDETYPE_CHOICES = (
        ('car', 'Car'),
        ('bus', 'Bus'),
        ('other', 'Other'),
    )
    #this is defined twice, other in RideRequest
    RIDEDIR_CHOICES = (
        ('round', 'Round Trip'),
        ('to', 'One Way too'),
        ('from', 'One Way from'),
    )

    ride_direction = models.CharField(
        max_length=32, choices=RIDEDIR_CHOICES, default="round", help_text="""
        What direction are you going?""")
    user = models.ForeignKey(User, editable=False, help_text="""
        User who is driving to event.""")
    published = models.DateTimeField(
        auto_now_add=True, blank=True, help_text="""
        When was ride posted on the site?""")
    ridetype = models.CharField(
        'Ride Type', max_length=32, choices=RIDETYPE_CHOICES,
        default='car', help_text="""
        What type of vehicle is being offered?""")
    title = models.CharField(max_length=255, help_text="""
        A one-line title to describe ride.""")
    if hasattr(settings, 'DEFUALT_DEPART_DATE'):
        default_depart_time = settings.DEFUALT_DEPART_DATE
    else:
        default_depart_time = None

    depart_time = models.DateTimeField(default=default_depart_time, help_text="""
       What time are you leaving?""")

    if hasattr(settings, 'DEFUALT_RETURN_DATE'):
        default_return_time = settings.DEFUALT_DEPART_DATE
    else:
        default_return_time = None
    return_time = models.DateTimeField(default=default_return_time, help_text="""
        What time are you coming back?""")
    seats_total = models.IntegerField(default=0, help_text="""
        How many seats in vehicle does the user wish to fill?""")
    waypoints = models.TextField(help_text="""
        List of addresses intersected by driving route separated by newlines.
        Must contain at least two lines for origin and destination.  This may
        be updated to include people who will be picked up.""")
    waypoints_points = models.LineStringField(
        null=True, default=None, help_text="""
        the points to the address of the waypoints""")
    route = models.LineStringField(null=True, default=None, help_text="""
        The driving route coords Google gave us from waypoints.""")
    route_data = models.TextField(blank=True, help_text="""
        Google's goofy compressed version of route coords.""")
    info = models.TextField(blank=True, help_text="""
        A little bit about yourself, the ride, and what to expect""")
    #forum_post = models.ForeignKey(ForumPost, null=True, blank=True)
    is_deleted = models.BooleanField(
        default=False, editable=False, help_text="""
        Flag to indicate should no longer be listed on site.""")
    objects = models.GeoManager()

    class Meta:
        unique_together = ("user", "title")

    def __unicode__(self):
        if self.ridetype == 'other':
            return "%s's ride" % (self.user)
        else:
            return "%s's %s ride" % (self.user, self.ridetype)

    @property
    def pending_requests(self):
        return self.requests.filter(status="pending")

    @property
    def accepted_requests(self):
        return self.requests.filter(status="accepted")

    def forum_title(self):
        waypoints = self.waypoint_list
        return "%s to %s on %s" % (
            waypoints[0], waypoints[-1], self.depart_time.date())

    def retrieve_route_from_google(self):
        route = geo.directions(self.waypoint_list)
        points = []
        for waypoint in route:
            flip_me = waypoint['overview_polyline']['points']
            points += [(x, y) for y, x in flip_me]
        self.route = LineString(points)

    @property
    def waypoint_list(self):
        return [s.strip() for s in self.waypoints.split('\n') if s.strip()]

    @property
    def seats_avail(self):
        accepted_requests = self.accepted_requests
        total = 0
        for item in accepted_requests:
            total = item.seats_wanted + total
        return self.seats_total - total

    @models.permalink
    def get_absolute_url(self):
        return ('rideshare.views.ride_info', [self.id])


class RideRequest(models.Model):
    """List of pending/accepted/denied Ride requests

    This table if for requests sent *to* a user offering a ride.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    RIDEDIR_CHOICES = (
        ('round', 'Round Trip'),
        ('to', 'One Way too'),
        ('from', 'One Way from'),
    )

    ride = models.ForeignKey(
        Ride, editable=False, related_name="requests", help_text="""
        The ride the user wants to get in on.""")
    user = models.ForeignKey(User, help_text="""
        The user who needs a ride to the event.""")
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default="pending", help_text="""
        Current acceptance status of request.""")
    ride_direction = models.CharField(
        max_length=32, choices=RIDEDIR_CHOICES, default="round", help_text="""
        What direction are you going?""")
    info = models.TextField(blank=True, help_text="""
        User explains why they think they deserve a ride.""")
    is_deleted = models.BooleanField(
        default=False, editable=False, help_text="""
        Flag to indicate should no longer be listed on site.""")
    seats_wanted = models.IntegerField(default=1, help_text="""
        how many seats the person is going to take up""")
    rendezvous = models.PointField(null=True, blank=True, help_text="""
        Aproximate coordinates of where they live to display on the
        attendees map.""")
    rendezvous_address = models.TextField(blank=True, help_text="""
        the address given by reverse geocoding the rendezvous point""")

    objects = models.GeoManager()

    @property
    def accepted(self):
        return (self.status == "accepted")

    @property
    def declined(self):
        return (self.status == "declined")

    class Meta:
        unique_together = ("ride", "user")

    def __unicode__(self):
        return "%s wants seat in %s" % (self.user, self.ride)

    #this is also defined twice
    rendezvous_lat = property(
        lambda s: s.rendezvous.y if s.rendezvous else None)
    rendezvous_lng = property(
        lambda s: s.rendezvous.x if s.rendezvous else None)
    rendezvous_latlng = property(
        lambda s: (s.rendezvous.y, s.rendezvous.x) if s.rendezvous else None,
        lambda s, v: setattr(s, 'rendezvous', Point(v[1], v[0])))

    @classmethod
    def fetch(cls, ride, user):
        if not ride or not user:
            return None
        try:
            return cls.objects.get(ride=ride, user=user)
        except ObjectDoesNotExist:
            return None
