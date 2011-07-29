r"""

    occupywallst.templatetags.occupywallst
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    We're gonna do what Django templates say can't be done.

"""

from datetime import datetime

from django import template
from django.template.loader import render_to_string


register = template.Library()


@register.filter
def timesince_short(timestamp):
    delta = (datetime.now() - timestamp)
    seconds = delta.days * 60 * 60 * 24 + delta.seconds
    if seconds <= 60:
        x = seconds
        s = ('second', 'seconds')
    elif seconds <= 60 * 60:
        x = int(round(seconds / 60.0))
        s = ('minute', 'minutes')
    elif seconds <= 60 * 60 * 24:
        x = int(round(seconds / 60 / 60))
        s = ('hour', 'hours')
    elif seconds <= 60 * 60 * 24 * 30:
        x = int(round(seconds / 60 / 60 / 24))
        s = ('day', 'days')
    else:
        x = int(round(seconds / 60 / 60 / 24 / 30))
        s = ('month', 'months')
    return "%d %s" % (x, s[x != 1])


@register.simple_tag
def show_comments(user, comments):
    """I wrote this because template includes don't recurse properly
    """
    res = []
    for comment in comments:
        if not comment.is_removed or user.is_staff:
            res.append(render_to_string('occupywallst/comment.html',
                                        {'comment': comment,
                                         'user': user}))
    return "".join(res)
