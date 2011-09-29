r"""

    occupywallst.templatetags.ows
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    We're gonna do what Django templates say can't be done.

"""

import re
import pytz
import datetime
import markdown

from django import template
from django.conf import settings
from django.utils.html import strip_tags
from django.template import Template, Context
from django.utils.safestring import mark_safe
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

pat_url = re.compile(r'(?<!\S)(https?://[^\s\'\"\]\)]+)', re.I)
pat_url_www = re.compile(r'(?<!\S)(www\.[-a-z]+\.[-.a-z]+)', re.I)
markdown_safe = markdown.Markdown(safe_mode='escape')
markdown_unsafe = markdown.Markdown()


@register.filter
def as_timezone(ts, zone):
    if not isinstance(ts, datetime.datetime):
        return ts
    return ts.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(zone))
as_timezone.is_safe = True


@register.filter
def as_tr(field):
    if field and field.field:  # should be a BoundField (not a Field)
        return mark_safe(tr_template.render(Context({'field': field})))
    else:
        return ''
as_tr.is_safe = True


@register.filter
def jsonify(value):
    return mark_safe(utils.jsonify(value))
jsonify.is_safe = True


@register.filter
def timesince_short(timestamp):
    return utils.timesince(timestamp)
timesince_short.is_safe = True


@register.filter
def synopsis(text, max_words=10, max_chars=40):
    """Creates a shortened version of content

    We only care about the first line.  If the text begins with a
    markdown quotation, it will be excluded unless the whole thing is
    a quote.

    To get rid of markup, we start by stripping html tags.  Then we
    run the result through markup and strip the html tags again.  The
    result is still unsafe of course.
    """
    lines = text.split('\n')
    no_quotes = [s for s in lines if s and not s.startswith('>')]
    if not no_quotes:
        return 'BLANK'
    first_line = unicode(strip_tags(markup(strip_tags(no_quotes[0]))))
    words = first_line.split()
    return " ".join(words[:max_words])[:max_chars]


def _markup(text, transform):
    text = pat_url.sub(r'<\1>', text)
    text = pat_url_www.sub(r'[\1](http://\1)', text)
    html = transform(text)
    # temporary hack to content distribution network
    html = html.replace('src="/media/', 'src="' + settings.MEDIA_URL)
    return mark_safe(html)


@register.filter
def markup(text):
    """Runs text through markdown, no html allowed
    """
    return _markup(text, markdown_safe.convert)
markup.is_safe = True


@register.filter
def markup_unsafe(text):
    """Runs text through markdown allowing custom html
    """
    return _markup(text, markdown_unsafe.convert)
markup_unsafe.is_safe = True  # lol


@register.simple_tag
def translate_object(obj, lang):
    """If possible, replaces certain fields with translated text
    """
    if obj:
        obj.translate(lang)
    return ''


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
