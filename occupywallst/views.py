r"""

    occupywallst.views
    ~~~~~~~~~~~~~~~~~~

    Dynamic web page functions.

"""

import logging

from django.db.models import Q
from django.contrib import auth
from django.contrib.auth import views as authviews
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect

from occupywallst.forms import SignupForm
from occupywallst import models as db


logger = logging.getLogger(__name__)


def index(request):
    articles = (db.Article.objects
                .select_related("author")
                .filter(is_visible=True, is_forum=False, is_deleted=False)
                .order_by('-published'))[:25]
    return render_to_response(
        'occupywallst/index.html', {'articles': articles},
        context_instance=RequestContext(request))


def forum(request, sort):
    articles = (db.Article.objects
                .select_related("author")
                .filter(is_visible=True, is_deleted=False)
                .order_by('-published'))
    return render_to_response(
        'occupywallst/forum.html', {'articles': articles},
        context_instance=RequestContext(request))


def chat(request):
    return render_to_response(
        'occupywallst/chat.html', {},
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


def attendees(request):
    response = render_to_response(
        'occupywallst/attendees.html', {},
        context_instance=RequestContext(request))
    return response


def rides(request):
    return render_to_response(
        'occupywallst/rides.html', {},
        context_instance=RequestContext(request))


def housing(request):
    return render_to_response(
        'occupywallst/housing.html', {},
        context_instance=RequestContext(request))


def telecom(request):
    return render_to_response(
        'occupywallst/telecom.html', {},
        context_instance=RequestContext(request))


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
            # this is so stupid!
            user = auth.authenticate(username=form.cleaned_data['username'],
                                     password=form.cleaned_data['password1'])
            assert user
            auth.login(request, user)
            return HttpResponseRedirect(user.get_absolute_url())
    else:
        form = SignupForm()
    return render_to_response(
        'occupywallst/signup.html', {'form': form},
        context_instance=RequestContext(request))
