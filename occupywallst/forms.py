r"""

    occupywallst.forms
    ~~~~~~~~~~~~~~~~~~

    HTML form definitions.

"""

from django import forms
from django.forms.models import modelformset_factory

from occupywallst import models as db
from occupywallst.fields import ReCaptchaField


class ProfileForm(forms.Form):
    email = forms.EmailField(required=False, help_text="""
        We won't show it on the site or share it with anyone""")
    notify_message = forms.BooleanField(required=False, initial=True,
                                        label="Message Notifications",
                                        help_text="""
        Do you want to receive an email notification when you receive a
        private message or a comment response?""")
    notify_news = forms.BooleanField(required=False, initial=True,
                                     label="News Notifications",
                                     help_text="""
        Can we email you notifications about news relating to the protest?""")
    info = forms.CharField(required=False, widget=forms.Textarea,
                           help_text="""
        Say whatever you want about yourself here for others
        to see.""")
    position_lat = forms.FloatField(required=False, widget=forms.HiddenInput)
    position_lng = forms.FloatField(required=False, widget=forms.HiddenInput)
    formatted_address = forms.CharField(required=False,
                                         widget=forms.HiddenInput)
    country = forms.CharField(required=False, widget=forms.HiddenInput)
    region = forms.CharField(required=False, widget=forms.HiddenInput)
    city = forms.CharField(required=False, widget=forms.HiddenInput)
    address = forms.CharField(required=False, widget=forms.HiddenInput)
    zipcode = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        if user:
            initial = {'email': user.email,
                       'info': user.userinfo.info,
                       'notify_news': user.userinfo.notify_news,
                       'notify_message': user.userinfo.notify_message,
                       'position_lat': user.userinfo.position_lat,
                       'position_lng': user.userinfo.position_lng,
                       'country': user.userinfo.country,
                       'region': user.userinfo.region,
                       'city': user.userinfo.city,
                       'address': user.userinfo.address,
                       'zipcode': user.userinfo.zipcode}
        else:
            initial = {}
        initial.update(kwargs.get('initial', {}))
        kwargs['initial'] = initial
        super(ProfileForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(ProfileForm, self).clean()
        return self.cleaned_data

    def save(self):
        user = self.user
        ui = user.userinfo
        ui.info = self.cleaned_data.get('info')
        ui.notify_message = self.cleaned_data.get('notify_message')
        ui.notify_news = self.cleaned_data.get('notify_news')
        position_lat = self.cleaned_data.get('position_lat')
        position_lng = self.cleaned_data.get('position_lng')
        if position_lat is not None and position_lng is not None:
            ui.position_latlng = position_lat, position_lng
        else:
            ui.position = None
        ui.formatted_address = self.cleaned_data.get('formatted_address')
        ui.country = self.cleaned_data.get('country')
        ui.region = self.cleaned_data.get('region')
        ui.city = self.cleaned_data.get('city')
        ui.address = self.cleaned_data.get('address')
        ui.zipcode = self.cleaned_data.get('zipcode')
        ui.save()
        user.email = self.cleaned_data.get('email')
        user.save()
        return user


class SignupForm(ProfileForm):
    username = forms.RegexField(
        label="Username", max_length=30, regex=r'^[a-zA-Z0-9]{3,30}$',
        help_text="Required. Letters and digits only and 3-30 characters.",
        error_messages={'invalid': ("Please enter letters and digits only.  "
                                    "Minimum 3 characters and max 30.")})
    password = forms.CharField(label="Password", widget=forms.PasswordInput,
                               min_length=6, max_length=128,
                               help_text="At least 6 characters")
    captcha = ReCaptchaField()

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(None, *args, **kwargs)

    def clean_username(self):
        username = self.data.get('username')
        if db.User.objects.filter(username__iexact=username).count():
            raise forms.ValidationError("Username is taken")
        return username

    def save(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = db.User()
        user.username = username
        user.set_password(password)
        user.save()
        userinfo = db.UserInfo()
        userinfo.user = user
        userinfo.attendance = 'maybe'
        userinfo.save()
        user.userinfo = userinfo
        user.save()
        self.user = user
        return super(SignupForm, self).save()


class RideForm(forms.ModelForm):
    class Meta:
        model = db.Ride
        exclude = ['seats_used', 'route', 'route_data', 'forum_post']


class RideRequestForm(forms.Form):
    info = forms.CharField(help_text="Want a seat? Tell us about yourself.",
            widget=forms.widgets.Textarea)
    def save(self, user, ride):
        ride_request = db.RideRequest(user=user,ride=ride)
        ride_request.status = "pending"
        ride_request.info = self.cleaned_data['info']
        ride_request.save()
        return ride_request


class SubscribeForm(forms.Form):
    email = forms.EmailField()
