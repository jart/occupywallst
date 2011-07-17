r"""

    occupywallst.urls
    ~~~~~~~~~~~~~~~~~

    HTTP request routing.

"""

from django.conf import settings
from django.conf.urls.defaults import patterns, url, include

from occupywallst import admin, api, utils


adminsite = admin.AdminSite(name='occupyadmin')

urlpatterns = patterns('',
    url(r'^$', 'occupywallst.views.index'),
    url(r'^article/(?P<slug>[-_\d\w]+)/', 'occupywallst.views.article'),
    url(r'^attendees/$', 'occupywallst.views.attendees'),
    url(r'^rides/$', 'occupywallst.views.rides'),
    url(r'^housing/$', 'occupywallst.views.housing'),
    url(r'^about/$', 'occupywallst.views.about'),
    url(r'^login/$', 'occupywallst.views.login'),
    url(r'^logout/$', 'occupywallst.views.logout'),
    url(r'^signup/$', 'occupywallst.views.signup'),
    url(r'^users/(?P<username>[-_\d\w]+)/$', 'occupywallst.views.user_page'),
    url(r'^api/attendees/$', utils.api_view(api.attendees)),
    url(r'^api/user/$', utils.api_view(api.user)),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^admin/', include(adminsite.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
