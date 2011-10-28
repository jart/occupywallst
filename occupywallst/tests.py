from django.test import TestCase
from django.test.client import Client

from django.core.urlresolvers import reverse
from models import *
from occupywallst import models as db
from occupywallst.templatetags import ows

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

    def test_verbiage_translation(self):
        v = Verbiage(name='test', content='hello, world')
        v.save()

        vt = VerbiageTranslation(verbiage=v, language='piglatin',
                                 content='ello-hay, orld-way')
        vt.save()

        assert 'ello-hay' in Verbiage.get('test', 'piglatin')


    # functional tests
    def test_index(self):
        c = Client()
        url = reverse('occupywallst.views.index')
        response = c.get(url)
        assert_success(response)

        # repeat request, to test caching code
        response = c.get(url)
        assert_success(response)

class UrlTest(TestCase):
    fixtures = ['example_data', 'verbiage']

    def test_articles(self):
        for article in db.Article.objects.all():
            response = self.client.get(article.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, ows.markup(article.content))

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_forum(self):
        response = self.client.get('/forum/')
        self.assertEquals(response.status_code, 200)

    def test_rss_news(self):
        response = self.client.get('/rss/news/')
        self.assertEquals(response.status_code, 200)

    def test_rss_forum(self):
        response = self.client.get('/rss/forum/')
        self.assertEquals(response.status_code, 200)

    def test_rss_comments(self):
        response = self.client.get('/rss/comments/')
        self.assertEquals(response.status_code, 200)

    def test_forum(self):
        response = self.client.get('/forum/')
        self.assertEquals(response.status_code, 200)

    def test_attendees(self):
        response = self.client.get('/attendees/')
        self.assertEquals(response.status_code, 200)

    def test_rides(self):
        response = self.client.get('/rides/')
        self.assertEquals(response.status_code, 200)

    def test_calendar(self):
        response = self.client.get('/calendar/')
        self.assertEquals(response.status_code, 200)

    def test_donate(self):
        response = self.client.get('/donate/')
        self.assertEquals(response.status_code, 200)

    def test_about(self):
        response = self.client.get('/about/')
        self.assertEquals(response.status_code, 200)

    def test_login(self):
        response = self.client.get('/login/')
        self.assertEquals(response.status_code, 200)

    def test_logout(self):
        response = self.client.get('/logout/')
        self.assertEquals(response.status_code, 200)

    def test_signup(self):
        response = self.client.get('/signup/')
        self.assertEquals(response.status_code, 200)

    def test_user_pages(self):
        for user in db.UserInfo.objects.all():
            response = self.client.get(user.get_absolute_url())
            self.assertEquals(response.status_code, 200)
