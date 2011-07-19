r"""

    occupywallst.views
    ~~~~~~~~~~~~~~~~~~

    Dynamic web page functions.

"""

import logging

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
                .filter(is_visible=True)
                .order_by('-published'))[:25]
    return render_to_response(
        'occupywallst/index.html', {'articles': articles},
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


def article(request, slug):
    try:
        article = db.Article.objects.get(slug=slug)
    except db.Article.DoesNotExist:
        raise Http404()
    recent = (db.Article.objects
              .filter(is_visible=True)
              .order_by('-published'))[:5]
    comments = article.comments_as_user(request.user)
    comments = _instate_hierarchy(comments)
    return render_to_response(
        'occupywallst/article.html', {'article': article,
                                      'comments': comments,
                                      'recent': recent},
        context_instance=RequestContext(request))


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


def about(request):
    return render_to_response(
        'occupywallst/about.html', {},
        context_instance=RequestContext(request))


def user_page(request, username):
    try:
        user = db.User.objects.get(username=username)
    except db.User.DoesNotExist:
        raise Http404()
    nearby_users = (db.UserInfo.objects
                    .distance(user.userinfo.position)
                    .order_by('distance'))[1:10]
    return render_to_response(
        'occupywallst/user.html', {'user': user,
                                   'nearby_users': nearby_users},
        context_instance=RequestContext(request))


def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(request.user.get_absolute_url())
    else:
        return authviews.login(
            request, template_name="occupywallst/login.html")


def logout(request):
    return authviews.logout(
        request, template_name="occupywallst/logged_out.html")


def signup(request):
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
