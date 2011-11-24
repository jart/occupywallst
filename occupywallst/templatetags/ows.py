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
from django.utils.translation import ugettext
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
pat_comment = re.compile(r'<!--.*?-->', re.S)
pat_header = re.compile(r'<(/?)h\d>', re.S)
pat_img = re.compile(r'<img[^>]>', re.S)
pat_mortify = [
    re.compile(r'(.*?)<!-- ?more ?-->', re.I | re.S),
    re.compile(r'<!-- ?begin synopsis ?-->(.+?)<!-- ?end synopsis ?-->',
               re.I | re.S),
]

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
    """
    Creates a shortened version of content

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


def mortify(text, url, funk):
    """
    Extracts specified synopsis in markdown article

    There are two ways to specify a synopsis:

    1. Put "<!-- more -->" somewhere in the article.  The synopsis
       will start at the beginning and end there.

    2. Wrap any particular portion text between "<!-- begin synopsis -->" and
       "<!-- end synopsis -->" tags.

    """
    readmore = ugettext('[Read More...](%(url)s)') % {'url': url}
    for pat in pat_mortify:
        mat = pat.search(text)
        if mat:
            res = mat.group(1) + ' ' + readmore
            break
    else:
        res = text
    return funk(res)


@register.filter
def not_more(text, arg):
    return mortify(text, arg, markup)
not_more.is_safe = True


@register.filter
def not_more_unsafe(text, arg):
    return mortify(text, arg, markup_unsafe)
not_more_unsafe.is_safe = True


def _markup(text, transform):
    text = pat_url.sub(r'<\1>', text)
    text = pat_url_www.sub(r'[\1](http://\1)', text)
    text = pat_comment.sub('', text)
    html = transform(text)
    html = html.replace('src="/media/', 'src="' + settings.MEDIA_URL)
    return mark_safe(html)


@register.filter
def markup(text):
    """Runs text through markdown, no html allowed
    """
    return _markup(text, markdown_safe.convert)
markup.is_safe = True


@register.filter
def strip_annoying_html(html):
    html = pat_header.sub(r'<\1p>', html)
    html = pat_img.sub('', html)
    return mark_safe(html)
strip_annoying_html.is_safe = True


@register.filter
def markup_unsafe(text):
    """Runs text through markdown allowing custom html
    """
    return _markup(text, markdown_unsafe.convert)
markup_unsafe.is_safe = True


@register.filter
def userlink(user):
    """
    Display a username in HTML with a link to their profile
    """
    if not user or not user.id:
        return ugettext('anonymous')
    res = ugettext('<a title="View %(user)s\'s profile" class="user"'
                   ' href="%(url)s">%(user)s</a>') % {
        'user': user.username, 'url': user.get_absolute_url()}
    return mark_safe(res)
userlink.is_safe = True


@register.simple_tag
def translate_object(obj, lang):
    """
    If possible, replaces certain fields with translated text
    """
    if obj:
        obj.translate(lang)
    return ''


@register.simple_tag(takes_context=True)
def show_comments(context, user, comments):
    """
    I wrote this because template includes don't recurse properly
    """
    res = []
    depth = context.get('depth', -1) + 1
    can_reply = depth + 1 < settings.OWS_MAX_COMMENT_DEPTH
    for comment in comments:
        if not comment.is_removed or user.is_staff:
            res.append(render_to_string('occupywallst/comment.html',
                                        {'comment': comment,
                                         'user': user,
                                         'depth': depth,
                                         'can_reply': can_reply}))
    return "".join(res)
