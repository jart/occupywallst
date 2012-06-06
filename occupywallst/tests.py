r"""

    occupywallst.tests
    ~~~~~~~~~~~~~~~~~~

    Regression tests.  These should be run before deploying code to
    make sure our changes didn't break anything.

"""

import json
import random
from datetime import datetime
from itertools import product

import redisbayes
from django.conf import settings
from django.test import TestCase
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse

from occupywallst import api
from occupywallst import models as db
from occupywallst.templatetags import ows


jdump = lambda v: json.dumps(v, indent=2)
fresh = lambda o: o.__class__.objects.get(id=o.id)
totup = lambda v: v if isinstance(v, tuple) else (v,)


def dict_product(data):
    """Returns cartesian product of a dictionary

    Turns this::

        {'hello': 'kitty', 'letters': ('a', 'b', 'c'), 'numbers': (1, 2, 3)}

    Into this::

        [{'hello': 'kitty', 'letters': 'a', 'numbers': 1},
         {'hello': 'kitty', 'letters': 'a', 'numbers': 2},
         {'hello': 'kitty', 'letters': 'a', 'numbers': 3},
         {'hello': 'kitty', 'letters': 'b', 'numbers': 1},
         {'hello': 'kitty', 'letters': 'b', 'numbers': 2},
         {'hello': 'kitty', 'letters': 'b', 'numbers': 3},
         {'hello': 'kitty', 'letters': 'c', 'numbers': 1},
         {'hello': 'kitty', 'letters': 'c', 'numbers': 2},
         {'hello': 'kitty', 'letters': 'c', 'numbers': 3}]

    """
    keys = data.keys()
    vals = [totup(v) for v in data.values()]
    return [dict(zip(keys, r)) for r in product(*vals)]


def assert_success(response):
    assert response.status_code == 200, \
        'request should be successful (found "%d")' % (response.status_code)


def assert_redirect(response):
    assert response.status_code == 302, \
        'request should be redirect (found "%d")' % (response.status_code)


def assert_and_get_valid_json(response):
    j = json.loads(response.content)
    #raise AssertionError, \
    #    'request should be valid json (found "%s...")' % response.content[:32]
    return j


def random_slug(N=20):
    letters = [chr(x) for x in range(ord('a'), ord('z') + 1)]
    return ''.join(random.choice(letters) for x in range(N))


def random_words(N=20):
    """Choose N random words for content"""
    words = ('Lorem ipsum dolor sit amet consectetur adipisicing elit sed '
             'do eiusmod tempor incididunt ut labore et dolore magna aliqua '
             'Ut enim ad minim veniam quis nostrud exercitation ullamco '
             'laboris nisi ut aliquip ex ea commodo consequat Duis aute '
             'irure dolor in reprehenderit in voluptate velit esse cillum '
             'dolore eu fugiat nulla pariatur Excepteur sint occaecat '
             'cupidatat non proident sunt in culpa qui officia deserunt '
             'mollit anim id est laborum').split()
    return ' '.join(random.choice(words) for n in range(N))


def add_content(N):
    """Add N articles and comments to the database, for testing etc."""
    settings.DEBUG = True
    users = [u for u in db.User.objects.all()]

    for i in range(N):
        a = api.article_new(user=random.choice(users),
                            title=random_words(5),
                            content=random_words(50),
                            is_forum=True)
        comment_ids = []
        for j in range(N):
            c = api.comment_new(user=random.choice(users),
                                article_slug=a[0]['slug'],
                                parent_id=random.choice([0] + comment_ids),
                                content=random_words(20))
            comment_ids.append(c[0]['id'])

            for k in range(N):
                api.comment_upvote(random.choice(users),
                                   random.choice(comment_ids))
                api.comment_downvote(random.choice(users),
                                   random.choice(comment_ids))


def new_user(username=None, password=None, email='', is_staff=False,
             is_active=True, is_superuser=False, **kwargs):
    username = username or random_slug()
    password = password or random_slug()
    user = db.User.objects.create_user(username, email, password)
    user.is_staff = is_staff
    user.is_active = is_active
    user.is_superuser = is_superuser
    user.userinfo = db.UserInfo.objects.create(user=user, **kwargs)
    user.save()
    user.password_hack = password
    return user


def new_article(user, **kwargs):
    vals = dict(author=user,
                published=datetime.now(),
                title=random_words(7),
                slug=random_slug(),
                content=random_words(20),
                is_forum=True,
                is_visible=True)
    vals.update(kwargs)
    return db.Article.objects.create(**vals)


def new_comment(article, user, **kwargs):
    vals = dict(user=user,
                article=article,
                content=random_words(20))
    vals.update(kwargs)
    return db.Comment.objects.create(**vals)


def update(o, **kwargs):
    for k, v in kwargs.items():
        setattr(o, k, v)
    o.save()
    return o


def copy_content(article_slug):
    """ copy article, comments, and users from live ows.org site to
    development data base"""

    import requests

    # copy article
    r = requests.get('http://occupywallst.org/api/safe/article_get/?article_slug=%s'%article_slug)
    j = json.loads(r.content)
    a = j['results'][0]

    username = a.pop('author')
    user, exists = db.User.objects.get_or_create(username=username)
    a.pop('html')
    a.pop('url')
    a.pop('published') # TODO: replace with a valid date time format
    article, exists = db.Article.objects.get_or_create(author=user, **a)


    # copy comments
    r = requests.get('http://occupywallst.org/api/safe/article_get_comments/?article_slug=%s'%article_slug)
    j = json.loads(r.content)

    for c in j['results']:
        username = c.pop('user')
        user, exists = db.User.objects.get_or_create(username=username)
        c.pop('published') # TODO: valid date time format
        comment, exists = db.Comment.objects.get_or_create(article=article, **c)

        # TODO: add upvotes and downvotes


class OWS(TestCase):
    fixtures = ['verbiage', 'example_data']

    def create_users(self):
        """Create users for functional testing of access control.

        It seems easier to create the users with a code block than as
        json fixtures, because the password is clearer before it is
        encrypted.
        """
        from django.contrib.auth.models import User
        self.red_user = User.objects.create_user('red', '', 'red')
        self.green_user = User.objects.create_user('green', '', 'green')
        self.blue_user = User.objects.create_user('blue', '', 'blue')
        self.admin_user = User.objects.create_user('admin', '', 'admin')
        self.staff_user = User.objects.create_user('staff', '', 'staff')
        self.mod_user = User.objects.create_user('mod', '', 'mod')
        for u in [self.red_user, self.green_user, self.blue_user,
                  self.admin_user, self.staff_user, self.mod_user]:
            ui = db.UserInfo(user=u)
            ui.save()
        self.admin_user.is_staff = True
        self.admin_user.is_admin = True
        self.admin_user.save()
        self.staff_user.is_staff = True
        self.staff_user.save()
        self.mod_user.userinfo.is_moderator = True
        self.mod_user.userinfo.save()

    def setUp(self):
        redisbayes.RedisBayes().flush()
        settings.OWS_LIMIT_VOTES = ()
        settings.OWS_LIMIT_THREAD = -1
        settings.OWS_LIMIT_COMMENT = -1
        settings.OWS_LIMIT_MSG_DAY = 999999
        self.create_users()
        self.article = db.Article(author=self.red_user,
                                  published=datetime.now(),
                                  title='article title',
                                  slug='article-slug',
                                  content='exciting article content')
        self.article.save()
        comment_list = api.comment_new(user=self.blue_user,
                                       article_slug=self.article.slug,
                                       parent_id=0,
                                       content=random_words(20))
        self.comment = db.Comment.objects.get(id=comment_list[0]['id'])

        # add a second comment
        api.comment_new(user=self.blue_user,
                        article_slug=self.article.slug,
                        parent_id=0,
                        content=random_words(20))

        self.carousel = db.Carousel()
        self.carousel.save()

        self.photo = db.Photo(carousel=self.carousel, caption='hello, world')
        self.photo.save()


    ######################################################################
    # tests of models

    def test_verbiage(self):
        """Test verbiage model"""
        assert db.Verbiage.get('title') != None, 'should have a title'
        assert db.Verbiage.get('title') != None, \
            'should cache title for second request'
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
        ui = db.UserInfo(user=self.red_user, position=Point((20, 10)))
        assert ui.position_lat == 10
        assert ui.position_lng == 20
        assert ui.position_latlng == (10, 20)

    def test_notification_send(self):
        cnt = self.red_user.notification_set.count()
        db.Notification.send(self.red_user,
                             'http://dev.occupywallst.org', 'test message')
        assert self.red_user.notification_set.count() == cnt + 1

        # send the same notification again, it should not go
        db.Notification.send(self.red_user,
                             'http://dev.occupywallst.org', 'test message')
        assert self.red_user.notification_set.count() == cnt + 1

        # now mark it as read, send it again, and it should go
        for n in self.red_user.notification_set.all():
            n.is_read = True
            n.save()

        db.Notification.send(self.red_user,
                             'http://dev.occupywallst.org', 'test message')
        assert self.red_user.notification_set.count() == cnt + 2

    def test_notification_broadcast(self):
        db.Notification.broadcast('hello everyone')
        # TODO: confirm that this had intended effect

    def test_article(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       published=datetime.now(),
                       content='this is a test')
        a.save()
        assert len(a.as_dict()) > 0

    def test_article_delete(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       published=datetime.now(),
                       content='this is a test')
        a.save()
        assert a.is_deleted == False
        a.delete()
        assert db.Article.objects.get(slug='test').is_deleted == True

    def test_article_recalculate(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       published=datetime.now(), content='this is a test')
        a.save()

        # add comment
        c = db.Comment(article=a, user=self.blue_user, content='nice test')
        c.save()

        db.Article.recalculate()
        # TODO: check that the comment count for the article is correct

    def test_article_comments_as_user(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       published=datetime.now(),
                       content='this is a test')
        a.save()

        # add comment as self.blue_user
        c = db.Comment(article=a, user=self.blue_user, content='nice test')
        c.save()

        # TODO: do something with me
        # comments = a.comments_as_user(self.blue_user)

        # TODO: check that this has the intended effects

    def test_article_translation(self):
        a = db.Article(author=self.red_user, title='test title', slug='test',
                       published=datetime.now(),
                       content='this is a test')
        a.save()
        at = db.ArticleTranslation(article=a, language='piglatin',
                                   title='est-tay itle-tay',
                                   content='is-thay is-ay a-ay est-tay')
        at.save()
        a.translate('piglatin')
        assert 'itle-tay' in a.title
        assert 'is-thay' in a.content

    # def test_news_article(self):
    #     # TODO: create news and non-news articles
    #     na = db.NewsArticle.objects.all()
    #     fp = db.ForumPost.objects.all()
    #     # TODO: check that all news articles are on the na list and
    #     # all non-news articles are not, and vice-versa for fp list

    def test_comment(self):
        c = db.Comment(article=self.article, user=self.blue_user,
                       content='nice test')
        c.save()
        assert str(c) != ''
        assert c.get_absolute_url() != ''
        assert c.get_forum_url() != ''
        assert len(c.as_dict().keys()) > 0

    def test_comment_delete(self):
        c = db.Comment(article=self.article, user=self.blue_user,
                       content='nice test')
        c.save()
        assert c.is_deleted == False
        c.delete()
        assert c.is_deleted == True

    def test_comment_up_down_vote(self):
        c = db.Comment(article=self.article, user=self.blue_user,
                       content='nice test')
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
        c = db.Comment(article=self.article, user=self.blue_user,
                       content='nice test')
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

    def test_photo(self):
        m = db.Photo()
        # TODO: test that it saves and processes images

    def test_carousel(self):
        m = db.Carousel()
        # TODO: test more

    # tests of views

    def test_index(self):
        url = reverse('occupywallst.views.index')
        response = self.client.get(url)
        assert_success(response)

    def test_cache_and_translation(self):
        def get_several_ways(url):
            """
            Since the app uses fancy caching there are several paths
            worth testing for each view:

              * not logged in
              * second request when not logged in (uses cache)
              * using a language other than english
              * logged in

            """
            response = self.client.get(url)
            assert_success(response)
            assert 'Welcome' in response.content

            # repeat request, to test caching code
            response = self.client.get(url)
            assert_success(response)

            # repeat request, in spanish
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE='es')
            assert_success(response)
            assert 'Bienvenido' in response.content
            assert 'Welcome' not in response.content

            # repeat request when logged in
            self.client.login(username='red', password='red')
            response = self.client.get(url)
            assert_success(response)

            # repeat request, to test caching code
            response = self.client.get(url)
            assert_success(response)

        for url in [reverse('occupywallst.views.index'),
                    reverse('occupywallst.views.forum')]:
            get_several_ways(url)

    def test_forum(self):
        url = reverse('occupywallst.views.forum')
        response = self.client.get(url)
        assert_success(response)

    def test_articles(self):
        for article in db.Article.objects.all():
            response = self.client.get(article.get_absolute_url())
            assert_success(response)
            self.assertContains(response, ows.markup(article.content))

    def test_attendees(self):
        response = self.client.get('/attendees/')
        assert_success(response)

    def test_rides(self):
        response = self.client.get('/rides/')
        assert_success(response)

    def test_calendar(self):
        response = self.client.get('/calendar/')
        assert_success(response)

    def test_donate(self):
        response = self.client.get('/donate/')
        assert_success(response)

    def test_about(self):
        response = self.client.get('/about/')
        assert_success(response)

    def test_login(self):
        url = '/login/'
        response = self.client.get(url)
        assert_success(response)
        response = self.client.post(url, {'username': 'red',
                                          'password': 'wrong'})
        assert 'enter a correct username and password' in response.content
        response = self.client.post(url, {'username': 'red',
                                          'password': 'red'})
        assert_redirect(response)

    def test_logout(self):
        self.client.login(username='red', password='red')
        response = self.client.get('/logout/')
        assert_success(response)
        assert 'login' in response.content

    def test_signup(self):
        url = '/signup/'
        response = self.client.get(url)
        assert_success(response)

        # clear the cache to avoid code that prevents many signups
        # from same ip address
        from django.core.cache import cache
        cache.clear()

        response = self.client.post(url, {'username': 'purple',
                                          'password': 'purple'}, follow=True)
        assert_success(response)
        assert 'purple' in response.content, response.content

    def test_user_pages(self):
        for user in db.UserInfo.objects.all():
            response = self.client.get(user.get_absolute_url())
            assert_success(response)

    ######################################################################
    # test of feeds

    def test_rss_news(self):
        response = self.client.get('/rss/news/')
        assert_success(response)

    def test_rss_forum(self):
        response = self.client.get('/rss/forum/')
        assert_success(response)

    def test_rss_comments(self):
        response = self.client.get('/rss/comments/')
        assert_success(response)

    ######################################################################
    # tests of apis

    def test_api_attendees(self):
        response = self.client.get('/api/safe/attendees/')
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)

        response = self.client.get('/api/safe/attendees/',
                                   {'bounds': '10,10,20,20'})
        assert_success(response)
        j = assert_and_get_valid_json(response)
        assert j['status'] != 'ERROR', jdump(j)

        # TODO: test that users appear in bounds when they are supposed to

    def test_api_attendee_info(self):
        response = self.client.get('/api/safe/attendee_info/')
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)

        response = self.client.get('/api/safe/attendee_info/',
                                   {'username': 'not_a_user'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)

        response = self.client.get('/api/safe/attendee_info/',
                                   {'username': 'red'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        assert j['results'][0]['username'] == 'red', jdump(j)

    def test_api_rides(self):
        response = self.client.get('/api/safe/rides/')
        j = assert_and_get_valid_json(response)
        assert j['status'] != 'ERROR', jdump(j)

    def test_api_article_get(self):
        self.client.login(username='red', password='red')
        response = self.client.get('/api/safe/article_get/',
                                   {'article_slug': self.article.slug})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)

    def test_api_article_get_comments(self):
        self.client.login(username='red', password='red')
        response = self.client.get('/api/safe/article_get_comments/',
                                   {'article_slug': self.article.slug})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        assert len(j['results']) == self.article.comment_set.count(), jdump(j)

    def test_api_article_get_comment_votes(self):
        self.client.login(username='red', password='red')
        response = self.client.get('/api/safe/article_get_comment_votes/',
                                   {'article_slug': self.article.slug})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        assert len(j['results']) == self.article.comment_set.count(), jdump(j)

    def test_api_comment_get(self):
        response = self.client.get('/api/safe/comment_get/',
                                   {'comment_id': self.comment.id})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)

    def test_api_carousel_get(self):
        response = self.client.get('/api/safe/carousel_get/',
                                   {'carousel_id': self.carousel.id})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)

    def test_api_forumlinks(self):
        response = self.client.get('/api/safe/forumlinks/',
                                   {'after': 0, 'count': 10})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)

    def test_api_check_username(self):
        # already taken
        response = self.client.post('/api/check_username/',
                                    {'username': self.red_user.username})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)

        # too short
        response = self.client.post('/api/check_username/',
                                    {'username': 'r'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)

        # too long
        response = self.client.post('/api/check_username/',
                                    {'username': 'r' * 31})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)

        # too funky
        response = self.client.post('/api/check_username/',
                                    {'username': '!@#$%'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)

        # just right
        response = self.client.post('/api/check_username/',
                                    {'username': 'totally_new_user'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ZERO_RESULTS', jdump(j)  # this means success

    # def test_api_signup(self):
    #     # already taken
    #     response = self.client.post('/api/signup/',
    #                                 {'username': self.red_user.username,
    #                                  'password': '123456',
    #                                  'email': 'new@occupywallst.org'})
    #     j = assert_and_get_valid_json(response)
    #     assert j['status'] == 'ERROR', jdump(j)

    #     # password too short
    #     response = self.client.post('/api/signup/',
    #                                 {'username': 'new_user',
    #                                  'password': '1234',
    #                                  'email': 'new@occupywallst.org'})
    #     j = assert_and_get_valid_json(response)
    #     assert j['status'] == 'ERROR', jdump(j)

    #     # email no good
    #     response = self.client.post('/api/signup/',
    #                                 {'username': 'new_user',
    #                                  'password': '123456',
    #                                  'email': 'new@occupy'})
    #     j = assert_and_get_valid_json(response)
    #     assert j['status'] == 'ERROR', jdump(j)

    #     # just right
    #     response = self.client.post('/api/signup/',
    #                                 {'username': 'new_user',
    #                                  'password': '123456',
    #                                  'email': 'new@occupywallst.org'})
    #     j = assert_and_get_valid_json(response)
    #     assert j['status'] == 'OK', jdump(j)

    #     # but trying it again fails, because we're now logged in
    #     response = self.client.post('/api/signup/',
    #                                 {'username': 'new_user',
    #                                  'password': '123456',
    #                                  'email': 'new@occupywallst.org'})
    #     j = assert_and_get_valid_json(response)
    #     assert j['status'] == 'ERROR', jdump(j)
    #     assert 'logged in' in j['message'], jdump(j)

    #     # and even if we log out, it still fails, because the user now exists
    #     self.client.post('/api/logout/')
    #     response = self.client.post('/api/signup/',
    #                                 {'username': 'new_user',
    #                                  'password': '123456',
    #                                  'email': 'new@occupywallst.org'})
    #     j = assert_and_get_valid_json(response)
    #     assert j['status'] == 'ERROR', jdump(j)
    #     assert j['message'] == 'username is taken', jdump(j)

    def test_api_login_and_logout(self):
        # should be same for invalid username and invalid password,
        # for increased security
        error_str = 'invalid username or password'
        # invalid user
        response = self.client.post('/api/login/',
                                    {'username': 'redff',
                                     'password': 'red'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)
        assert j['message'] == error_str, jdump(j)

        # invalid password
        response = self.client.post('/api/login/',
                                    {'username': 'red',
                                     'password': 'redff'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)
        assert j['message'] == error_str, jdump(j)

        # correct username/password
        response = self.client.post('/api/login/',
                                    {'username': 'red',
                                     'password': 'red'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        assert j['results'][0]['username'] == 'red', jdump(j)

        # logging in again should succeed
        response = self.client.post('/api/login/',
                                    {'username': 'blue',
                                     'password': 'blue'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        assert j['results'][0]['username'] == 'blue', jdump(j)

        # logging out and in should succeed
        response = self.client.post('/api/logout/')
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ZERO_RESULTS', jdump(j)

        response = self.client.post('/api/login/',
                                    {'username': 'blue',
                                     'password': 'blue'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        assert j['results'][0]['username'] == 'blue', jdump(j)

    def test_api_message(self):
        settings.DEBUG = True
        content = random_words(10)

        # login as red
        self.client.post('/api/login/', {'username': 'red', 'password': 'red'})

        #  send a message to blue
        response = self.client.post('/api/message_send/',
                                    {'to_username': 'blue',
                                     'content': content})

        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        m = db.Message.objects.get(id=j['results'][0]['id'])
        assert m.content == content

        # delete the message
        response = self.client.post('/api/message_delete/',
                                    {'message_id': m.id})

        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ZERO_RESULTS', jdump(j)
        m = db.Message.objects.get(id=m.id)
        assert m.content == ''

        # now again, but delete by blue
        response = self.client.post('/api/message_send/',
                                    {'to_username': 'blue',
                                     'content': content})
        j = assert_and_get_valid_json(response)
        m = db.Message.objects.get(id=j['results'][0]['id'])
        assert m.content == content

        self.client.post('/api/logout/')
        self.client.post('/api/login/', {'username': 'blue',
                                         'password': 'blue'})
        response = self.client.post('/api/message_delete/',
                                    {'message_id': m.id})

        settings.DEBUG = False

    def test_api_article(self):
        title = random_words(5)
        content = random_words(20)

        # login as red
        self.client.post('/api/login/', {'username': 'red',
                                         'password': 'red'})

        # create a new article
        response = self.client.post('/api/article_new/',
                                    {'title': title,
                                     'content': content,
                                     'is_forum': True})
        j = assert_and_get_valid_json(response)
        a = db.Article.objects.get(id=j['results'][0]['id'])
        assert a.content == content

        # edit it
        new_title = random_words(2)
        new_content = random_words(25)
        response = self.client.post('/api/article_edit/',
                                    {'article_slug': a.slug,
                                     'title': new_title,
                                     'content': new_content})
        j = assert_and_get_valid_json(response)
        a = db.Article.objects.get(id=j['results'][0]['id'])
        assert a.content == new_content
        assert a.title == new_title

        # delete it
        response = self.client.post('/api/article_delete/',
                                    {'article_slug': a.slug})
        j = assert_and_get_valid_json(response)
        a = db.Article.objects.get(id=a.id)
        assert a.content == '[DELETED]'

        # create a new article
        title = random_words(5)
        content = random_words(20)
        response = self.client.post('/api/article_new/',
                                    {'title': title,
                                     'content': content,
                                     'is_forum': True})
        j = assert_and_get_valid_json(response)
        a = db.Article.objects.get(id=j['results'][0]['id'])

        # logout and login as an admin
        self.client.post('/api/logout/')
        self.client.post('/api/login/', {'username': 'OccupyWallSt',
                                         'password': 'anarchy'})

        # remove it
        response = self.client.post('/api/article_remove/',
                                    {'article_slug': a.slug,
                                     'action': 'remove'})
        j = assert_and_get_valid_json(response)
        a = db.Article.objects.get(id=a.id)
        assert a.is_visible == False

        # unremove it
        response = self.client.post('/api/article_remove/',
                                    {'article_slug': a.slug,
                                     'action': 'unremove'})
        j = assert_and_get_valid_json(response)
        a = db.Article.objects.get(id=a.id)
        assert a.is_visible == True

        # delete it
        response = self.client.post('/api/article_delete/',
                                    {'article_slug': a.slug})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ZERO_RESULTS', jdump(j)

    def test_api_comment(self):
        settings.OWS_LIMIT_COMMENT = -1  # turn off limit for testing
        content = random_words(20)

        # login as red
        self.client.post('/api/login/', {'username': 'red', 'password': 'red'})

        # create a comment
        response = self.client.post('/api/comment_new/',
                                    {'article_slug': self.article.slug,
                                     'parent_id': '',
                                     'content': content})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=j['results'][0]['id'])
        assert c.content == content

        # create a child of that comment
        parent_id = c.id
        response = self.client.post('/api/comment_new/',
                                    {'article_slug': self.article.slug,
                                     'parent_id': parent_id,
                                     'content': content})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=j['results'][0]['id'])
        assert c.content == content

        # edit it
        new_content = random_words(25)
        response = self.client.post('/api/comment_edit/',
                                    {'comment_id': c.id,
                                     'content': new_content})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=j['results'][0]['id'])
        assert c.content == new_content

        # delete it
        response = self.client.post('/api/comment_delete/',
                                    {'comment_id': c.id})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=c.id)
        assert c.content == ''

        # create a comment
        response = self.client.post('/api/comment_new/',
                                    {'article_slug': self.article.slug,
                                     'parent_id': '',
                                     'content': content})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=j['results'][0]['id'])

        # logout and login as an admin
        self.client.post('/api/logout/')
        self.client.post('/api/login/', {'username': 'OccupyWallSt',
                                         'password': 'anarchy'})

        # remove it
        response = self.client.post('/api/comment_remove/',
                                    {'comment_id': c.id,
                                     'action': 'remove'})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=c.id)
        assert c.is_removed == True

        # unremove it
        response = self.client.post('/api/comment_remove/',
                                    {'comment_id': c.id,
                                     'action': 'unremove'})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=c.id)
        assert c.is_removed == False

        # grant moderator permissions to green
        self.green_user.userinfo.is_moderator = True
        self.green_user.userinfo.save()

        assert self.green_user.userinfo.can_moderate()

        # logout and login as green
        self.client.post('/api/logout/')
        self.client.post('/api/login/', {'username': 'green', 'password': 'green'})

        # remove red's comment
        response = self.client.post('/api/comment_remove/',
                                    {'comment_id': c.id,
                                     'action': 'remove'})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=c.id)
        assert c.is_removed == True

        # unremove it
        response = self.client.post('/api/comment_remove/',
                                   {'comment_id': c.id,
                                    'action': 'unremove'})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=c.id)
        assert c.is_removed == False

        # logout and login as blue
        self.client.post('/api/logout/')
        self.client.post('/api/login/', {'username': 'blue', 'password': 'blue'})

        # try to remove red's comment, should fail
        response = self.client.post('/api/comment_remove/',
                                    {'comment_id': c.id,
                                     'action': 'remove'})
        c = db.Comment.objects.get(id=c.id)
        assert c.is_removed == False

        # logout and login as admin
        self.client.post('/api/logout/')
        self.client.post('/api/login/', {'username': 'OccupyWallSt', 'password': 'anarchy'})

        # upvote it
        ups = c.ups
        response = self.client.post('/api/comment_upvote/', {'comment': c.id})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=c.id)
        assert c.ups == ups + 1

        # downvote it
        downs = c.downs
        response = self.client.post('/api/comment_downvote/',
                                    {'comment': c.id})
        j = assert_and_get_valid_json(response)
        c = db.Comment.objects.get(id=c.id)
        assert c.downs == downs + 1

    def test_api_comment_spam(self):
        self.client.post('/api/login/', {'username': 'red', 'password': 'red'})

        response = self.client.post(
            '/api/comment_new/', {'article_slug': self.article.slug,
                                  'parent_id': '',
                                  'content': 'VISIT SWAMPTHING.COM TODAY!'})
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'ERROR', jdump(j)
        assert j['message'] == 'turn off bloody caps lock', jdump(j)

        data = {'article_slug': self.article.slug,
                'parent_id': '',
                'content': 'visit swampthing.com today!'}

        response = self.client.post('/api/comment_new/', data)
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        c = db.Comment.objects.get(id=j['results'][0]['id'])
        assert not c.is_removed

        assert not db.SpamText.is_spam(c.content)
        db.SpamText.objects.create(text='swampthing.com')
        assert db.SpamText.is_spam(c.content)

        response = self.client.post('/api/comment_new/', data)
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        c = db.Comment.objects.get(id=j['results'][0]['id'])
        assert c.is_removed

    def test_shadow_ban(self):
        self.client.post('/api/login/', {'username': 'red', 'password': 'red'})

        data = {'article_slug': self.article.slug,
                'parent_id': '',
                'content': 'oh my goth'}

        response = self.client.post('/api/comment_new/', data)
        j = assert_and_get_valid_json(response)
        import pprint
        pprint.pprint(j)
        assert j['status'] == 'OK', jdump(j)
        c = db.Comment.objects.get(id=j['results'][0]['id'])
        assert not c.is_removed

        self.red_user.userinfo.is_shadow_banned = True
        self.red_user.userinfo.save()

        response = self.client.post('/api/comment_new/', data)
        j = assert_and_get_valid_json(response)
        assert j['status'] == 'OK', jdump(j)
        c = db.Comment.objects.get(id=j['results'][0]['id'])
        assert c.is_removed

        self.red_user.userinfo.is_shadow_banned = False
        self.red_user.userinfo.save()


class TestAPI(TestCase):
    def setUp(self):
        settings.TEST_MODE = True
        settings.OWS_LIMIT_VOTES = ()
        settings.OWS_LIMIT_THREAD = -1
        settings.OWS_LIMIT_COMMENT = -1
        settings.OWS_LIMIT_MSG_DAY = 999999

    def invoke(self, api, data, extra):
        resp = self.client.post(api, data, **extra)
        if resp.status_code != 200:
            raise Exception("%s gave unexpected status code: %d"
                            % (api, resp.status_code))
        return json.loads(resp.content)

    def good(self, api, data={}, **extra):
        for api, data, extra in product(totup(api),
                                        dict_product(data),
                                        dict_product(extra)):
            res = self.invoke(api, data, extra)
            if res['status'] == 'ERROR':
                raise Exception('unexpected api failure\n' +
                                'api = ' + jdump(api) + '\n' +
                                'args = ' + jdump(data) + '\n' +
                                'extra = ' + jdump(extra) + '\n' +
                                'result = ' + jdump(res) + '\n')
        return res

    def bad(self, msg, api, data={}, **extra):
        for api, data, extra in product(totup(api),
                                        dict_product(data),
                                        dict_product(extra)):
            res = self.invoke(api, data, extra)
            if res['status'] != 'ERROR':
                raise Exception("api didn't fail\n" +
                                'api = ' + jdump(api) + '\n' +
                                'args = ' + jdump(data) + '\n' +
                                'extra = ' + jdump(extra) + '\n' +
                                'result = ' + jdump(res) + '\n')
            self.assertEqual(res['message'], msg)
        return res

    def login(self, user):
        self.good('/api/login/', {'username': user.username,
                                  'password': user.password_hack})

    def logout(self):
        self.good('/api/logout/')

    def test_comment_vote(self):
        votes = lambda c: (c.karma, c.ups, c.downs)
        c = new_comment(new_article(new_user()), new_user())
        self.assertEqual(votes(fresh(c)), (0, 0, 0))

        # must be logged in
        self.logout()
        self.bad('not logged in', '/api/comment_upvote/', {'comment': c.id})
        self.bad('not logged in', '/api/comment_downvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (0, 0, 0))

        # comment must exist
        self.login(new_user())
        self.bad('comment not found', '/api/comment_upvote/', {'comment': 0})
        self.bad('comment not found', '/api/comment_downvote/', {'comment': 0})

        # can only vote once
        self.login(new_user())
        self.good('/api/comment_downvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (-1, 0, 1))
        self.good('/api/comment_downvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (-1, 0, 1))
        self.good('/api/comment_upvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (1, 1, 0))
        self.good('/api/comment_upvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (1, 1, 0))

        # multiple votes / tallying
        self.login(new_user())
        self.good('/api/comment_upvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (2, 2, 0))
        self.login(new_user())
        self.good('/api/comment_downvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (1, 2, 1))
        self.login(new_user())
        self.good('/api/comment_downvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (0, 2, 2))
        self.login(new_user())
        self.good('/api/comment_downvote/', {'comment': c.id})
        self.assertEqual(votes(fresh(c)), (-1, 2, 3))

        # removed/deleted stuff
        c = update(c, is_deleted=True)
        self.bad('comment not found', '/api/comment_upvote/', {'comment': c.id})
        self.bad('comment not found', '/api/comment_downvote/', {'comment': c.id})
        c = update(c, is_removed=True, is_deleted=False)
        self.good('/api/comment_upvote/', {'comment': c.id})
        self.good('/api/comment_downvote/', {'comment': c.id})

    def test_shadowban(self):
        user = new_user()

        # normal users can't ban
        self.logout()
        self.bad("you're not logged in", '/api/shadowban/', {'action': 'ban', 'username': user.username})
        self.login(new_user())
        self.bad("insufficient permissions", '/api/shadowban/', {'action': 'ban', 'username': user.username})

        # but moderators can
        self.login(new_user(is_moderator=True))
        self.good('/api/shadowban/', {'action': 'ban', 'username': user.username})
        self.good('/api/shadowban/', {'action': 'unban', 'username': user.username})

        # and staff can
        self.login(new_user(is_staff=True))
        self.good('/api/shadowban/', {'action': 'ban', 'username': user.username})
        self.good('/api/shadowban/', {'action': 'unban', 'username': user.username})

        # you can't post shit when banned
        def tryit(expect_removed):
            self.login(user)
            data = self.good('/api/article_new/', {'title': random_words(10), 'content': random_words(), 'is_forum': 'true'})
            art = db.Article.objects.get(id=data['results'][0]['id'])
            self.assertEqual(art.is_removed, expect_removed)
            data = self.good('/api/comment_new/', {'article_slug': art.slug, 'parent_id': '', 'content': random_words()})
            com = db.Comment.objects.get(id=data['results'][0]['id'])
            self.assertEqual(com.is_removed, expect_removed)
        self.login(user)
        tryit(False)
        self.login(new_user(is_moderator=True))
        self.good('/api/shadowban/', {'action': 'ban', 'username': user.username})
        self.login(user)
        tryit(True)
        self.login(new_user(is_moderator=True))
        self.good('/api/shadowban/', {'action': 'unban', 'username': user.username})

        # same goes for staff
        self.login(new_user(is_staff=True))
        self.good('/api/shadowban/', {'action': 'ban', 'username': user.username})
        self.good('/api/shadowban/', {'action': 'unban', 'username': user.username})

        # but you can't ban important people
        self.login(new_user(is_moderator=True))
        self.bad("cannot ban privileged users", '/api/shadowban/', {'action': 'ban', 'username': new_user(is_staff=True).username})
        self.bad("cannot ban privileged users", '/api/shadowban/', {'action': 'ban', 'username': new_user(is_moderator=True).username})

    def test_delete(self):
        # you need to be logged in
        self.logout()
        self.bad("you're not logged in", '/api/comment_delete/', {'comment_id': '666'})
        self.bad("you're not logged in", '/api/article_delete/', {'article_slug': '666'})

        # you can delete your stuff
        user = new_user()
        art = new_article(user)
        com = new_comment(art, user)
        self.login(user)
        self.good('/api/comment_delete/', {'comment_id': com.id})
        self.good('/api/article_delete/', {'article_slug': art.slug})
        # unless it was converted to a news article
        art = update(art, is_forum=False)
        self.bad('insufficient privileges', '/api/article_delete/', {'article_slug': art.slug})

        # but you can't delete other people's stuff
        me, them = new_user(), new_user()
        art = new_article(them)
        com = new_comment(art, them)
        self.login(me)
        self.bad("you didn't post that", '/api/comment_delete/', {'comment_id': com.id})
        self.bad("you didn't post that", '/api/article_delete/', {'article_slug': art.slug})

        # unless you're a mod
        me, them = new_user(is_moderator=True), new_user()
        art = new_article(them)
        com = new_comment(art, them)
        self.login(me)
        self.good('/api/comment_delete/', {'comment_id': com.id})
        self.good('/api/article_delete/', {'article_slug': art.slug})

    def test_remove(self):
        # you need to be logged in
        self.logout()
        self.bad("you're not logged in", ('/api/comment_remove/', '/api/article_remove/'),
                 {'action': ('remove', 'unremove'), 'comment_id': '666', 'article_slug': '666'})

        # this is a mod only feature
        user = new_user()
        art = new_article(user)
        com = new_comment(art, user)
        self.login(user)
        self.bad('insufficient permissions', '/api/comment_remove/', {'action': ('remove', 'unremove'), 'comment_id': com.id})
        self.bad('insufficient permissions', '/api/article_remove/', {'action': ('remove', 'unremove'), 'article_slug': art.slug})
        self.login(new_user())
        self.bad('insufficient permissions', '/api/comment_remove/', {'action': ('remove', 'unremove'), 'comment_id': com.id})
        self.bad('insufficient permissions', '/api/article_remove/', {'action': ('remove', 'unremove'), 'article_slug': art.slug})
        self.login(new_user(is_moderator=True))
        self.good('/api/comment_remove/', {'action': ('remove', 'unremove'), 'comment_id': com.id})
        self.good('/api/article_remove/', {'action': ('remove', 'unremove'), 'article_slug': art.slug})
