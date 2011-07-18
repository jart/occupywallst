r"""

    occupywallst.forms
    ~~~~~~~~~~~~~~~~~~

    HTML form definitions.

"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from occupywallst import models as db


class SignupForm(UserCreationForm):
    attendance = forms.ChoiceField(choices=db.UserInfo.ATTENDANCE_CHOICES,
                                   required=True, help_text="""
        Are you coming to the protest?""")
    email = forms.EmailField(required=False, help_text="""
        Optional.  This won't be shown on the website.""")
    need_ride = forms.BooleanField(required=False, help_text="""
        Optional.  Do you need a lift?  If so check this box to add yourself
        to the map of people looking for a ride.""")
    notify_message = forms.BooleanField(required=False, initial=True,
                                        help_text="""
        Do you want to receive an email notification when you receive a
        private message?""")
    notify_news = forms.BooleanField(required=False, initial=True,
                                     help_text="""
        Can we email you notifications about news relating to the protest?""")
    info = forms.CharField(required=False, widget=forms.Textarea,
                           help_text="""
        Optional.  Say whatever you want about yourself here for others
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

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance')
        if user and user.userinfo:
            initial = {'email': user.email,
                       'info': user.userinfo.info,
                       'need_ride': user.userinfo.need_ride,
                       'attendance': user.userinfo.attendance,
                       'notify_news': user.userinfo.notify_news,
                       'notify_message': user.userinfo.notify_message,
                       'position_lat': user.userinfo.position_lat,
                       'position_lng': user.userinfo.position_lng,
                       'country': user.country,
                       'region': user.region,
                       'city': user.city,
                       'address': user.address,
                       'zipcode': user.zipcode}
        else:
            initial = {}
        initial.update(kwargs.get('initial', {}))
        kwargs['initial'] = initial
        super(SignupForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(SignupForm, self).clean()
        need_ride = self.cleaned_data.get('need_ride')
        position_lat = self.cleaned_data.get('position_lat')
        position_lng = self.cleaned_data.get('position_lng')
        if need_ride and not (position_lat and position_lng):
            raise forms.ValidationError("You can't ask for a ride if you " +
                                        "don't tell us where you're from.")
        return self.cleaned_data

    def save(self):
        user = super(SignupForm, self).save()
        userinfo = db.UserInfo()
        userinfo.user = user
        userinfo.info = self.cleaned_data.get('info')
        userinfo.attendance = self.cleaned_data.get('attendance')
        userinfo.notify_message = self.cleaned_data.get('notify_message')
        userinfo.notify_news = self.cleaned_data.get('notify_news')
        position_lat = self.cleaned_data.get('position_lat')
        position_lng = self.cleaned_data.get('position_lng')
        if position_lat is not None and position_lng is not None:
            userinfo.position_latlng = position_lat, position_lng
        else:
            userinfo.position = None
        userinfo.formatted_address = self.cleaned_data.get('formatted_address')
        userinfo.country = self.cleaned_data.get('country')
        userinfo.region = self.cleaned_data.get('region')
        userinfo.city = self.cleaned_data.get('city')
        userinfo.address = self.cleaned_data.get('address')
        userinfo.zipcode = self.cleaned_data.get('zipcode')
        userinfo.need_ride = self.cleaned_data.get('need_ride')
        userinfo.save()
        user.email = self.cleaned_data.get('email')
        user.userinfo = userinfo
        user.save()
        return user
