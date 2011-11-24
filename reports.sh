#!/bin/bash
#
# i generate text file reports to help you track down abuse.  it's a
# good idea to have them generated to a secret folder on your
# webserver.
#
# to use me run "crontab -e" and add:
#
# @hourly     nice reports.sh ows /var/www/reports
#

DB=$1
DEST=$2
THRESHOLD=$3

[[ $DB ]] || exit 1
[[ -d $DEST ]] || exit 1
[[ $THRESHOLD ]] || THRESHOLD=20

for HOURS in 1 4 12 24 48; do
cat <<EOF | psql $DB >$DEST/voting-${HOURS}hours.txt
select (select username from auth_user where id = uid) as name,
       vote_count,
       (select count(*)
          from occupywallst_article
         where author_id = uid) as article_count_all_time,
       (select count(*)
          from occupywallst_comment
         where user_id = uid) as comment_count_all_time
  from (select user_id as uid, count(*) as vote_count
          from occupywallst_commentvote
         where time > now() - interval '$HOURS hour'
         group by uid
         order by vote_count desc) as A
 where vote_count > $THRESHOLD;
EOF
done
