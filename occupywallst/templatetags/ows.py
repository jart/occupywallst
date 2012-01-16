r"""

    occupywallst.templatetags.ows
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    We're gonna do what Django templates say can't be done.

"""

import re
import pytz
import hashlib
import datetime
import markdown

from django import template
from django.conf import settings
from django.core.cache import cache
from django.utils.html import strip_tags
from django.template import Template, Context
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.template.loader import render_to_string

from occupywallst import utils

try:
    import GeoIP
except ImportError:
    GEO = None
else:
    GEO = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)


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
pat_img = re.compile(r'<img[^>]*>', re.S)
pat_readmore = [
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
def synopsis(text, max_words=10, max_chars=None):
    """Turns large markdown text into a short plain-text description

    First we try to extract a manually specified synopsis (see
    :py:func:`read_more()`).  If that doesn't work then we extract the
    first paragraph.  Markdown quotations are excluded unless the
    whole thing is a quote.

    The result will be truncated after ``max_words``.  ``max_chars``
    is a fail-safe in case there are super long words.  It defaults to
    ``max_words * (5 + 1)`` because five is the average number of
    letters in English words.  If ``max_chars <= 0`` then this feature
    is disabled.

    Then we strip html tags, run it through markdown, strip html again
    and turn html entities back into plain text.  The result should be
    considered unsafe.
    """
    key = hashlib.sha256(text.encode('utf8')).hexdigest()
    res = cache.get(key)
    if res is not None:
        return res
    for pat in pat_readmore:
        mat = pat.search(text)
        if mat:
            res = mat.group(1)
            break
    else:
        lines = text.split('\n')
        no_quotes = [s for s in lines if not s.startswith('>')]
        res = "\n".join(no_quotes).strip()
        if not res:
            return 'BLANK'
        paragraphs = res.split('\n\n')
        res = paragraphs[0]
    res = unicode(strip_tags(markup(strip_tags(res)))
                  .replace('&gt;', '>')
                  .replace('&lt;', '<')
                  .replace('&amp;', '&')
                  .replace('&quot;', '"'))
    words = res.split()
    res = " ".join(words[:max_words])
    if max_chars is None:
        max_chars = max_words * 6
    if max_chars > 0:
        res = res[:max_chars]
    cache.set(key, res, 60 * 60)
    return res


@register.filter
def read_more(text, url=None):
    """Extracts shortened version of markdown article (for "read more")

    If ``url`` is specified, a "Read More" hyperlink will be appended
    to the returned string, if and only if the synopsis was manually
    specified.

    There are two ways to specify a synopsis:

    1. Put ``<!-- more -->`` somewhere in the article.  The synopsis
       will start at the beginning and end there.

    2. Wrap any particular portion text between ``<!-- begin synopsis -->``
       and ``<!-- end synopsis -->`` tags.

    """
    for pat in pat_readmore:
        mat = pat.search(text)
        if mat:
            res = mat.group(1)
            if url:
                res += ' ' + ugettext('[Read More...](%(url)s)') % {'url': url}
            break
    else:
        res = text
    return res


@register.filter
def strip_annoying_html(html):
    html = pat_header.sub(r'<\1p>', html)
    html = pat_img.sub('', html)
    return mark_safe(html)
strip_annoying_html.is_safe = True


def _markup(text, convert):
    """Turn markdown text into HTML with additional hacks

    - HTML comments are removed.

    - Angle brackets are added around hyperlinks to make them
      clickable because otherwise no one would know to do this.

    - Any images that start with ``/media/`` will be rewritten to use
      ``settings.MEDIA_URL``.  This is so we don't have to specify the
      CDN address when writing articles.

    """
    text = pat_url.sub(r'<\1>', text)
    text = pat_url_www.sub(r'[\1](http://\1)', text)
    text = pat_comment.sub('', text)
    html = convert(text)
    html = html.replace('src="/media/', 'src="' + settings.MEDIA_URL)
    return mark_safe(html)


@register.filter
def markup(text):
    """Runs text through markdown, no html allowed"""
    return _markup(text, markdown_safe.convert)
markup.is_safe = True


@register.filter
def markup_unsafe(text):
    """Runs text through markdown, html allowed"""
    return _markup(text, markdown_unsafe.convert)
markup_unsafe.is_safe = True


@register.filter
def userlink(user):
    """Display a username in HTML with a link to their profile"""
    if not user or not user.id:
        return ugettext('anonymous')
    res = ugettext('<a title="View %(user)s\'s profile" class="user"'
                   ' href="%(url)s">%(user)s</a>') % {
        'user': user.username, 'url': user.get_absolute_url()}
    return mark_safe(res)
userlink.is_safe = True


@register.filter
def nofollow(html):
    return mark_safe(html.replace('<a ', '<a rel="nofollow" '))
nofollow.is_safe = True


@register.filter
def ipcountry(ip):
    if GEO:
        return GEO.country_code_by_addr(ip) or ''
    else:
        return ''


@register.simple_tag
def translate_object(obj, lang):
    """If possible, replaces certain fields with translated text"""
    if obj:
        obj.translate(lang)
    return ''


@register.simple_tag(takes_context=True)
def show_comments(context, user, comments):
    """I wrote this because template includes don't recurse properly"""
    res = []
    depth = context.get('depth', -1) + 1
    can_reply = depth + 1 < settings.OWS_MAX_COMMENT_DEPTH
    is_mod = (user and user.id and user.userinfo.can_moderate())
    for comment in comments:
        if not comment.is_removed or is_mod:
            res.append(render_to_string('occupywallst/comment.html',
                                        {'comment': comment,
                                         'user': user,
                                         'depth': depth,
                                         'can_reply': can_reply}))
    return "".join(res)
