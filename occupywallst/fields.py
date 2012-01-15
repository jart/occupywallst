r"""

    occupywallst.fields
    ~~~~~~~~~~~~~~~~~~~

    Form fields and stuff

"""

from django import forms
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from recaptcha.client import captcha

from occupywallst import widgets


class ReCaptchaField(forms.CharField):
    default_error_messages = {
        'captcha_invalid': _(u'Invalid captcha'),
    }

    def __init__(self, *args, **kwargs):
        self.widget = widgets.ReCaptchaWidget
        self.required = False
        super(ReCaptchaField, self).__init__(*args, **kwargs)

    def clean(self, values):
        super(ReCaptchaField, self).clean(values[1])
        challenge = smart_unicode(values[0])
        response = smart_unicode(values[1])
        ip = smart_unicode(values[2])
        key = settings.RECAPTCHA_PRIVATE_KEY
        res = captcha.submit(challenge, response, key, ip)
        if not res.is_valid:
            raise forms.util.ValidationError(
                self.error_messages['captcha_invalid'])
        return challenge
