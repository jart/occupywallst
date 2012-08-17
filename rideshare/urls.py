from django.conf import settings
from django.conf.urls.defaults import url, patterns, include
from django.views.decorators.http import require_GET, require_POST
from rideshare import views, admin
from occupywallst import utils

urlpatterns = patterns('rideshare',
    #rides
    url(r'^$', 'views.rides', name='rides'),
    url(r'^create/$', 'views.ride_create', name='ride_create'),
    url(r'^(?P<ride_id>\d+)/$', 'views.ride_info', name='ride_info'),
    url(r'^(?P<ride_id>\d+)/delete/$', 'views.ride_delete', name='ride_delete'),
    url(r'^(?P<ride_id>\d+)/edit/$', 'views.ride_edit', name='ride_edit'),
    #ride requests
    url(r'^(?P<request_id>\d+)/request/view/$', 'views.ride_request_view', name='ride_request_view'),
    url(r'^(?P<ride_id>\d+)/request/add/$', 'views.ride_request_add_update', name='ride_request_add_update'),
    url(r'^(?P<ride_id>\d+)/request/delete/$', 'views.ride_request_delete', name="ride_request_delete"),
    #ride ajax
    url(r'^api/safe/rides/$', require_GET(utils.api_view(views.rides_get))),
    url(r'^api/ride_request_update/$', require_POST(utils.api_view(views.ride_request_update)), name="ride_request_update"),
    #url(r'^api/ride_edit_rendezvous/$', require_POST(utils.api_view(views.ride_edit_rendezvous)), name="ride_edit_rendezvous"),  
)
