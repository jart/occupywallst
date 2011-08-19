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
    url(r'^$', 'occupywallst.views.index'),
    url(r'^rss/news/$', feeds.RSSNewsFeed()),
    url(r'^rss/forum/$', feeds.RSSForumFeed()),
    url(r'^rss/comments/$', feeds.RSSCommentFeed()),
    url(r'^article/(?P<slug>[-_\d\w]+)/$', 'occupywallst.views.article'),
    url(r'^forum/$', 'occupywallst.views.forum', {'sort': 'new'}),
    url(r'^forum/(?P<slug>[-_\d\w]+)/$', 'occupywallst.views.thread'),
    url(r'^attendees/$', 'occupywallst.views.attendees'),
    url(r'^notification/(?P<id>\d+)/$', 'occupywallst.views.notification'),
    url(r'^rides/$', 'occupywallst.views.rides'),
    url(r'^calendar/$', 'occupywallst.views.calendar'),
    url(r'^chat/$', 'occupywallst.views.chat'),
    url(r'^chat/(?P<room>[a-zA-Z0-9]+)/$', 'occupywallst.views.chat'),
    url(r'^housing/$', 'occupywallst.views.housing'),
    url(r'^conference/$', 'occupywallst.views.conference'),
    url(r'^about/$', 'occupywallst.views.about'),
    url(r'^login/$', 'occupywallst.views.login'),
    url(r'^logout/$', 'occupywallst.views.logout'),
    url(r'^signup/$', 'occupywallst.views.signup'),
    url(r'^error/$', 'occupywallst.views.error'),
    url(r'^users/(?P<username>[-_\d\w]+)/$', 'occupywallst.views.user_page'),
    url(r'^users/(?P<username>[-_\d\w]+)/edit/$', 'occupywallst.views.edit_profile'),
    url(r'^api/attendees/$', utils.api_view(api.attendees)),
    url(r'^api/attendee/info/$', utils.api_view(api.attendee_info)),
    url(r'^api/thread/new/$', utils.api_view(api.thread_new)),
    url(r'^api/comment/get/$', utils.api_view(api.comment_get)),
    url(r'^api/comment/new/$', utils.api_view(api.comment_new)),
    url(r'^api/comment/edit/$', utils.api_view(api.comment_edit)),
    url(r'^api/comment/remove/$', utils.api_view(api.comment_remove)),
    url(r'^api/comment/delete/$', utils.api_view(api.comment_delete)),
    url(r'^api/comment/vote/$', utils.api_view(api.comment_vote)),
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
