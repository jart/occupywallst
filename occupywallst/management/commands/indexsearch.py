r"""

    occupywallst.management.commands.indexsearch
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Regenerate whoosh full text search table.

"""

import os
import subprocess

from whoosh import fields, index
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from occupywallst import models as db


class Command(BaseCommand):
    args = ''
    help = __doc__

    def handle(self, *args, **options):
        dst = settings.WHOOSH_ROOT
        tmp = settings.WHOOSH_ROOT + '.tmp'
        tra = settings.WHOOSH_ROOT + '.trash'
        if not os.path.exists(tmp):
            os.mkdir(tmp)

        ix = index.create_in(tmp, fields.Schema(
            id=fields.NUMERIC(stored=True),
            title=fields.TEXT,
            user=fields.TEXT,
            date=fields.DATETIME,
            content=fields.TEXT,
        ))

        writer = ix.writer()
        for post in (db.Article.objects
                     .filter(is_visible=True, is_deleted=False)
                     .order_by('-published')):
            writer.add_document(
                id=post.id,
                date=post.published,
                title=unicode(post.title),
                user=unicode(post.author.username if post.author else ''),
                content="%s %s" % (unicode(post.title), unicode(post.content)),
            )
        writer.commit()

        if os.path.exists(tra):
            subprocess.call(['rm', '-rf', tra])
        if os.path.exists(dst):
            os.rename(dst, tra)
            os.rename(tmp, dst)
            subprocess.call(['rm', '-rf', tra])
        else:
            os.rename(tmp, dst)
