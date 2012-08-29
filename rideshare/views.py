from hashlib import sha256
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.forms import ValidationError
from django.template import RequestContext
from django.contrib.gis.geos import Polygon
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404

from rideshare import forms, models as db
from occupywallst import api, utils, models as maindb


def my_cache(mkkey, seconds=60):
    def _my_cache(function):
        @wraps(function)
        def __my_cache(request, *args, **kwargs):
            if request.user.is_authenticated():
                response = function(request, *args, **kwargs)
            else:
                key = sha256(mkkey(request, *args, **kwargs) + ':' +
                             request.LANGUAGE_CODE).hexdigest()
                response = cache.get(key)
                if not response:
                    response = function(request, *args, **kwargs)
                    cache.set(key, response, seconds)
            return response
        return __my_cache
    return _my_cache


@my_cache(lambda r: 'rides')
def rides(request):
    rides = db.Ride.objects.all()
    user_ride_request = None
    user_ride = None
    if request.user.is_authenticated():
        try:
            user_ride = rides.get(user=request.user)
        except db.Ride.DoesNotExist:
            try:
                user_ride_request = \
                    db.RideRequest.objects.get(user=request.user)
            except db.RideRequest.DoesNotExist:
                pass
    return render_to_response('rides.html', {
        'rides': rides,
        'user_ride': user_ride,
        'user_ride_request': user_ride_request,
    }, context_instance=RequestContext(request))


@login_required
def ride_request_view(request, request_id):
    ride_request = db.RideRequest.objects.get(pk=int(request_id))
    return render_to_response('request_view.html', {
        "ride_request": ride_request,
        "ride": ride_request.ride,
    }, context_instance=RequestContext(request))


@login_required
def ride_delete(request, ride_id):
    ride = db.Ride.objects.select_related('requests').get(
        user=request.user, pk=int(ride_id))
    requests = ride.requests.all()
    for req in requests:
        maindb.Notification.send(
            req.user, reverse('rides'),
            '%s has deleted there ride' % (ride.user.username))
    requests.delete()
    ride.delete()
    return HttpResponseRedirect(reverse(rides))


@login_required
def ride_create(request):
    return ride_create_or_update(request)


@login_required
def ride_edit(request, ride_id):
    ride = get_object_or_404(db.Ride, pk=int(ride_id))
    return ride_create_or_update(request, ride)


@login_required
def ride_create_or_update(request, instance=None):
    if request.method == "POST":
        form = forms.RideForm(request.POST, instance=instance)
        if form.is_valid():
            ride = form.save(commit=False)
            try:
                # this should maybe go into some work queue instead of
                # being run sync
                ride.user = request.user
                ride.retrieve_route_from_google()
                #ride.full_clean()
                ride.save()
                return HttpResponseRedirect(ride.get_absolute_url())
            except ValidationError:
                 #stupid hack
                from django.forms.util import ErrorList
                form._errors["title"] = ErrorList([
                    "You have already created a ride with that title",
                ])
        else:
            ride_requests = None
    else:
        userinfo = maindb.UserInfo.objects.get(user=request.user)
        if hasattr(settings, 'DEFAULT_END_ADDRESS'):
            default_end_address = settings.DEFAULT_END_ADDRESS
        else:
            default_end_address = None
        form = forms.RideForm(initial={
            'start_address': userinfo.formatted_address,
            'end_address': default_end_address,
        }, instance=instance)
        ride_requests = db.RideRequest.objects.filter(ride=instance)
    return render_to_response('ride_update.html', {
        "form": form,
        "ride": instance,
        "requests": ride_requests,
    }, context_instance=RequestContext(request))


def ride_info(request, ride_id):
    ride = db.Ride.objects.get(pk=int(ride_id))
    CHOICES = [(i, i) for i in range(1, ride.seats_avail + 1)]
    ride_request = None
    requests = None
    form = None
    try:
        if request.user == ride.user:
            #get all the ride requests
            requests = db.RideRequest.objects.filter(ride=ride)
        else:
            #get one
            ride_request = db.RideRequest.objects.get(user=request.user)
            form = forms.RideRequestForm(instance=ride_request)
            form.fields['seats_wanted'].widget.choices = CHOICES
    except db.RideRequest.DoesNotExist:
        #creat a ride request
        form = forms.RideRequestForm()
        form.fields['seats_wanted'].widget.choices = CHOICES
    return render_to_response('ride_info.html', {
        "ride": ride,
        "ride_request": ride_request,
        "requests": requests,
        "form": form,
    }, context_instance=RequestContext(request))


@login_required
def ride_request_add_update(request, ride_id):
    ride = get_object_or_404(db.Ride, pk=int(ride_id))
    try:
        ride_request = db.RideRequest.objects.get(user=request.user, ride=ride)
    except db.RideRequest.DoesNotExist:
        ride_request = db.RideRequest(user=request.user, ride_id=ride_id)
    if request.method == 'POST':
        form = forms.RideRequestForm(request.POST, instance=ride_request)
        form.save()
        msg = "Ride Request From %s -- %s" % (
            ride_request.user.username, request.POST['info'])
        api.message_send(request.user, ride.user, msg)
        msg = '%s has request a seat on your ride' % (
            ride_request.user.username)
        url = ride_request.ride.get_absolute_url()
        maindb.Notification.send(ride.user, url, msg)
    if request.is_ajax():
        return HttpResponse("{test:tes}", mimetype="application/json")
    else:
        return HttpResponseRedirect(ride.get_absolute_url())


@login_required
def ride_request_delete(request, ride_id):
    ride_request = db.RideRequest.objects.get(
        ride__pk=ride_id, user__id=request.user.id)
    if request.user == ride_request.user:
        ride_request.delete()
        msg = '%s has canceled their ride request' % (
            ride_request.user.username)
        url = ride_request.ride.get_absolute_url()
        maindb.Notification.send(ride_request.ride.user, url, msg)
    return HttpResponseRedirect(reverse(rides))


def _str_to_bbox(val):
    swlat, swlng, nwlat, nwlng = [float(s) for s in val.split(',')]
    return Polygon.from_bbox([swlng, swlat, nwlng, nwlat])


def rides_get(bounds=None, **kwargs):
    """Find all rides within visible map area"""
    if bounds:
        bbox = _str_to_bbox(bounds)
        qset = (db.Ride.objects
                .filter(route__isnull=False,
                        route__bboverlaps=bbox))
    else:
        qset = (db.Ride.objects
                .filter(route__isnull=False))
    for ride in qset:
        yield {'id': ride.id,
               'title': ride.title,
               'address': ride.waypoint_list[0],
               'route': ride.route}

def ride_request_update(request_id, status, user=None, **kwargs):
    ride_request = (db.RideRequest.objects
                    .select_related("ride", "ride__user")
                    .filter(id=request_id))
    try:
        req = ride_request[0]
    except IndexError:
        raise utils.APIException(_("request not found"))
    if req.ride.user == user:
        req.status = status
        req.save()
        # msg = '%s %s your ride request' % (req.ride.user.username, status)
        # message_send(req.ride.user, req.user, msg)
        maindb.Notification.send(
            req.user, req.ride.get_absolute_url(),
            '%s %s your ride request' % (req.ride.user.username, status))
        return [{"id": req.id, "status": req.status}]
    else:
        raise utils.APIException(_("insufficient permissions"))
