from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
from recaptcha.client import captcha

class ReCaptcha(forms.widgets.Widget):
    recaptcha_challenge_name = 'recaptcha_challenge_field'
    recaptcha_response_name = 'recaptcha_response_field'

    def render(self, name, value, attrs=None):
        return mark_safe(u'%s' % captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY))

    def value_from_datadict(self, data, files, name):
        return [data.get(self.recaptcha_challenge_name, None), 
            data.get(self.recaptcha_response_name, None)]

class ImageWidget(forms.widgets.FileInput):
    """
    A FileInput that displays an image and a copyable link instead of a file path
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
        output.append('<td>%s</td></tr>'%img)
        output.append('<tr><td></td><td><input type="text" size="60" value="%s"></td></tr>'%url)
        output.append('<tr><td>Change:</td><td>')
        output.append(super(ImageWidget, self).render(name, value, attrs))
        output.append('</td></tr></table>')
        return mark_safe(u''.join(output))
