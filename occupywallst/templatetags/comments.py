r"""

    occupywallst.templatetags.comments
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    We're gonna do what Django templates say can't be done.

"""

import datetime

from django import template
from django.template.loader import render_to_string


register = template.Library()


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
