from django.test import TestCase
from django.test.client import Client

from django.core.urlresolvers import reverse
from models import *

def assert_success(response):
    assert response.status_code == 200, \
        'request should be successful (found "%d")' % response.status_code

class OWS(TestCase):
    fixtures = ['occupywallst/fixtures/verbiage.json']

    def create_users(self):
        """ Create users for functional testing of access control.

        It seems easier to create the users with a code block than as
        json fixtures, because the password is clearer before it is
        encrypted.
        """
        from django.contrib.auth.models import User
        user = User.objects.create_user('red', '', 'red')
        user = User.objects.create_user('green', '', 'green')
        user = User.objects.create_user('blue', '', 'blue')

    def setUp(self):
        self.create_users()

    # unit tests
    def test_verbiage(self):
        """ Test verbiage model"""
        
        assert Verbiage.get('title') != None, 'should have a title'
        assert Verbiage.get('title') != None, 'should cache title for second request'
        assert Verbiage.get('title', 'en') != None, 'should translate title'

        assert Verbiage.get('header') != None, 'should have a header'
        assert Verbiage.get('footer') != None, 'should have a footer'

        assert Verbiage.get('scripts') != None, 'should have jscript'




    # functional tests
    def test_index(self):
        c = Client()
        url = reverse('occupywallst.views.index')
        response = c.get(url)
        assert_success(response)

        # repeat request, to test caching code
        response = c.get(url)
        assert_success(response)
