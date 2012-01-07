r"""

    occupywallst.management.commands.train
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Train spam filter based on recent thread/comment moderation.

"""

import os
import subprocess

from whoosh import fields, index
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from occupywallst import models as db
from occupywallst.api import REDBAY


class Command(BaseCommand):
    args = ''
    help = __doc__

    def handle(self, *args, **options):
        REDBAY.flush()
        for post in (list(db.Article.objects.order_by('-published')[:1000]) +
                     list(db.Comment.objects.order_by('-published')[:2000])):
            bclass = 'bad' if post.is_removed else 'good'
            REDBAY.train(bclass, post.full_text())
