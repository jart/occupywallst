
import re

import sys
sys.exit()

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'occupywallst.settings'

from occupywallst import models as db
from datetime import datetime, timedelta

res = []
for user in set(c.user for c in db.Comment.objects.select_related('user').order_by('-published')[:10000] if c.user):
    comments = user.comment_set.all()[:]
    if len(comments) < 5:
        continue
    span = (max(c.published for c in comments) - min(c.published for c in comments)).seconds
    dups = len(comments) - len(set(c.content for c in comments))
    res.append([user.username, span, len(comments), len(comments) / float(span), dups])
res.sort(key=lambda a: a[4], reverse=True)
for row in res:
    print row
