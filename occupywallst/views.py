r"""

    occupywallst.views
    ~~~~~~~~~~~~~~~~~~

    Dynamic web page functions.

"""

import logging
from functools import wraps
from datetime import datetime, timedelta

from django.db.models import Q
from django.core.cache import cache
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import views as authviews
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from occupywallst import api
from occupywallst import models as db
from occupywallst.forms import ProfileForm, SignupForm


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
                key = mkkey(request, *args, **kwargs)
                response = cache.get(key)
                if not response:
                    response = function(request, *args, **kwargs)
                    cache.set(key, response, seconds)
            return response
        return __my_cache
    return _my_cache



@my_cache(lambda r: 'index')
def index(request):
    from django.core.cache import cache
    response = cache.get('_index')
    if not response:
        articles = (db.Article.objects
                    .select_related("author")
                    .filter(is_visible=True, is_forum=False, is_deleted=False)
                    .order_by('-published'))
        response = render_to_response(
            'occupywallst/index.html', {'articles': articles[:8]},
            context_instance=RequestContext(request))
        cache.set('_index', response, 5)
    return response


@my_cache(lambda r: 'forum')
def forum(request):
    articles = (db.Article.objects
                .select_related("author")
                .filter(is_visible=True, is_deleted=False)
                .order_by('-published'))
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
        'occupywallst/forum.html', {'articles': articles,
                                    'bests': bests[:5],
                                    'recents': recents[:20]},
        context_instance=RequestContext(request))


@my_cache(lambda r: 'calendar')
def calendar(request):
    return render_to_response(
        'occupywallst/calendar.html', {},
        context_instance=RequestContext(request))


@my_cache(lambda r, room="pub": 'chat:' + room)
def chat(request, room="pub"):
    return render_to_response(
        'occupywallst/chat.html', {'room': room},
        context_instance=RequestContext(request))


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


@my_cache(lambda r, slug, forum=False: ('artfrm:' if forum else 'artnwz:') + slug)
def article(request, slug, forum=False):
    try:
        article = (db.Article.objects
                   .select_related("author")
                   .get(slug=slug, is_deleted=False))
        if not forum and article.is_forum:
            raise db.Article.DoesNotExist()
    except db.Article.DoesNotExist:
        raise Http404()
    comments = article.comments_as_user(request.user)
    comments = _instate_hierarchy(comments)
    recents = (db.Article.objects
               .select_related("author")
               .filter(is_visible=True, is_deleted=False)
               .order_by('-published'))
    if not forum:
        recents = recents.filter(is_forum=False)
    return render_to_response(
        "occupywallst/article.html", {'article': article,
                                      'comments': comments,
                                      'recents': recents[:25],
                                      'forum': forum},
        context_instance=RequestContext(request))


def thread(request, slug):
    return article(request, slug, forum=True)


@my_cache(lambda r: 'attendees')
def attendees(request):
    response = render_to_response(
        'occupywallst/attendees.html', {},
        context_instance=RequestContext(request))
    return response


@my_cache(lambda r: 'rides')
def rides(request):
    return render_to_response(
        'occupywallst/rides.html', {},
        context_instance=RequestContext(request))


@my_cache(lambda r: 'housing')
def housing(request):
    return render_to_response(
        'occupywallst/housing.html', {},
        context_instance=RequestContext(request))


@my_cache(lambda r: 'conference')
def conference(request):
    return render_to_response(
        'occupywallst/conference.html', {},
        context_instance=RequestContext(request))


@my_cache(lambda r: 'about')
def about(request):
    return render_to_response(
        'occupywallst/about.html', {},
        context_instance=RequestContext(request))


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
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            api.login(request, form.cleaned_data.get('username'),
                      form.cleaned_data.get('password'))
            url = request.user.get_absolute_url()
            return HttpResponseRedirect(url + '?new=1')
    else:
        form = SignupForm()
    return render_to_response(
        'occupywallst/signup.html', {'form': form},
        context_instance=RequestContext(request))


@login_required
def edit_profile(request, username):
    if username != request.user.username:
        url = request.user.get_absolute_url()
        return HttpResponseRedirect(url + 'edit/')
    if request.method == 'POST':
        form = ProfileForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.user.get_absolute_url())
    else:
        form = ProfileForm(request.user)
    return render_to_response(
        'occupywallst/edit_profile.html', {'form': form},
        context_instance=RequestContext(request))
