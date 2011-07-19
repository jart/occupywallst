r"""

    occupywallst.api
    ~~~~~~~~~~~~~~~~

    Ajax data providers.

    They just return plain old python data and have nothing to do with
    the HTTP request/response logic.  To make these functions return
    something like JSON we use middleware decorators (such as
    ``api_view()``) which are specified in the ``urls.py`` file.

"""

from datetime import datetime

from django.conf import settings
from django.contrib.gis.geos import Polygon
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
        qset = db.UserInfo.objects.filter(position__isnull=False,
                                          position__within=bbox)
    else:
        qset = db.UserInfo.objects.filter(position__isnull=False)
    for userinfo in qset[:100]:
        yield {'id': userinfo.user.id,
               'username': userinfo.user.username,
               'position': userinfo.position_latlng}


def attendee_info(username, **kwargs):
    """Get information about a user
    """
    user = db.User.objects.get(username=username)
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


def comment_new(user, article_slug, parent_id, content, **kwargs):
    """Leave a comment on an article

    If ``parent_id != "null"``, this will be a reply to an existing
    comment.

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
    if parent_id != "null":
        try:
            parent = db.Comment.objects.get(id=parent_id,
                                            is_deleted=False,
                                            article=article)
        except db.Comment.DoesNotExist:
            raise APIException("parent comment not found")
    else:
        parent_id = None
    if not settings.DEBUG:
        lastcom = user.comment_set.order_by('-published')[:1]
        if lastcom:
            if (datetime.now() - lastcom[0].published).seconds < 60:
                raise APIException("you're doing that too fast")
    com = db.Comment.objects.create(article=article,
                                    user=user,
                                    content=content,
                                    parent_id=parent_id)
    com.upvote(user)
    article.comment_count += 1
    article.save()
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
    yield com.as_dict()


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
    if action == 'remove':
        com.is_removed = True
        com.article.comment_count -= 1
    elif action == 'unremove':
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
