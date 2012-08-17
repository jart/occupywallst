# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Ride'
        db.create_table('rideshare_ride', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ride_direction', self.gf('django.db.models.fields.CharField')(default='round', max_length=32)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('published', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ridetype', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('depart_time', self.gf('django.db.models.fields.DateTimeField')(default='2012-05-15')),
            ('return_time', self.gf('django.db.models.fields.DateTimeField')(default='2012-05-22')),
            ('seats_total', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('waypoints', self.gf('django.db.models.fields.TextField')()),
            ('waypoints_points', self.gf('django.contrib.gis.db.models.fields.LineStringField')(default=None, null=True)),
            ('route', self.gf('django.contrib.gis.db.models.fields.LineStringField')(default=None, null=True)),
            ('route_data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('info', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('rideshare', ['Ride'])

        # Adding unique constraint on 'Ride', fields ['user', 'title']
        db.create_unique('rideshare_ride', ['user_id', 'title'])

        # Adding model 'RideRequest'
        db.create_table('rideshare_riderequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ride', self.gf('django.db.models.fields.related.ForeignKey')(related_name='requests', to=orm['rideshare.Ride'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=32)),
            ('ride_direction', self.gf('django.db.models.fields.CharField')(default='round', max_length=32)),
            ('info', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('seats_wanted', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('rendezvous', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True, blank=True)),
            ('rendezvous_address', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('rideshare', ['RideRequest'])

        # Adding unique constraint on 'RideRequest', fields ['ride', 'user']
        db.create_unique('rideshare_riderequest', ['ride_id', 'user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'RideRequest', fields ['ride', 'user']
        db.delete_unique('rideshare_riderequest', ['ride_id', 'user_id'])

        # Removing unique constraint on 'Ride', fields ['user', 'title']
        db.delete_unique('rideshare_ride', ['user_id', 'title'])

        # Deleting model 'Ride'
        db.delete_table('rideshare_ride')

        # Deleting model 'RideRequest'
        db.delete_table('rideshare_riderequest')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rideshare.ride': {
            'Meta': {'unique_together': "(('user', 'title'),)", 'object_name': 'Ride'},
            'depart_time': ('django.db.models.fields.DateTimeField', [], {'default': "'2012-05-15'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'return_time': ('django.db.models.fields.DateTimeField', [], {'default': "'2012-05-22'"}),
            'ride_direction': ('django.db.models.fields.CharField', [], {'default': "'round'", 'max_length': '32'}),
            'ridetype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'route': ('django.contrib.gis.db.models.fields.LineStringField', [], {'default': 'None', 'null': 'True'}),
            'route_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'seats_total': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'waypoints': ('django.db.models.fields.TextField', [], {}),
            'waypoints_points': ('django.contrib.gis.db.models.fields.LineStringField', [], {'default': 'None', 'null': 'True'})
        },
        'rideshare.riderequest': {
            'Meta': {'unique_together': "(('ride', 'user'),)", 'object_name': 'RideRequest'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rendezvous': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'rendezvous_address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ride': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requests'", 'to': "orm['rideshare.Ride']"}),
            'ride_direction': ('django.db.models.fields.CharField', [], {'default': "'round'", 'max_length': '32'}),
            'seats_wanted': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['rideshare']