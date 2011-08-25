r"""

    occupywallst.templatetags.ows
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    We're gonna do what Django templates say can't be done.

"""

import re
import markdown

from django import template
from django.utils.safestring import mark_safe
from django.template import Template, Context
from django.template.loader import render_to_string

from occupywallst import utils

register = template.Library()

tr_template = Template(u'''
  <tr id="row_{{ field.name }}" class="field">
    <th>{{ field.label_tag }}</th>
    <td>{% if field.errors %}{{ field.errors }}{% endif %}{{ field }}<br />
        <span class="helptext">{{ field.help_text|safe }}</span></td>
  </tr>
''')

pat_url = re.compile(r'(?<![<\(\[])(https?://[^\s\'\"\]\)]+)', re.I)
pat_url_www = re.compile(r'(?<!\S)(www\.[-a-z]+\.[-.a-z]+)', re.I)
markdown_safe = markdown.Markdown(safe_mode='escape')
markdown_unsafe = markdown.Markdown()


@register.filter
def as_tr(field):
    if field and field.field:  # should be a BoundField (not a Field)
        return mark_safe(tr_template.render(Context({'field': field})))
    else:
        return ''


@register.filter
def jsonify(value):
    return mark_safe(utils.jsonify(value))


@register.filter
def timesince_short(timestamp):
    return utils.timesince(timestamp)


@register.filter
def markup(text):
    text = pat_url.sub(r'<\1>', text)
    text = pat_url_www.sub(r'[\1](http://\1)', text)
    return mark_safe(markdown_safe.convert(' %s ' % text))


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
