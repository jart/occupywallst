from django.test import TestCase
from occupywallst import models as db
from occupywallst.templatetags import ows

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
