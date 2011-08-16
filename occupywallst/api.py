r"""

    occupywallst.api
    ~~~~~~~~~~~~~~~~

    AJAX Remote Procedure Calls.

    They just return plain old python data and have nothing to do with
    the HTTP request/response logic.  To make these functions return
    something like JSON we use middleware decorators (such as
    ``api_view()``) which are specified in the ``urls.py`` file.

"""

from datetime import datetime

from django.conf import settings
from django.utils.text import truncate_words
from django.contrib.gis.geos import Polygon
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from occupywallst import models as db
from occupywallst.utils import APIException


def str_to_bbox(val):
    swlat, swlng, nwlat, nwlng = [float(s) for s in val.split(',')]
    return Polygon.from_bbox([swlng, swlat, nwlng, nwlat])


def attendees(bounds, **kwargs):
    """Find all people going who live within visible map area.
    """
    if bounds:
        bbox = str_to_bbox(bounds)
        qset = (db.UserInfo.objects
                .select_related("user")
                .filter(position__isnull=False,
                        position__within=bbox))
    else:
        qset = (db.UserInfo.objects
                .select_related("user")
                .filter(position__isnull=False))
    for userinfo in qset[:100]:
        yield {'id': userinfo.user.id,
               'username': userinfo.user.username,
               'position': userinfo.position_latlng}


def attendee_info(username, **kwargs):
    """Get information about a user
    """
    user = (db.User.objects
            .select_related("userinfo")
            .get(username=username))
    html = render_to_string('occupywallst/attendee_info.html',
                            {'user': user})
    yield {'id': user.id,
           'username': user.username,
           'info': user.userinfo.info,
           'need_ride': user.userinfo.need_ride,
           'location': user.userinfo.position_latlng,
           'html': html}


def _render_comment(comment, user):
    comment.upvoted = False
    comment.downvoted = False
    try:
        vote = db.CommentVote.objects.get(comment=comment, user=user)
    except db.CommentVote.DoesNotExist:
        vote = None
    if vote:
        if vote.vote == 1:
            comment.upvoted = True
        elif vote.vote == -1:
            comment.downvoted = True
    return render_to_string('occupywallst/comment.html',
                            {'comment': comment,
                             'user': user})


def thread_new(user, title, content, **kwargs):
    """Create a new thread on the message board forum.
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    if len(title) < 4:
        raise APIException("title too short")
    if len(title) > 255:
        raise APIException("title too long")
    slug = slugify(title)[:50]
    if db.Article.objects.filter(slug=slug).count():
        raise APIException("a thread with this title has already been posted")
    if not settings.DEBUG and not user.is_staff:
        last = user.article_set.order_by('-published')[:1]
        if last:
            limit = settings.OWS_POST_LIMIT_THREAD
            since = (datetime.now() - last[0].published).seconds
            if since < limit:
                raise APIException("please wait %d seconds before making "
                                   "another post" % (limit - since))
    thread = db.Article()
    thread.published = datetime.now()
    thread.is_forum = True
    thread.is_visible = True
    thread.author = user
    thread.title = title
    thread.slug = slug
    thread.content = content
    thread.save()
    yield thread.as_dict()


def comment_new(user, article_slug, parent_id, content, **kwargs):
    """Leave a comment on an article

    If parent_id is set, this will be a reply to an existing comment.

    Also upvotes comment and increments article comment count.
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    content = content.strip()
    if len(content) < 5:
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
        last = user.comment_set.order_by('-published')[:1]
        if last:
            limit = settings.OWS_POST_LIMIT_COMMENT
            since = (datetime.now() - last[0].published).seconds
            if since < limit:
                raise APIException("please wait %d seconds before making "
                                   "another post" % (limit - since))
    com = db.Comment.objects.create(article=article,
                                    user=user,
                                    content=content,
                                    parent_id=parent_id)
    com.upvote(user)
    article.comment_count += 1
    article.save()
    if parent:
        db.Notification.send(parent.user, parent.get_absolute_url(),
                             '%s replied to your comment: %s'
                             % (user.username,
                                truncate_words(parent.content, 7)))
    yield com.as_dict({'html': _render_comment(com, user)})


def comment_get(user, comment_id, **kwargs):
    """Fetch a single comment information
    """
    try:
        com = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    yield com.as_dict({'html': _render_comment(com, user)})


def comment_edit(user, comment_id, content, **kwargs):
    """Edit a comment's content
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    content = content.strip()
    if len(content) < 5:
        raise APIException("comment too short")
    try:
        com = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    if com.user != user:
        raise APIException("you didn't post that comment")
    com.content = content
    com.save()
    yield com.as_dict({'html': _render_comment(com, user)})


def comment_remove(user, comment_id, action, **kwargs):
    """Allows moderator to remove a comment
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    if not user.is_staff:
        raise APIException("insufficient vespene gas")
    try:
        com = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    if action == 'remove' and not com.is_removed:
        com.is_removed = True
        com.article.comment_count -= 1
    elif action == 'unremove' and com.is_removed:
        com.is_removed = False
        com.article.comment_count += 1
    else:
        raise APIException("invalid action")
    com.save()
    com.article.save()
    yield None


def comment_delete(user, comment_id, **kwargs):
    """Delete a comment

    Also decrements article comment count.
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    try:
        com = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    if com.user != user:
        raise APIException("you didn't post that comment")
    com.article.comment_count -= 1
    com.article.save()
    com.delete()
    yield None


def comment_vote(user, comment_id, vote, **kwargs):
    """Increases comment karma by one
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    try:
        com = db.Comment.objects.get(id=comment_id, is_deleted=False)
    except db.Comment.DoesNotExist:
        raise APIException("comment not found")
    if vote == "up":
        com.upvote(user)
    elif vote == "down":
        com.downvote(user)
    else:
        raise APIException("invalid vote")
    yield None


def message_send(user, to_username, content, **kwargs):
    """Send a private message.
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    content = content.strip()
    if len(content) < 5:
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
    yield msg.as_dict({'html': render_to_string('occupywallst/message.html',
                                                {'message': msg})})


def message_delete(user, message_id, **kwargs):
    """Delete a message

    Both the sender and the receiver are able to delete messages.
    """
    if not user.is_authenticated():
        raise APIException("you're not logged in")
    try:
        msg = db.Message.objects.get(id=message_id, is_deleted=False)
    except db.Message.DoesNotExist:
        raise APIException("message not found")
    if user != msg.to_user and user != msg.from_user:
        raise APIException("you didn't send or receive that message")
    msg.delete()
    yield None
