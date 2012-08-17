r"""

    rideshare.forms
    ~~~~~~~~~~~~~~~~~~

    HTML form definitions.

"""

from django import forms

from rideshare import models as db


class RideForm(forms.ModelForm):
    class Meta:
        model = db.Ride
        fields = ('title', 'info', 'ridetype', 'seats_total',
                  'ride_direction', 'depart_time', 'return_time',
                  'start_address', 'end_address', 'waypoints',
                  'waypoints_points')
        exclude = ['published', 'seats_used', 'route', 'route_data',
                   'forum_post', 'waypoints_points']

    start_address = forms.CharField(required=True)
    end_address = forms.CharField(required=True)
    waypoints = forms.CharField(
        required=False, widget=forms.Textarea, help_text="""
        Add other adresses or destinations separated by newlines to make
        you route more accurate""")
    waypoints_points_wkt = forms.CharField(
        required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(RideForm, self).__init__(*args, **kwargs)
        self.fields['seats_total'].label = "Seats available"
        self.fields['waypoints'].label = "Waypoints(optional)"
        self.fields['info'].label = "Ride Description"

        if 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']
            #pdb.set_trace()
            self.initial['waypoints_points_wkt'] = instance.waypoints_points
            self.initial['start_address'] = instance.waypoint_list[0]
            self.initial['end_address'] = instance.waypoint_list[-1]
            self.initial['waypoints'] = '\n'.join(instance.waypoint_list[1:-1])

    def save(self, commit=True):
        from django.contrib.gis.geos import GEOSGeometry
        model = super(RideForm, self).save(commit=False)

        points = GEOSGeometry(self.cleaned_data['waypoints_points_wkt'])
        #pdb.set_trace()
        model.waypoints_points = points

        if self.cleaned_data['waypoints'] != '':
            self.cleaned_data['waypoints'] = \
                self.cleaned_data['waypoints'] + '\n'
        model.waypoints = (self.cleaned_data['start_address'] + "\n" +
                           self.cleaned_data['waypoints'] +
                           self.cleaned_data['end_address'])
        if commit:
            model.save()
        return model


class RideRequestForm(forms.ModelForm):
    class Meta:
        model = db.RideRequest
        exclude = ('rendezvous', 'user', 'status')

    rendezvous_lat = forms.FloatField(
        required=False, widget=forms.HiddenInput)
    rendezvous_lng = forms.FloatField(
        required=False, widget=forms.HiddenInput)
    rendezvous_address = forms.CharField(
        required=False, widget=forms.HiddenInput)
    seats_wanted = forms.IntegerField(
        required=False, widget=forms.Select)

    # Override the constructor to manually set the form's latitude and
    # longitude fields if a Location instance is passed into the form
    def __init__(self, *args, **kwargs):
        super(RideRequestForm, self).__init__(*args, **kwargs)
        # Set the form fields based on the model object
        if 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']
            self.initial['rendezvous_lat'] = instance.rendezvous_lat
            self.initial['rendezvous_lng'] = instance.rendezvous_lng

    def save(self, commit=True):
        #commit = kwargs.pop('commit', True)
        model = super(RideRequestForm, self).save(commit=False)
        # Save the latitude and longitude based on the form fields
        model.rendezvous_latlng = (self.cleaned_data['rendezvous_lng'],
                                   self.cleaned_data['rendezvous_lat'])
        if commit:
            model.save()
        return model
