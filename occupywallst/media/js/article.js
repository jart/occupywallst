
var article_init;

(function() {
    "use strict";

    function init() {
        $("#comment-post button").click(function() {
            $("#comment-post img").show();
            $("#comment-post span").text("");
            $.getJSON("/api/comment/new/", {
                "article_slug": $("article").attr("id"),
                "content": $("#comment-post textarea").val()
            }, function(data) {
                $("#comment-post img").hide();
                if (data.status == "OK") {
                    var com = data.results[0];
                    $("#comment-list").prepend($(com.html));
                } else {
                    $("#comment-post span").text(data.message);
                }
            }).error(function(e) {
                $("#comment-post img").hide();
                $("#comment-post span").text("oh snap");
            });
            return false;
        });
        $(".comment").each(function(i) {
            var comment = $(this);
            var commentid = comment.attr("id").split("-")[1];
            $(".up", comment).click(function() {
                if ($(".up", comment).hasClass("upvoted"))
                    return;
                $.getJSON("/api/comment/up/", {
                    "commentid": commentid
                }, function(data) {
                });
                if ($(".down", comment).hasClass("downvoted")) {
                    $(".karma", comment).text(
                        parseInt($(".karma", comment).text()) + 2);
                    $(".ups", comment).text(
                        parseInt($(".ups", comment).text()) + 1);
                    $(".downs", comment).text(
                        parseInt($(".downs", comment).text()) - 1);
                } else {
                    $(".karma", comment).text(
                        parseInt($(".karma", comment).text()) + 1);
                    $(".ups", comment).text(
                        parseInt($(".ups", comment).text()) + 1);
                }
                $(".up", comment).addClass("upvoted");
                $(".down", comment).removeClass("downvoted");
                return false;
            });
            $(".down", comment).click(function() {
                if ($(".up", comment).hasClass("downvoted"))
                    return;
                $.getJSON("/api/comment/down/", {
                    "commentid": commentid
                }, function(data) {
                });
                if ($(".up", comment).hasClass("upvoted")) {
                    $(".karma", comment).text(
                        parseInt($(".karma", comment).text()) - 2);
                    $(".ups", comment).text(
                        parseInt($(".ups", comment).text()) - 1);
                    $(".downs", comment).text(
                        parseInt($(".downs", comment).text()) + 1);
                } else {
                    $(".karma", comment).text(
                        parseInt($(".karma", comment).text()) - 1);
                    $(".downs", comment).text(
                        parseInt($(".downs", comment).text()) + 1);
                }
                $(".up", comment).removeClass("upvoted");
                $(".down", comment).addClass("downvoted");
                return false;
            });
        });
    }

    /* export stuff */

    article_init = init;

})();
