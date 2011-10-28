from django.test import TestCase
from django.test.client import Client

from django.core.urlresolvers import reverse
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
        self.red_user = User.objects.create_user('red', '', 'red')
        self.green_user = User.objects.create_user('green', '', 'green')
        self.blue_user = User.objects.create_user('blue', '', 'blue')

    def setUp(self):
        self.create_users()

        self.article = db.Article(author=self.red_user, title='article title', slug='article-slug',
                                  content='exciting article content')
        self.article.save()

    # unit tests
    def test_verbiage(self):
        """ Test verbiage model"""
        
        assert db.Verbiage.get('title') != None, 'should have a title'
        assert db.Verbiage.get('title') != None, 'should cache title for second request'
        assert db.Verbiage.get('title', 'en') != None, 'should translate title'

        assert db.Verbiage.get('header') != None, 'should have a header'
        assert db.Verbiage.get('footer') != None, 'should have a footer'

        assert db.Verbiage.get('scripts') != None, 'should have jscript'

    def test_verbiage_translation(self):
        v = db.Verbiage(name='test', content='hello, world')
        v.save()

        vt = db.VerbiageTranslation(verbiage=v, language='piglatin',
                                 content='ello-hay, orld-way')
        vt.save()

        assert 'ello-hay' in db.Verbiage.get('test', 'piglatin')

    def test_user_info_wo_geodata(self):
        ui = db.UserInfo(user=self.red_user)

        assert str(ui) != ''
        assert ui.position_lat == None
        assert ui.position_lng == None
        assert ui.position_latlng == None
        assert len(ui.as_dict().keys()) > 0

    def test_user_info_w_geodata(self):
        from django.contrib.gis.geos import Point
        ui = db.UserInfo(user=self.red_user, position=Point((20,10)))

        assert ui.position_lat == 10
        assert ui.position_lng == 20
        assert ui.position_latlng == (10,20)

    def test_notification_send(self):

        cnt = self.red_user.notification_set.count()

        db.Notification.send(self.red_user, 'http://dev.occupywallst.org', 'test message')
        assert self.red_user.notification_set.count() == cnt+1

        # send the same notification again, it should not go
        db.Notification.send(self.red_user, 'http://dev.occupywallst.org', 'test message')
        assert self.red_user.notification_set.count() == cnt+1

        # now mark it as read, send it again, and it should go
        n = self.red_user.notification_set.all()[0]
        n.is_read = True
        n.save()

        db.Notification.send(self.red_user, 'http://dev.occupywallst.org', 'test message')
        assert self.red_user.notification_set.count() == cnt+2

    def test_notification_broadcast(self):
        db.Notification.broadcast('hello everyone')
        # TODO: confirm that this had intended effect

    def test_article(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       content='this is a test')
        a.save()
        assert len(a.as_dict()) > 0

    def test_article_delete(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       content='this is a test')
        a.save()

        assert a.is_deleted == False

        a.delete()
        assert db.Article.objects.get(slug='test').is_deleted == True

    def test_article_recalculate(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       content='this is a test')
        a.save()

        # add comment
        c = db.Comment(article=a, user=self.blue_user, content='nice test')
        c.save()
                       
        db.Article.recalculate()
        # TODO: check that the comment count for the article is correct

    def test_article_comments_as_user(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       content='this is a test')
        a.save()

        # add comment as self.blue_user
        c = db.Comment(article=a, user=self.blue_user, content='nice test')
        c.save()

        comments = a.comments_as_user(self.blue_user)

        # TODO: check that this has the intended effects

    def test_article_translation(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       content='this is a test')
        a.save()

        at = db.ArticleTranslation(article=a, language='piglatin', title='est-tay itle-tay',
                                   content='is-thay is-ay a-ay est-tay')
        at.save()

        a.translate('piglatin')

        assert 'itle-tay' in a.title
        assert 'is-thay' in a.content
        
    def test_news_article(self):
        # TODO: create news and non-news articles

        na = db.NewsArticle.objects.all()
        fp = db.ForumPost.objects.all()

        # TODO: check that all news articles are on the na list and
        # all non-news articles are not, and vice-versa for fp list

    def test_comment(self):
        c = db.Comment(article=self.article, user=self.blue_user, content='nice test')
        c.save()
                       
        assert str(c) != ''
        assert c.get_absolute_url() != ''
        assert c.get_forum_url() != ''

        assert len(c.as_dict().keys()) > 0

    def test_comment_delete(self):
        c = db.Comment(article=self.article, user=self.blue_user, content='nice test')
        c.save()

        assert c.is_deleted == False

        c.delete()
        assert c.is_deleted == True


    def test_comment_up_down_vote(self):
        c = db.Comment(article=self.article, user=self.blue_user, content='nice test')
        c.save()

        c.upvote(self.green_user)

        assert c.karma == 1
        assert c.ups == 1

        c.downvote(self.red_user)
        assert c.karma == 0
        assert c.downs == 1

        c.karma = 100
        c.save()
        db.Comment.recalculate()
        c = db.Comment.objects.get(content='nice test')
        assert c.karma == 0

    def test_comment_vote_prune(self):
        c = db.Comment(article=self.article, user=self.blue_user, content='nice test')
        c.save()
        c.upvote(self.green_user)

        db.CommentVote.prune()

    def test_message(self):
        m = db.Message(from_user=self.blue_user, to_user=self.red_user,
                       content='hey, what\'s up?')
        m.save()

        assert str(m) != ''
        assert len(m.as_dict()) > 0

    def test_message_delete(self):
        m = db.Message(from_user=self.blue_user, to_user=self.red_user,
                       content='hey, what\'s up?')
        m.save()

        m.delete()
        assert m.is_deleted == True

    def test_ride(self):
        # TODO: add tests for this model if it is still in use
        pass

    def test_ride_request(self):
        # TODO: add tests for this model if it is still in use
        pass

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
