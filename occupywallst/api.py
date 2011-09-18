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
from datetime import datetime

from django.conf import settings
from django.contrib import auth
from django.core.cache import cache
from django.utils.text import truncate_words
from django.core.validators import email_re
from django.contrib.gis.geos import Polygon
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from occupywallst import models as db
from occupywallst.utils import APIException


def _str_to_bbox(val):
    swlat, swlng, nwlat, nwlng = [float(s) for s in val.split(',')]
    return Polygon.from_bbox([swlng, swlat, nwlng, nwlat])


def _to_bool(val):
    if type(val) is bool:
        return val
    else:
        return (str(val) == "1" or
                str(val).lower() == "true")


def attendees(bounds, **kwargs):
    """Find all people going who live within visible map area.
    """
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
    for userinfo in qset:
        yield {'id': userinfo.user.id,
               'username': userinfo.user.username,
               'position': userinfo.position_latlng}


def attendee_info(username, **kwargs):
    """Get information for displaying attendee bubble
    """
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


def article_new(user, title, content, is_forum, **kwargs):
    """Create a news article or forum thread

    We mustn't allow users without staff privileges to post news
    articles.
    """
    is_forum = _to_bool(is_forum)
    # if not (user and user.id):
    #     raise APIException("anonymous posts disabled. please sign up for an account")
    if not is_forum:
        if not (user and user.id) or not user.is_staff:
            raise APIException("insufficient privileges")
    if len(title) < 3:
        raise APIException("title too short")
    if len(title) > 255:
        raise APIException("title too long")
    slug = slugify(title)[:50]
    if db.Article.objects.filter(slug=slug).count():
        raise APIException("a thread with this title exists")
    if not settings.DEBUG and user and user.id and not user.is_staff:
        last = user.article_set.order_by('-published')[:1]
        if last:
            limit = settings.OWS_POST_LIMIT_THREAD
            since = (datetime.now() - last[0].published).seconds
            if since < limit:
                raise APIException("please wait %d seconds before making "
                                   "another post" % (limit - since))
    article = db.Article()
    if user and user.id:
        article.author = user
    article.published = datetime.now()
    article.is_visible = True
    article.title = title
    article.slug = slug
    article.content = content
    article.is_forum = is_forum
    article.save()
    return article_get(user, slug)


def article_edit(user, article_slug, content, **kwargs):
    """Edit an article or forum post

    We mustn't allow users without staff privileges to edit an article
    once it's been flagged to allow HTML or converted to a news
    article.
    """
    if not (user and user.id):
        raise APIException("you're not logged in")
    content = content.strip()
    if len(content) < 3:
        raise APIException("article too short")
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException("article not found")
    if article.author != user:
        raise APIException("you didn't post that")
    if not user.is_staff:
        if article.allow_html or not article.is_forum:
            raise APIException("insufficient privileges")
    article.content = content
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
        raise APIException("you're not logged in")
    try:
        article = db.Article.objects.get(slug=article_slug, is_visible=True,
                                         is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException("article not found")
    if article.author != user:
        raise APIException("you didn't post that")
    if not user.is_staff:
        if not article.is_forum:
            raise APIException("insufficient privileges")
    article.author = None
    article.title = "[DELETED]"
    article.content = "[DELETED]"
    article.is_visible = False
    article.save()
    return []


def article_get(user, article_slug, **kwargs):
    """Get article information
    """
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException("article not found")
    html = render_to_string('occupywallst/article_content.html',
                            {'article': article,
                             'user': user})
    return [article.as_dict({'html': html})]


def comment_new(user, article_slug, parent_id, content, **kwargs):
    """Leave a comment on an article

    If parent_id is set, this will be a reply to an existing comment.

    Also upvotes comment and increments article comment count.
    """
    # if not (user and user.id):
    #     raise APIException("anonymous posts disabled. please sign up for an account")
    content = content.strip()
    if len(content) < 3:
        raise APIException("comment too short")
    try:
        article = db.Article.objects.get(slug=article_slug, is_deleted=False)
    except db.Article.DoesNotExist:
        raise APIException('article not found')
    if parent_id:
        try:
            parent = db.Comment.objects.get(id=parent_id,
                                            is_deleted=False,
                                            article=article)
        except db.Comment.DoesNotExist:
            raise APIException("parent comment not found")
    else:
        parent = None
        parent_id = None
    if not settings.DEBUG:
        last = None
        if user and user.id:
            if not user.is_staff:
                qset = user.comment_set.order_by('-published')
                try:
                    last = qset[1]
                except IndexError:
                    pass
        else:
            last = db.Comment.objects.order_by('-published')[:1]
        if last:
            limit = settings.OWS_POST_LIMIT_COMMENT
            since = (datetime.now() - last[0].published).seconds
            if since < limit:
                raise APIException("please wait %d seconds before making "
                                   "another post" % (limit - since))
    comment = db.Comment()
    comment.article = article
    if user and user.id:
        username = user.username
        comment.user = user
    else:
        username = 'anonymous'
    comment.content = content
    comment.parent_id = parent_id
    comment.save()
    comment_vote(user, comment, "up", **kwargs)
    article.comment_count += 1
    article.save()
    if parent:
        db.Notification.send(parent.user, comment.get_absolute_url(),
                             '%s replied to your comment: %s'
                             % (username, truncate_words(parent.content, 7)))
    else:
        db.Notification.send(article.author, comment.get_absolute_url(),
                             '%s replied to your post: %s'
                             % (username, truncate_words(article.content, 7)))
    return comment_get(user, comment.id)


def comment_get(user, comment_id, **kwargs):
    """Fetch a single comment information
    """
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
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
                             'user': user})
    return [comment.as_dict({'html': html})]


def comment_edit(user, comment_id, content, **kwargs):
    """Edit a comment's content
    """
    if not (user and user.id):
        raise APIException("you're not logged in")
    content = content.strip()
    if len(content) < 3:
        raise APIException("comment too short")
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    if comment.user != user:
        raise APIException("you didn't post that comment")
    comment.content = content
    comment.save()
    return comment_get(user, comment.id)


def comment_remove(user, comment_id, action, **kwargs):
    """Allows moderator to remove a comment
    """
    if not (user and user.id):
        raise APIException("you're not logged in")
    if not user.is_staff:
        raise APIException("insufficient vespene gas")
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    if action == 'remove' and not comment.is_removed:
        comment.is_removed = True
        comment.article.comment_count -= 1
    elif action == 'unremove' and comment.is_removed:
        comment.is_removed = False
        comment.article.comment_count += 1
    else:
        raise APIException("invalid action")
    comment.save()
    comment.article.save()
    return []


def comment_delete(user, comment_id, **kwargs):
    """Delete a comment

    Also decrements article comment count.
    """
    if not (user and user.id):
        raise APIException("you're not logged in")
    try:
        comment = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    if comment.user != user:
        raise APIException("you didn't post that comment")
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
    if not isinstance(comment, db.Comment):
        try:
            comment = db.Comment.objects.get(id=comment, is_deleted=False)
        except db.Comment.DoesNotExist:
            raise APIException("comment not found")
    if not (user and user.id):
        if 'request' in kwargs:
            ip = kwargs['request'].META['REMOTE_ADDR']
            key = "vote_comment_%s__%s" % (comment.id, ip)
            if cache.get(key, False):
                raise APIException("you already voted")
            else:
                cache.set(key, True)
    if vote == "up":
        comment.upvote(user)
    elif vote == "down":
        comment.downvote(user)
    else:
        raise APIException("invalid vote")
    return []


def comment_upvote(user, comment, **kwargs):
    """Upvotes a comment
    """
    return comment_vote(user, comment, "up", **kwargs)


def comment_downvote(user, comment, **kwargs):
    """Downvotes a comment
    """
    return comment_vote(user, comment, "down", **kwargs)


def message_send(user, to_username, content, **kwargs):
    """Send a private message.
    """
    if not (user and user.id):
        raise APIException("you're not logged in")
    content = content.strip()
    if len(content) < 3:
        raise APIException("message too short")
    try:
        to_user = db.User.objects.get(username=to_username, is_active=True)
    except db.User.DoesNotExist:
        raise APIException('user not found')
    if user == to_user:
        raise APIException("you can't message yourself")
    if not settings.DEBUG:
        last = user.messages_sent.order_by('-published')[:1]
        if last:
            if (datetime.now() - last[0].published).seconds < 30:
                raise APIException("hey slow down a little!")
    msg = db.Message.objects.create(from_user=user,
                                    to_user=to_user,
                                    content=content)
    db.Notification.send(to_user, user.get_absolute_url(),
                         '%s sent you a message' % (user.username))
    html = render_to_string('occupywallst/message.html',
                            {'message': msg})
    return [msg.as_dict({'html': html})]


def message_delete(user, message_id, **kwargs):
    """Delete a message

    Both the sender and the receiver are able to delete messages.
    """
    if not (user and user.id):
        raise APIException("you're not logged in")
    try:
        msg = db.Message.objects.get(id=message_id, is_deleted=False)
    except db.Message.DoesNotExist:
        raise APIException("message not found")
    if user != msg.to_user and user != msg.from_user:
        raise APIException("you didn't send or receive that message")
    msg.delete()
    return []


def check_username(username, check_if_taken=True, **kwargs):
    """Check if a username is valid and available
    """
    if len(username) < 3:
        raise APIException("Username is too short")
    if len(username) > 30:
        raise APIException("Username is too long")
    if not re.match(r'[a-zA-Z0-9]{3,30}', username):
        raise APIException("Bad username, use only letters/numbers")
    if check_if_taken:
        if db.User.objects.filter(username=username).count():
            raise APIException("Username is taken")
    return []


def signup(request, username, password, email, **kwargs):
    """Create a new account

    - Username must have only letters/numbers and be 3-30 chars
    - Password must be 6-128 chars
    - Email is optional
    """
    if request.user.is_authenticated():
        raise APIException("you're already logged in")
    check_username(username=username)
    if len(password) < 6:
        raise APIException("password must be at least six characters")
    if len(password) > 128:
        raise APIException("password too long")
    if email:
        if not email_re.match(email):
            raise APIException("invalid email address")
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
    """Login user
    """
    if request.user.is_authenticated():
        raise APIException("you're already logged in")
    user = auth.authenticate(username=username, password=password)
    if not user:
        raise APIException("invalid username or password")
    auth.login(request, user)
    return [user.userinfo.as_dict()]


def logout(request, **kwargs):
    """Logout user
    """
    auth.logout(request)
    return []
