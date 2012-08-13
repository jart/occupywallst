#!/bin/bash
#
# i recalculate counter fields in database to ensure their
# correctness.  sometimes stuff like comment karma can get out of sync
# if users are purged from the database or a software bug occurs.
# this script should be run periodically to fix that.
#
# to use me run "crontab -e" and add:
#
# @hourly     nice recalculate.sh ows
#

DB=$1
[[ $DB ]] || exit 1

cat <<EOF | psql -q $DB

update occupywallst_comment as C
   set ups = coalesce((select count(*)
                         from occupywallst_commentvote as CV
                   inner join occupywallst_userinfo as UI 
                           on CV.user_id = UI.user_id
                        where comment_id = C.id
                          and is_shadow_banned = false
                          and vote = 1), 0),
       downs = coalesce((select count(*)
                           from occupywallst_commentvote as CV
                     inner join occupywallst_userinfo as UI 
                             on CV.user_id = UI.user_id
                          where comment_id = C.id
                            and is_shadow_banned = false
                            and vote = -1), 0),
       karma = coalesce((select sum(vote)
                           from occupywallst_commentvote as CV
                     inner join occupywallst_userinfo as UI 
                             on CV.user_id = UI.user_id
                          where comment_id = C.id
                            and is_shadow_banned = false), 0)
 where published > now() - interval '30 day';

update occupywallst_userinfo as U
   set karma = coalesce((select sum(karma)
                           from occupywallst_comment as C
                          where C.user_id = U.user_id
                            and not is_removed
                            and not is_deleted), 0)
 where U.user_id in (select distinct(user_id)
                       from occupywallst_comment 
                      where published > now() - interval '30 day');

EOF
