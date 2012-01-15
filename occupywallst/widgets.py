r"""

    occupywallst.widgets
    ~~~~~~~~~~~~~~~~~~~~

    Widgets and stuff

"""

from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
from recaptcha.client import captcha


class ReCaptchaWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        html = captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY)
        return mark_safe(unicode(html))

    def value_from_datadict(self, data, files, name):
        return [data.get('recaptcha_challenge_field', None),
                data.get('recaptcha_response_field', None),
                data.get('recaptcha_magic_ip_field', None)]


class ImageWidget(forms.widgets.FileInput):
    """
    A FileInput that displays an image and a copyable link instead of
    a file path.
    """

    def render(self, name, value, attrs=None):
        # TODO: find the smart way to get the display image url
        if hasattr(value, 'url'):
            url = value.url
            url = url.replace('/photos', '/photos/photos')
            url = url.replace('.png', '_display.png')
            img = '<img src="%s" />' % url
        else:
            url = ''
            img = '(none)'
        output = []
        output.append('<table><tr><td>Currently:</td>')
        output.append('<td>%s</td></tr>' % (img))
        output.append('<tr><td></td><td><input type="text" size="60" '
                      'value="%s"></td></tr>' % (url))
        output.append('<tr><td>Change:</td><td>')
        output.append(super(ImageWidget, self).render(name, value, attrs))
        output.append('</td></tr></table>')
        return mark_safe(u''.join(output))
