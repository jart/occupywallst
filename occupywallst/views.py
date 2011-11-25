r"""

    occupywallst.views
    ~~~~~~~~~~~~~~~~~~

    Dynamic web page functions.

"""

import logging
from hashlib import sha256
from functools import wraps
from datetime import datetime, timedelta

from django.db.models import Q
from django.conf import settings
from django.forms import ValidationError
from django.contrib.auth import views as authviews
from django.core.cache import cache
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from occupywallst import api, forms, models as db


logger = logging.getLogger(__name__)


def error(request):
    assert False


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


@my_cache(lambda r: 'index')
def index(request):
    articles = (db.Article.objects
                .select_related("author")
                .filter(is_visible=True, is_forum=False, is_deleted=False)
                .order_by('-published'))
    return render_to_response(
        'occupywallst/index.html', {'articles': articles[:8],
                                    'archives': articles[8:]},
        context_instance=RequestContext(request))


@my_cache(lambda r: 'forum')
def forum(request):
    per_page = 25
    articles = (db.Article.objects
                .select_related("author")
                .filter(is_visible=True, is_deleted=False)
                .order_by('-killed'))
    bests = (db.Comment.objects
             .select_related("article", "user")
             .filter(is_removed=False, is_deleted=False)
             .filter(published__gt=datetime.now() - timedelta(days=1))
             .order_by('-karma'))
    recents = (db.Comment.objects
               .select_related("article", "user")
               .filter(is_removed=False, is_deleted=False)
               .order_by('-published'))
    return render_to_response(
        'occupywallst/forum.html', {'articles': articles[:per_page],
                                    'bests': bests[:7],
                                    'recents': recents[:20],
                                    'per_page': 50},
        context_instance=RequestContext(request))


def bonus(request, page):
    """Render page based on Verbiage table entry"""
    try:
        res = db.Verbiage.get('/' + page, request.LANGUAGE_CODE)
    except ObjectDoesNotExist:
        raise Http404()
    if hasattr(res, 'render'):
        res = res.render(RequestContext(request))
    return HttpResponse(res)


def _instate_hierarchy(comments):
    """Rearranges list of comments into hierarchical structure

    This adds the pseudo-field "replies" to each comment.
    """
    for com in comments:
        com.replies = []
    comhash = dict([(c.id, c) for c in comments])
    res = []
    for com in comments:
        if com.parent_id is None:
            res.append(com)
        else:
            if com.parent_id in comhash:
                comhash[com.parent_id].replies.append(com)
    return res


@my_cache(lambda r, slug, forum=False:
              ('artfrm:' if forum else 'artnwz:') + slug)
def article(request, slug, forum=False):
    try:
        article = (db.Article.objects
                   .select_related("author")
                   .get(slug=slug, is_deleted=False))
        if not forum and article.is_forum:
            raise db.Article.DoesNotExist()
    except db.Article.DoesNotExist:
        raise Http404()
    def get_comments():
        comments = article.comments_as_user(request.user)
        comments = _instate_hierarchy(comments)
        for comment in comments:
            yield comment
    recents = (db.Article.objects
               .select_related("author")
               .filter(is_visible=True, is_deleted=False)
               .order_by('-published'))
    if not forum:
        recents = recents.filter(is_forum=False)
    return render_to_response(
        "occupywallst/article.html", {'article': article,
                                      'comments': get_comments(),
                                      'recents': recents[:25],
                                      'forum': forum},
        context_instance=RequestContext(request))


def thread(request, slug):
    return article(request, slug, forum=True)


@my_cache(lambda r: 'rides')
def rides(request):
    rides = db.Ride.objects.all()
    return render_to_response(
        'occupywallst/rides.html', {"rides": rides},
        context_instance=RequestContext(request))


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
            ride.user = request.user
            try:
                # this should maybe go into some work queue instead of
                # being run sync
                ride.retrieve_route_from_google()
                ride.full_clean()
                ride.save()
                return HttpResponseRedirect(ride.get_absolute_url())
            except ValidationError:
                # stupid hack
                from django.forms.util import ErrorList
                form._errors["title"] = ErrorList([
                    "You have already created a ride with that title",
                ])
    else:
        form = forms.RideForm(instance=instance)
    return render_to_response(
        'occupywallst/ride_update.html', {"form": form,
                                          "ride": instance},
        context_instance=RequestContext(request))


def ride_info(request, ride_id):
    ride = get_object_or_404(db.Ride, pk=int(ride_id))
    ride_request = None
    requests = None
    comments = ride.forum_post.comments_as_user(request.user)
    comments = _instate_hierarchy(comments)
    if request.user.is_authenticated():
        if request.user == ride.user:
            requests = ride.requests.order_by('status').select_related("user")
        else:
            requests = None
            try:
                ride_request = ride.requests.get(
                        user=request.user, is_deleted=False)
            except db.RideRequest.DoesNotExist:
                ride_request = None
    form = forms.RideRequestForm()
    return render_to_response(
        'occupywallst/ride_info.html', {"ride": ride,
                                        "form": form,
                                        "requests": requests,
                                        "ride_request": ride_request,
                                        "comments": comments},
        context_instance=RequestContext(request))


@login_required
def ride_request_add(request, ride_id):
    ride = get_object_or_404(db.Ride, pk=int(ride_id))
    request_form = forms.RideRequestForm(request.POST)
    request_exists = db.RideRequest.objects.filter(
        user=request.user, ride=ride)
    if request_form.is_valid() and not request_exists:
        request_form.save(request.user, ride)
    return HttpResponseRedirect(ride.get_absolute_url())


@login_required
def ride_request_delete(request, ride_id):
    if request.method == "POST":
        ride = get_object_or_404(db.Ride, pk=int(ride_id))
        db.RideRequest.objects.filter(ride=ride, user=request.user).update(
                is_deleted=True)
    return HttpResponseRedirect(ride.get_absolute_url())


def user_page(request, username):
    try:
        user = (db.User.objects
                .filter(is_active=True)
                .select_related("userinfo")
                .get(username=username))
    except db.User.DoesNotExist:
        raise Http404()
    if user.userinfo.position is not None:
        nearby_users = (db.UserInfo.objects
                        .select_related("user")
                        .filter(position__isnull=False)
                        .distance(user.userinfo.position)
                        .order_by('distance'))[1:10]
    else:
        nearby_users = []
    if request.user.is_authenticated():
        messages = (db.Message.objects
                    .select_related("from_user", "from_user__userinfo",
                                    "to_user", "to_user__userinfo")
                    .filter(Q(from_user=user, to_user=request.user) |
                            Q(from_user=request.user, to_user=user))
                    .filter(is_deleted=False)
                    .order_by('-published'))
        for message in messages:
            if message.to_user == request.user and message.is_read == False:
                message.is_read = True
                message.save()
    else:
        messages = []
    return render_to_response(
        'occupywallst/user.html', {'obj': user,
                                   'messages': messages,
                                   'nearby': nearby_users},
        context_instance=RequestContext(request))


@login_required
def notification(request, id):
    try:
        notify = db.Notification.objects.get(id=id, user=request.user)
    except db.Notification.DoesNotExist:
        raise Http404()
    if not notify.is_read:
        notify.is_read = True
        notify.save()
    return HttpResponseRedirect(notify.url)


def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(request.user.get_absolute_url())
    return authviews.login(
        request, template_name="occupywallst/login.html")


def logout(request):
    return authviews.logout(
        request, template_name="occupywallst/logged_out.html")


def signup(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(request.user.get_absolute_url())
    if request.method == 'POST':
        form = forms.SignupForm(request.POST)
        if form.is_valid():
            key = 'signup_' + request.META['REMOTE_ADDR']
            if cache.get(key):
                return HttpResponse('please wait before signing up again')
            cache.set(key, True, settings.OWS_LIMIT_SIGNUP)
            form.save()
            api.login(request, form.cleaned_data.get('username'),
                      form.cleaned_data.get('password'))
            url = request.user.get_absolute_url()
            return HttpResponseRedirect(url + '?new=1')
    else:
        form = forms.SignupForm()
    return render_to_response(
        'occupywallst/signup.html', {'form': form},
        context_instance=RequestContext(request))


@login_required
def edit_profile(request, username):
    if username != request.user.username:
        url = request.user.get_absolute_url()
        return HttpResponseRedirect(url + 'edit/')
    if request.method == 'POST':
        form = forms.ProfileForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.user.get_absolute_url())
    else:
        form = forms.ProfileForm(request.user)
    return render_to_response(
        'occupywallst/edit_profile.html', {'form': form},
        context_instance=RequestContext(request))
