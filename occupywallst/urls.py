r"""

    occupywallst.urls
    ~~~~~~~~~~~~~~~~~

    HTTP request routing.

"""

from django.conf import settings
from django.conf.urls.defaults import patterns, url, include

from occupywallst import admin, api, utils, feeds


adminsite = admin.AdminSite(name='occupyadmin')

urlpatterns = patterns('',
    url(r'^$', 'occupywallst.views.index', name='index'),
    url(r'^rss/news/$', feeds.RSSNewsFeed(), name='rss-news'),
    url(r'^rss/forum/$', feeds.RSSForumFeed(), name='rss-forum'),
    url(r'^rss/comments/$', feeds.RSSCommentFeed(), name='rss-comments'),
    url(r'^article/(?P<slug>[-_\d\w]+)/$', 'occupywallst.views.article', name='article'),
    url(r'^forum/$', 'occupywallst.views.forum', {'sort': 'new'}, name='forum'),
    url(r'^forum/(?P<slug>[-_\d\w]+)/$', 'occupywallst.views.thread', name='forum-post'),
    url(r'^attendees/$', 'occupywallst.views.attendees', name='attendees'),
    url(r'^notification/(?P<id>\d+)/$', 'occupywallst.views.notification', name='notification'),
    url(r'^rides/$', 'occupywallst.views.rides', name='rides'),
    url(r'^calendar/$', 'occupywallst.views.calendar', name='calendar'),
    url(r'^chat/$', 'occupywallst.views.chat', name='chat'),
    url(r'^chat/(?P<room>[a-zA-Z0-9]+)/$', 'occupywallst.views.chat', name='chat-private'),
    url(r'^housing/$', 'occupywallst.views.housing', name='housing'),
    url(r'^conference/$', 'occupywallst.views.conference', name='conference'),
    url(r'^about/$', 'occupywallst.views.about', name='about'),
    url(r'^login/$', 'occupywallst.views.login', name='login'),
    url(r'^logout/$', 'occupywallst.views.logout', name='logout'),
    url(r'^signup/$', 'occupywallst.views.signup', name='signup'),
    url(r'^error/$', 'occupywallst.views.error', name='error'),
    url(r'^users/(?P<username>[-_\d\w]+)/$', 'occupywallst.views.user_page', name='user'),
    url(r'^users/(?P<username>[-_\d\w]+)/edit/$', 'occupywallst.views.edit_profile', name='user-edit'),
    url(r'^api/attendees/$', utils.api_view(api.attendees)),
    url(r'^api/attendee/info/$', utils.api_view(api.attendee_info)),
    url(r'^api/thread/new/$', utils.api_view(api.thread_new)),
    url(r'^api/comment/get/$', utils.api_view(api.comment_get)),
    url(r'^api/comment/new/$', utils.api_view(api.comment_new)),
    url(r'^api/comment/edit/$', utils.api_view(api.comment_edit)),
    url(r'^api/comment/remove/$', utils.api_view(api.comment_remove)),
    url(r'^api/comment/delete/$', utils.api_view(api.comment_delete)),
    url(r'^api/comment/upvote/$', utils.api_view(api.comment_upvote)),
    url(r'^api/comment/downvote/$', utils.api_view(api.comment_downvote)),
    url(r'^api/message/send/$', utils.api_view(api.message_send)),
    url(r'^api/message/delete/$', utils.api_view(api.message_delete)),
    url(r'^api/check_username/$', utils.api_view(api.check_username)),
    url(r'^api/signup/$', utils.api_view(api.signup)),
    url(r'^api/login/$', utils.api_view(api.login)),
    url(r'^api/logout/$', utils.api_view(api.logout)),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^admin/', include(adminsite.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
