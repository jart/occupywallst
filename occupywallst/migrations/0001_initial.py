# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Verbiage'
        db.create_table('occupywallst_verbiage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('use_markdown', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('use_template', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('occupywallst', ['Verbiage'])

        # Adding model 'VerbiageTranslation'
        db.create_table('occupywallst_verbiagetranslation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('verbiage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='translations', to=orm['occupywallst.Verbiage'])),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('occupywallst', ['VerbiageTranslation'])

        # Adding unique constraint on 'VerbiageTranslation', fields ['verbiage', 'language']
        db.create_unique('occupywallst_verbiagetranslation', ['verbiage_id', 'language'])

        # Adding model 'UserInfo'
        db.create_table('occupywallst_userinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('info', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('need_ride', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('attendance', self.gf('django.db.models.fields.CharField')(default='maybe', max_length=32)),
            ('notify_message', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('notify_news', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('position', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True, blank=True)),
            ('formatted_address', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('zipcode', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
        ))
        db.send_create_signal('occupywallst', ['UserInfo'])

        # Adding model 'Notification'
        db.create_table('occupywallst_notification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('published', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('is_read', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('url', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('occupywallst', ['Notification'])

        # Adding model 'Article'
        db.create_table('occupywallst_article', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('published', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('killed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('comment_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('allow_html', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_visible', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_forum', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('occupywallst', ['Article'])

        # Adding model 'ArticleTranslation'
        db.create_table('occupywallst_articletranslation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['occupywallst.Article'])),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('occupywallst', ['ArticleTranslation'])

        # Adding unique constraint on 'ArticleTranslation', fields ['article', 'language']
        db.create_unique('occupywallst_articletranslation', ['article_id', 'language'])

        # Adding model 'Comment'
        db.create_table('occupywallst_comment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['occupywallst.Article'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('published', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('ups', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('downs', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('karma', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('is_removed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('occupywallst', ['Comment'])

        # Adding model 'CommentVote'
        db.create_table('occupywallst_commentvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('comment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['occupywallst.Comment'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('vote', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('occupywallst', ['CommentVote'])

        # Adding unique constraint on 'CommentVote', fields ['comment', 'user']
        db.create_unique('occupywallst_commentvote', ['comment_id', 'user_id'])

        # Adding model 'Message'
        db.create_table('occupywallst_message', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='messages_sent', to=orm['auth.User'])),
            ('to_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='messages_recv', to=orm['auth.User'])),
            ('published', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_read', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('occupywallst', ['Message'])

        # Adding model 'Ride'
        db.create_table('occupywallst_ride', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('published', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ridetype', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('depart_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('seats_total', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('waypoints', self.gf('django.db.models.fields.TextField')()),
            ('route', self.gf('django.contrib.gis.db.models.fields.LineStringField')(default=None, null=True)),
            ('route_data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('info', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('occupywallst', ['Ride'])

        # Adding unique constraint on 'Ride', fields ['user', 'title']
        db.create_unique('occupywallst_ride', ['user_id', 'title'])

        # Adding model 'RideRequest'
        db.create_table('occupywallst_riderequest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ride', self.gf('django.db.models.fields.related.ForeignKey')(related_name='requests', to=orm['occupywallst.Ride'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=32)),
            ('info', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('occupywallst', ['RideRequest'])

        # Adding unique constraint on 'RideRequest', fields ['ride', 'user']
        db.create_unique('occupywallst_riderequest', ['ride_id', 'user_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'RideRequest', fields ['ride', 'user']
        db.delete_unique('occupywallst_riderequest', ['ride_id', 'user_id'])

        # Removing unique constraint on 'Ride', fields ['user', 'title']
        db.delete_unique('occupywallst_ride', ['user_id', 'title'])

        # Removing unique constraint on 'CommentVote', fields ['comment', 'user']
        db.delete_unique('occupywallst_commentvote', ['comment_id', 'user_id'])

        # Removing unique constraint on 'ArticleTranslation', fields ['article', 'language']
        db.delete_unique('occupywallst_articletranslation', ['article_id', 'language'])

        # Removing unique constraint on 'VerbiageTranslation', fields ['verbiage', 'language']
        db.delete_unique('occupywallst_verbiagetranslation', ['verbiage_id', 'language'])

        # Deleting model 'Verbiage'
        db.delete_table('occupywallst_verbiage')

        # Deleting model 'VerbiageTranslation'
        db.delete_table('occupywallst_verbiagetranslation')

        # Deleting model 'UserInfo'
        db.delete_table('occupywallst_userinfo')

        # Deleting model 'Notification'
        db.delete_table('occupywallst_notification')

        # Deleting model 'Article'
        db.delete_table('occupywallst_article')

        # Deleting model 'ArticleTranslation'
        db.delete_table('occupywallst_articletranslation')

        # Deleting model 'Comment'
        db.delete_table('occupywallst_comment')

        # Deleting model 'CommentVote'
        db.delete_table('occupywallst_commentvote')

        # Deleting model 'Message'
        db.delete_table('occupywallst_message')

        # Deleting model 'Ride'
        db.delete_table('occupywallst_ride')

        # Deleting model 'RideRequest'
        db.delete_table('occupywallst_riderequest')


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
        'occupywallst.article': {
            'Meta': {'object_name': 'Article'},
            'allow_html': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'comment_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_forum': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'killed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'occupywallst.articletranslation': {
            'Meta': {'unique_together': "(('article', 'language'),)", 'object_name': 'ArticleTranslation'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['occupywallst.Article']"}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'occupywallst.comment': {
            'Meta': {'object_name': 'Comment'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['occupywallst.Article']"}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'downs': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_removed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'karma': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'parent_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ups': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'occupywallst.commentvote': {
            'Meta': {'unique_together': "(('comment', 'user'),)", 'object_name': 'CommentVote'},
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['occupywallst.Comment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'vote': ('django.db.models.fields.IntegerField', [], {})
        },
        'occupywallst.message': {
            'Meta': {'object_name': 'Message'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages_sent'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages_recv'", 'to': "orm['auth.User']"})
        },
        'occupywallst.notification': {
            'Meta': {'object_name': 'Notification'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'published': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'occupywallst.ride': {
            'Meta': {'unique_together': "(('user', 'title'),)", 'object_name': 'Ride'},
            'depart_time': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ridetype': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'route': ('django.contrib.gis.db.models.fields.LineStringField', [], {'default': 'None', 'null': 'True'}),
            'route_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'seats_total': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'waypoints': ('django.db.models.fields.TextField', [], {})
        },
        'occupywallst.riderequest': {
            'Meta': {'unique_together': "(('ride', 'user'),)", 'object_name': 'RideRequest'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ride': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requests'", 'to': "orm['occupywallst.Ride']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'occupywallst.userinfo': {
            'Meta': {'object_name': 'UserInfo'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'attendance': ('django.db.models.fields.CharField', [], {'default': "'maybe'", 'max_length': '32'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'formatted_address': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'need_ride': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notify_message': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'notify_news': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'position': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'})
        },
        'occupywallst.verbiage': {
            'Meta': {'object_name': 'Verbiage'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'use_markdown': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'use_template': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'occupywallst.verbiagetranslation': {
            'Meta': {'unique_together': "(('verbiage', 'language'),)", 'object_name': 'VerbiageTranslation'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'verbiage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'translations'", 'to': "orm['occupywallst.Verbiage']"})
        }
    }

    complete_apps = ['occupywallst']
