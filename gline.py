import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'occupywallst.settings'
from occupywallst import models as db
for username in sys.argv[1:]:
    print "glining:", username
    user = db.User.objects.get(username=username)
    for ip in set([c.ip for c in user.comment_set.all()]):
        if ip:
            os.system('sudo ufw insert 1 deny from ' + ip)
    user.delete()
