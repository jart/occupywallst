
var article_init;

$.fn.numberAdd = function (delta) {
    this.each(function () {
        $(this).text(parseInt($(this).text()) + delta);
    });
};

(function() {
    "use strict";

    var replyform;
    var penguin = 50;

    function init() {
        replyform = $(".replyform");
        init_postform($(".postform"), $("#comment-list"), "");
        $(".comment").each(function(i) {
            init_comment($(this));
        });
    }

    function init_postform(form, container, parent_id) {
        $(".save", form).click(function() {
            $(".loader", form).show();
            $(".error", form).text("");
            api("/api/comment/new/", {
                "article_slug": $("article").attr("id"),
                "parent_id": parent_id,
                "content": $("textarea", form).val()
            }, function(data) {
                $(".loader", form).hide();
                if (data.status == "OK") {
                    var res = data.results[0];
                    var comment = $(res.html);
                    init_comment(comment);
                    comment.hide();
                    container.prepend(comment);
                    comment.fadeIn();
                    $("#comment-count").numberAdd(+1);
                    $("textarea", form).val("");
                    if (!form.is(".postform"))
                        form.remove();
                } else {
                    $(".error", form).text(data.message);
                }
            }).error(function(err) {
                $(".loader", form).hide();
                $(".error", form).text(err.status + ' ' + err.statusText);
            });
            return false;
        });
        $(".cancel", form).click(function() {
            form.slideUp(penguin, function() {
                form.remove();
            });
            return false;
        });
    }

    function init_comment(comment) {
        var comment_id = comment.attr("id").split("-")[1];
        var content = $("> .content", comment);
        var replies = $("> .replies", comment);

        $(".reply", content).click(function() {
            if ($(".replyform", content).length)
                return false;
            var form = replyform.clone();
            content.append(form);
            form.slideDown(penguin, function() {
                $("textarea", form).focus();
            });
            init_postform(form, replies, comment_id);
            return false;
        });

        $(".up", content).click(function() {
            if ($(".up", content).hasClass("upvoted"))
                return false;
            api("/api/comment/vote/", {
                "comment_id": comment_id,
                "vote": "up"
            }, function(data) {
            });
            if ($(".down", content).hasClass("downvoted")) {
                $(".karma", content).numberAdd(+2);
                $(".ups", content).numberAdd(+1);
                $(".downs", content).numberAdd(-1);
            } else {
                $(".karma", content).numberAdd(+1);
                $(".ups", content).numberAdd(+1);
            }
            $(".up", content).addClass("upvoted");
            $(".down", content).removeClass("downvoted");
            return false;
        });

        $(".down", content).click(function() {
            if ($(".up", content).hasClass("downvoted"))
                return false;
            api("/api/comment/vote/", {
                "comment_id": comment_id,
                "vote": "down"
            }, function(data) {
            });
            if ($(".up", content).hasClass("upvoted")) {
                $(".karma", content).numberAdd(-2);
                $(".ups", content).numberAdd(-1);
                $(".downs", content).numberAdd(+1);
            } else {
                $(".karma", content).numberAdd(-1);
                $(".downs", content).numberAdd(+1);
            }
            $(".up", content).removeClass("upvoted");
            $(".down", content).addClass("downvoted");
            return false;
        });

        $(".delete", content).click(function() {
            if (!confirm("Sure you want to delete this comment?"))
                return false;
            api("/api/comment/delete/", {
                "comment_id": comment_id
            }, function(data) {
                if (data.status == "OK") {
                    comment.remove();
                    $("#comment-count").numberAdd(-1);
                } else {
                    alert(data.message);
                }
            });
            return false;
        });

        $(".remove", content).click(function() {
            var action = $(".remove", content).text();
            api("/api/comment/remove/", {
                "comment_id": comment_id,
                "action": action
            }, function(data) {
                if (data.status == "OK") {
                    if (action == "remove") {
                        content.addClass("removed");
                        $(".remove", content).text("unremove");
                        $("#comment-count").numberAdd(-1);
                    } else {
                        content.removeClass("removed");
                        $(".remove", content).text("remove");
                        $("#comment-count").numberAdd(+1);
                    }
                } else {
                    alert(data.message);
                }
            });
            return false;
        });
    }

    // export stuff
    article_init = init;

})();
