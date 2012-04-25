r"""

    occupywallst.api
    ~~~~~~~~~~~~~~~~

    High-level functions for fetching and manipulating data.  These
    functions primarily serve as remote procedure calls (not CRUD or
    REST) for the website's javascript code.

    Unlike ``views.py``, the API is designed to be (mostly) decoupled
    from the HTTP request/response mechanism.  All the HTTP/JSON stuff
    is applied by decorators which are specified in ``urls.py``.  If
    you want to see how the HTTP request/response logic is applied,
    check out ``utils.py``.  I designed things this way so:

    - These functions can be called internally by other Python code.

    - I can write xml/zeromq/udp/etc. interfaces to the API if needed
      without changing this code.

    - Unit testability.

    API functions must do the following:

    - Return a list.

    - Include a ``**kwargs`` argument.

    - Cope with string-only arguments.

    - Raise :py:class:`APIException` if anything goes wrong.

"""

import re
from datetime import datetime, date, timedelta

import redis
from redisbayes import RedisBayes
from django.conf import settings
from django.contrib import auth
from django.core.cache import cache
from django.core.validators import email_re
from django.contrib.gis.geos import Polygon
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from occupywallst import models as db
from occupywallst.templatetags.ows import synopsis
from occupywallst.utils import APIException, timesince


REDBAY = RedisBayes(redis.Redis())


def _str_to_bbox(val):
    swlat, swlng, nwlat, nwlng = [float(s) for s in val.split(',')]
    return Polygon.from_bbox([swlng, swlat, nwlng, nwlat])


def _to_bool(val):
    if type(val) is bool:
        return val
    else:
        return (str(val) == "1" or
                str(val).lower() == "true")


def _try_to_get_ip(args):
    if 'request' in args:
        return args['request'].META.get('REMOTE_ADDR', '')
    else:
        return ''


def _too_many_caps(text):
    caps = len(re.sub(r'[^A-Z]', '', text))
    lows = len(re.sub(r'[^a-z]', '', text))
    return (caps + lows >= 8 and caps > lows)


def forumlinks(user, after, count, **kwargs):
    """Used for continuous stream of forum post links"""
    after, count = int(after), int(count)
    if after < 0 or count <= 0:
        raise APIException(_("bad arguments"))
    articles = (db.Article.objects_as(user)
                .select_related("author", "author__userinfo")
                .order_by('-killed'))
    for article in articles[after:after + count]:
        yield render_to_string('occupywallst/forumpost_synopsis.html',
                               {'article': article,
                                'user': user})


def commentfeed(user, after, count, **kwargs):
    """Used for continuous stream of forum comments"""
    ip = _try_to_get_ip(kwargs)
    after, count = int(after), int(count)
    if after < 0 or count <= 0:
        raise APIException(_("bad arguments"))
    comments = (db.Comment.objects_as(user)
                .select_related("article", "user", "user__userinfo")
                .order_by('-published'))[after:after + count + 10]
    comments = db.mangle_comments(comments, user, ip)
    for comment in comments[:count]:
        yield render_to_string('occupywallst/comment.html',
                               {'comment': comment,
                                'user': user,
                                'can_reply': True,
                                'extended': True})


def attendees(bounds, **kwargs):
    """Find all people going who live within visible map area"""
    if bounds:
        bbox = _str_to_bbox(bounds)
        qset = (db.UserInfo.objects
                .select_related("user")
                .filter(position__isnull=False,
                        position__within=bbox))
    else:
        qset = (db.UserInfo.objects
                .select_related("user")
                .filter(position__isnull=False))
    for userinfo in qset[:1000]:
        yield {'id': userinfo.user.id,
               'username': userinfo.user.username,
               'position': userinfo.position_latlng}


def rides(bounds=None, **kwargs):
    """Find all rides within visible map area"""
    if bounds:
        bbox = _str_to_bbox(bounds)
        qset = (db.Ride.objects
                .filter(route__isnull=False,
                        route__bboverlaps=bbox,
                        depart_time__gte=date.today()))
    else:
        qset = (db.Ride.objects
                .filter(route__isnull=False))
    for ride in qset:
        yield {'id': ride.id,
               'route': ride.route}


def ride_request_update(request_id, status, user=None, **kwargs):
    ride_request = (db.RideRequest.objects.filter(id=request_id)
                    .select_related("ride", "ride__user"))
    try:
        req = ride_request[0]
    except IndexError:
        raise APIException(_("request not found"))
    if req.ride.user == user:
        req.status = status
        req.save()
        return [{"id": req.id, "status": req.status}]
    else:
        raise APIException(_("insufficient permissions"))


def attendee_info(username, **kwargs):
    """Get information for displaying attendee bubble"""
    user = (db.User.objects
            .select_related("userinfo")
            .get(username=username))
    html = render_to_string('occupywallst/attendee_info.html',
                            {'user': user})
    return [{'id': user.id,
             'username': user.username,
             'info': user.userinfo.info,
             'need_ride': user.userinfo.need_ride,
             'location': user.userinfo.position_latlng,
             'html': html}]


def _check_post(user, post):
    """Ensure user-submitted forum content is kosher"""
    if user.userinfo.can_moderate():
        return
    if len(post.content) < 3:
        raise APIException(_("content too short"))
    if len(post.content) > 10 * 1024:
        raise APIException(_("content too long"))
    if ((len(post.content) < 8 and 'bump' in post.content.lower()) or
        (len(post.content) < 5 and '+1' in post.content.lower())):
        raise APIException(_("please don't bump threads"))
    if _too_many_caps(post.content):
        raise APIException(_("turn off bloody caps lock"))
    if hasattr(post, 'title'):
        if len(post.title) < 3:
            raise APIException(_("title too short"))
        if len(post.title) > 128:
            raise APIException(_("title too long"))
        if _too_many_caps(post.title):
            raise APIException(_("turn off bloody caps lock"))
        if db.SpamText.is_spam(post.title):
            post.is_removed = True
        if 'watch' in re.sub('[^a-z]', '', post.title.lower()):
            post.is_removed = True
        if 'episode' in re.sub('[^a-z]', '', post.title.lower()):
            post.is_removed = True
        if 'streaming' in re.sub('[^a-z]', '', post.title.lower()):
            post.is_removed = True
        if 'download' in re.sub('[^a-z]', '', post.title.lower()):
            post.is_removed = True
        if re.match(r's\d\de\d\d', post.title.lower()):
            post.is_removed = True
        if ' HD ' in post.title:
            post.is_removed = True
    if db.SpamText.is_spam(post.content):
        post.is_removed = True
    if post.is_removed:
        _train(post)
    if user.userinfo.is_shadow_banned:
        post.is_removed = True
    try:
        bclass = REDBAY.classify(post.full_text())
    except redis.ConnectionError:
        bclass = 'good'
    if bclass == 'bad' and user.userinfo.karma < settings.OWS_KARMA_THRESHOLD:
        post.is_removed = True


def _limiter(last, seconds):
    limit = timedelta(seconds=seconds)
    since = (datetime.now() - last)
    if since < limit:
        raise APIException(
            _("please wait %(duration)s before making another post") % {
                "duration": timesince(datetime.now() - limit + since)})


def article_new(user, title, content, is_forum, **kwargs):
    """Create a news article or forum thread

    We mustn't allow users without staff privileges to post news
    articles.
    """
    is_forum = _to_bool(is_forum)
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    if not is_forum:
        if not user.is_staff:
            raise APIException(_("insufficient privileges"))
    title = title.strip()
    content = content.strip()
    slug = slugify(title)[:50]
    if db.Article.objects.filter(slug=slug).count():
        raise APIException(_("a thread with this title exists"))
    if not settings.DEBUG and not user.is_staff:
        last = user.article_set.order_by('-published')[:1]
        if last:
            _limiter(last[0].published, settings.OWS_LIMIT_THREAD)
        ip = _try_to_get_ip(kwargs)
        if ip:
            last = cache.get('api_article_new_' + ip)
            if last:
                _limiter(last, settings.OWS_LIMIT_THREAD)
    article = db.Article()
    article.author = user
    article.published = datetime.now()
    article.is_visible = True
    article.title = title
    article.slug = slug
    article.content = content
    article.is_forum = is_forum
    article.ip = _try_to_get_ip(kwargs)
    _check_post(user, article)
    article.save()
    return article_get(user, slug)


def _check_modify_article(user, article):
    """Ensure user have permission to modify an article

    Normal users can only edit their own forum posts.  Moderators can edit all
    forum posts; however, only staff/admin users can edit news articles and
    articles that have been flagged to allow html.
    """
    if not user.is_staff:
        if not article.is_forum or article.allow_html:
            raise APIException(_("insufficient privileges"))
    if not user.userinfo.can_moderate():
        if article.author != user:
            raise APIException(_("you didn't post that"))
    if user.userinfo.can_moderate() and not user.is_staff:
        if article.author.is_staff:
            raise APIException(_("insufficient privileges"))


def _check_modify_comment(user, comment, mods_only=False):
    """Ensure user have permission to modify an comment

    Normal users can only edit their own comments.  Moderators and staff can
    modify all comments.
    """
    if not user.userinfo.can_moderate():
        if comment.user != user:
            raise APIException(_("you didn't post that"))
    if user.userinfo.can_moderate() and not user.is_staff:
        if comment.user.is_staff:
            raise APIException(_("insufficient privileges"))


def shadowban(user, username, action, **kwargs):
    """Ban a user through nefarious means"""
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    if not user.userinfo.can_moderate():
        raise APIException(_("insufficient permissions"))
    try:
        user2 = db.User.objects.get(username=username)
    except db.User.DoesNotExist:
        raise APIException(_("user not found"))
    if user2.userinfo.can_moderate():
        raise APIException(_("cannot ban privileged users"))
    if action == 'ban':
        if not user2.userinfo.is_shadow_banned:
            user2.userinfo.is_shadow_banned = True
    elif action == 'unban':
        if user2.userinfo.is_shadow_banned:
            user2.userinfo.is_shadow_banned = False
    else:
        raise APIException(_("invalid action"))
    user2.userinfo.save()
    return []


def article_edit(user, article_slug, title, content, **kwargs):
    """Edit an article or forum post

    We mustn't allow users without staff privileges to edit an article
    once it's been flagged to allow HTML or converted to a news
    article.
    """
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    title = title.strip()
    content = content.strip()
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException(_("article not found"))
    _check_modify_article(user, article)
    article.title = title
    article.content = content
    _check_post(user, article)
    article.save()
    return article_get(user, article_slug)


def article_delete(user, article_slug, **kwargs):
    """Delete an article or forum post

    This doesn't actually delete but rather clears the auther, title
    and content fields and sets is_visible to False.  It isn't
    possible to clear the slug field because it'd break hyperlinks.
    Commenting is still possible if you have the hyperlink to the
    article saved.  To fully delete an article you must go in the
    backend.

    We mustn't allow users without staff privileges to edit an article
    once it's been converted to a news article.
    """
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException(_("article not found"))
    _check_modify_article(user, article)
    article.author = None
    article.title = "[DELETED]"
    article.content = "[DELETED]"
    article.is_visible = False
    article.save()
    return []


def _train(obj, user=None):
    """Train bayesian spam filter that stuff like this is spam"""
    if user and not user.userinfo.can_moderate():
        return
    try:
        REDBAY.train('bad', obj.full_text())
    except redis.ConnectionError:
        pass


def _untrain(obj, user=None):
    """Undo previous spam training and train to think this is good"""
    if user and not user.userinfo.can_moderate():
        return
    try:
        REDBAY.untrain('bad', obj.full_text())
        REDBAY.train('good', obj.full_text())
    except redis.ConnectionError:
        pass


def article_remove(user, article_slug, action, **kwargs):
    """Makes an article unlisted and invisible to search engines"""
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    if not user.userinfo.can_moderate():
        raise APIException(_("insufficient permissions"))
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException(_("article not found"))
    _check_modify_article(user, article)
    if action == 'remove' and article.is_visible:
        _train(article, user)
        article.is_visible = False
    elif action == 'unremove' and not article.is_visible:
        _untrain(article, user)
        article.is_visible = True
    else:
        raise APIException(_("invalid action"))
    article.save()
    return []


def article_get(user, article_slug=None, read_more=False, **kwargs):
    """Get article information"""
    read_more = _to_bool(read_more)
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException(_("article not found"))
    html = render_to_string('occupywallst/article_content.html',
                            {'article': article,
                             'user': user,
                             'read_more': read_more})
    return [article.as_dict({'html': html})]


def article_get_comments(user, article_slug=None, **kwargs):
    """Get all comments for an article"""
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
        comments = article.comment_set.all()
        return [comment.as_dict() for comment in comments]
    except db.Article.DoesNotExist:
        raise APIException(_("article not found"))


def article_get_comment_votes(user, article_slug=None, **kwargs):
    """Get all votes for all comments for an article"""
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
        votes = db.CommentVote.objects.filter(
            comment__in=article.comment_set.all())
        return [vote.as_dict() for vote in votes]
    except db.Article.DoesNotExist:
        raise APIException(_("article not found"))


def comment_new(user, article_slug, parent_id, content, **kwargs):
    """Leave a comment on an article

    If parent_id is set, this will be a reply to an existing comment.

    Also upvotes comment and increments article comment count.
    """
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    content = content.strip()
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException(_('article not found'))

    def comment_depth(id):
        depth = 0
        current = id
        while current:
            current = comhash.get(current, 0).parent_id
            depth += 1
        return depth

    if parent_id:
        other_comments = (db.Comment.objects
                    .select_related("article")
                    .filter(article=article, is_deleted=False))
        comhash = dict((c.id, c) for c in other_comments)
        parent = comhash[int(parent_id)]
        if int(parent_id) not in comhash:
            raise APIException(_("parent comment not found"))
        if comment_depth(int(parent_id)) + 1 > settings.OWS_MAX_COMMENT_DEPTH:
            raise APIException(_("comment nested too deep"))
    else:
        parent = None
        parent_id = None

    if not settings.DEBUG and not user.is_staff:
        last = user.comment_set.order_by('-published')[:1]
        if last:
            _limiter(last[0].published, settings.OWS_LIMIT_COMMENT)
        ip = _try_to_get_ip(kwargs)
        if ip:
            last = cache.get('api_comment_new_' + ip)
            if last:
                _limiter(last, settings.OWS_LIMIT_COMMENT)

    comment = db.Comment()
    comment.article = article
    username = user.username
    comment.user = user
    comment.content = content
    comment.parent_id = parent_id
    comment.ip = _try_to_get_ip(kwargs)
    _check_post(user, comment)
    comment.save()
    comment_vote(user, comment, "up", **kwargs)
    if not comment.is_removed:
        article.comment_count += 1
        article.killed = datetime.now()
    article.save()
    if not comment.is_removed:
        if parent:
            db.Notification.send(
                parent.user, comment.get_absolute_url(),
                '%s replied to your comment: %s' % (
                    username, synopsis(parent.content, 7)))
        else:
            db.Notification.send(
                article.author, comment.get_absolute_url(),
                '%s replied to your post: %s' % (
                    username, synopsis(article.content, 7)))
    return comment_get(user, comment.id)


def comment_get(user, comment_id=None, **kwargs):
    """Fetch a single comment information"""
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException(_("comment not found"))
    comment.upvoted = False
    comment.downvoted = False
    if user and user.id:
        try:
            vote = db.CommentVote.objects.get(comment=comment, user=user)
        except db.CommentVote.DoesNotExist:
            vote = None
        if vote:
            if vote.vote == 1:
                comment.upvoted = True
            elif vote.vote == -1:
                comment.downvoted = True
    html = render_to_string('occupywallst/comment.html',
                            {'comment': comment,
                             'user': user,
                             'can_reply': True})
    return [comment.as_dict({'html': html})]


def comment_edit(user, comment_id, content, **kwargs):
    """Edit a comment's content"""
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    content = content.strip()
    if len(content) < 3:
        raise APIException(_("comment too short"))
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException(_("comment not found"))
    _check_modify_comment(user, comment)
    comment.content = content
    _check_post(user, comment)
    comment.save()
    return comment_get(user, comment.id)


def comment_remove(user, comment_id, action, **kwargs):
    """Allows moderator to remove a comment"""
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    if not user.userinfo.can_moderate():
        raise APIException(_("insufficient permissions"))
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException(_("comment not found"))
    _check_modify_comment(user, comment)
    if action == 'remove' and not comment.is_removed:
        _train(comment, user)
        comment.is_removed = True
        comment.article.comment_count -= 1
    elif action == 'unremove' and comment.is_removed:
        _untrain(comment, user)
        comment.is_removed = False
        comment.article.comment_count += 1
    else:
        raise APIException(_("invalid action"))
    comment.save()
    comment.article.save()
    return []


def comment_delete(user, comment_id, **kwargs):
    """Delete a comment

    Also decrements article comment count.
    """
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException(_("comment not found"))
    _check_modify_comment(user, comment)
    comment.article.comment_count -= 1
    comment.article.save()
    comment.delete()
    return []


def comment_vote(user, comment, vote, **kwargs):
    """Increases comment karma by one

    If a user is logged in, we track their votes in the database.

    If a user is not logged in, we still allow them to vote but to
    prevent them from clicking the downvote arrow repeatedly we only
    allow an IP to vote once.  We track these votes in a
    non-persistant cache because we don't want to log IP addresses.
    """
    if not (user and user.id):
        raise APIException(_("not logged in"))
    if not isinstance(comment, db.Comment):
        try:
            comment = db.Comment.objects.get(id=comment, is_deleted=False)
        except db.Comment.DoesNotExist:
            raise APIException(_("comment not found"))
    if not settings.DEBUG and not user.is_staff:
        for tdelta, maxvotes in settings.OWS_LIMIT_VOTES:
            votes = (db.CommentVote.objects
                     .filter(user=user, time__gt=datetime.now() - tdelta)
                     .count())
            if votes > maxvotes:
                raise APIException(_("you're voting too much"))
    if not user.userinfo.is_shadow_banned:
        if vote == "up":
            comment.upvote(user)
        elif vote == "down":
            comment.downvote(user)
        else:
            raise APIException(_("invalid vote"))
    return []


def comment_upvote(user, comment, **kwargs):
    """Upvotes a comment"""
    return comment_vote(user, comment, "up", **kwargs)


def comment_downvote(user, comment, **kwargs):
    """Downvotes a comment"""
    return comment_vote(user, comment, "down", **kwargs)


def message_send(user, to_username, content, **kwargs):
    """Send a private message"""
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    content = content.strip()
    if len(content) < 3:
        raise APIException(_("message too short"))
    try:
        to_user = db.User.objects.get(username=to_username, is_active=True)
    except db.User.DoesNotExist:
        raise APIException(_('user not found'))
    if user == to_user:
        raise APIException(_("you can't message yourself"))
    if not user.is_staff:
        hours24 = datetime.now() - timedelta(hours=24)
        rec = db.Message.objects.filter(from_user=user, published__gt=hours24)
        sentusers = set(m.to_user.username for m in rec)
        if len(sentusers) > settings.OWS_LIMIT_MSG_DAY:
            raise APIException(
                _("you can't send more than %(limit)s messages per day") % {
                    "limit": settings.OWS_LIMIT_MSG_DAY})
    msg = db.Message.objects.create(from_user=user,
                                    to_user=to_user,
                                    content=content)
    db.Notification.send(
        to_user, user.get_absolute_url(),
        _("%(username)s sent you a message" % {"username": user.username}))
    html = render_to_string('occupywallst/message.html', {'message': msg})
    return [msg.as_dict({'html': html})]


def message_delete(user, message_id, **kwargs):
    """Delete a message

    Both the sender and the receiver are able to delete messages.
    """
    if not (user and user.id):
        raise APIException(_("you're not logged in"))
    try:
        msg = db.Message.objects.get(id=message_id, is_deleted=False)
    except db.Message.DoesNotExist:
        raise APIException(_("message not found"))
    if user != msg.to_user and user != msg.from_user:
        raise APIException(_("you didn't send or receive that message"))
    msg.delete()
    return []


def carousel_get(user, carousel_id=None, **kwargs):
    """Fetch a list of photos in a carousel"""
    try:
        carousel = db.Carousel.objects.get(id=carousel_id)
    except db.Carousel.DoesNotExist:
        raise APIException(_("carousel not found"))
    return [photo.as_dict() for photo in carousel.photo_set.all()]


def check_username(username, check_if_taken=True, **kwargs):
    """Check if a username is valid and available"""
    if len(username) < 3:
        raise APIException(_("username too short"))
    if len(username) > 30:
        raise APIException(_("username too long"))
    if not re.match(r'[a-zA-Z0-9]{3,30}', username):
        raise APIException(_("bad username, use only letters/numbers"))
    if check_if_taken:
        if db.User.objects.filter(username__iexact=username).count():
            raise APIException(_("username is taken"))
    return []


def signup(request, username, password, email, **kwargs):
    """Create a new account

    - Username must have only letters/numbers and be 3-30 chars
    - Password must be 6-128 chars
    - Email is optional
    """
    raise APIException("disabled")
    if request.user.is_authenticated():
        raise APIException(_("you're already logged in"))
    check_username(username=username)
    if len(password) < 6:
        raise APIException(_("password must be at least six characters"))
    if len(password) > 128:
        raise APIException(_("password too long"))
    if email:
        if not email_re.match(email):
            raise APIException(_("invalid email address"))
    user = db.User()
    user.username = username
    user.set_password(password)
    user.email = email
    user.save()
    userinfo = db.UserInfo()
    userinfo.user = user
    userinfo.attendance = 'maybe'
    userinfo.save()
    user.userinfo = userinfo
    user.save()
    res = login(request, username, password)
    res[0]['conversion'] = render_to_string('occupywallst/conversion.html')
    return res


def login(request, username, password, **kwargs):
    """Login user"""
    if request.user.is_authenticated():
        logout(request)
    user = auth.authenticate(username=username, password=password)
    if not user:
        raise APIException(_("invalid username or password"))
    auth.login(request, user)
    return [user.userinfo.as_dict()]


def logout(request, **kwargs):
    """Logout user"""
    auth.logout(request)
    return []
