
var article_init;

jQuery.fn.numberAdd = function(delta) {
    this.each(function() {
        jQuery(this).text(parseInt(jQuery(this).text()) + delta);
    });
};

(function() {
    "use strict";

    var penguin = 50;

    function init() {
        init_article($("article"));
        init_comment_form($("#postform"), $("#comment-list"), "");
        $(".comment").each(function(i) {
            init_comment($(this));
        });
        var anchor = $(document.location.hash);
        if (anchor.hasClass("comment")) {
            $("> .content", anchor).addClass("highlight");
        }
    }

    function init_article(article) {
        var slug = article.attr("id");

        $(".edit", article).click(function(ev) {
            ev.preventDefault();
            if ($(".editform", article).length)
                return;
            var form = $("#editform").clone().attr("id", "");
            var old_words;
            form.insertBefore($(".words", article));
            $(".save", form).click(function(ev) {
                ev.preventDefault();
                $(".loader", form).show();
                $(".error", form).text("");
                api("/api/article_edit/", {
                    "article_slug": slug,
                    "content": $("textarea", form).val()
                }, function(data) {
                    $(".loader", form).hide();
                    if (data.status == "OK") {
                        var elem = $(data.results[0].html);
                        article.replaceWith(elem);
                        init_article(elem);
                    } else {
                        $(".error", form).text(data.message);
                    }
                }).error(function(err) {
                    $(".loader", form).hide();
                    $(".error", form).text(err.status + ' ' + err.statusText);
                });
            });
            $(".cancel", form).click(function(ev) {
                ev.preventDefault();
                form.slideUp(penguin, function() {
                    $(".words", article).html(old_words);
                    form.remove();
                });
            });
            api("/api/safe/article_get/", {
                article_slug: slug
            }, function(data) {
                if (data.status == "OK") {
                    var res = data.results[0];
                    var words = $(".words", article);
                    old_words = words.html();
                    $("textarea", form).val(res.content);
                    $("textarea", form).markdown_preview(words);
                    form.slideDown(penguin, function() {
                        $("textarea", form).focus();
                    });
                }
            });
        });

        $(".delete", article).click(function(ev) {
            ev.preventDefault();
            if (!confirm("Sure you want to delete this article?"))
                return;
            api("/api/article_delete/", {
                "article_slug": slug
            }, function(data) {
                if (data.status != "ERROR") {
                    window.location.href = "..";
                } else {
                    alert(data.message);
                }
            });
        });
    }

    function init_comment_form(form, container, parent_id) {
        $(".save", form).click(function(ev) {
            ev.preventDefault();
            $(".loader", form).show();
            $(".error", form).text("");
            api("/api/comment_new/", {
                "article_slug": $("article").attr("id"),
                "parent_id": parent_id,
                "content": $("textarea", form).val()
            }, function(data) {
                $(".loader", form).hide();
                if (data.status == "OK") {
                    var comment = $(data.results[0].html);
                    init_comment(comment);
                    comment.hide();
                    container.prepend(comment);
                    comment.fadeIn();
                    $("#comment-count").numberAdd(+1);
                    $("textarea", form).val("");
                    if (form.is(".editform"))
                        form.remove();
                } else {
                    $(".error", form).text(data.message);
                }
            }).error(function(err) {
                $(".loader", form).hide();
                $(".error", form).text(err.status + ' ' + err.statusText);
            });
        });
        $(".cancel", form).click(function(ev) {
            ev.preventDefault();
            form.slideUp(penguin, function() {
                form.remove();
            });
        });
    }

    function init_comment(comment) {
        var comment_id = comment.attr("id").split("-")[1];
        var content = $("> .content", comment);
        var replies = $("> .replies", comment);

        $(".reply", content).click(function(ev) {
            ev.preventDefault();
            if ($(".editform", content).length)
                return;
            var form = $("#editform").clone().attr("id", "");
            content.append(form);
            init_comment_form(form, replies, comment_id);
            form.slideDown(penguin, function() {
                $("textarea", form).focus();
            });
        });

        $(".edit", content).click(function(ev) {
            ev.preventDefault();
            if ($(".editform", content).length)
                return;
            var form = $("#editform").clone().attr("id", "");
            var old_words;
            content.append(form);
            $(".save", form).click(function(ev) {
                ev.preventDefault();
                $(".loader", form).show();
                $(".error", form).text("");
                api("/api/comment_edit/", {
                    "comment_id": comment_id,
                    "content": $("textarea", form).val()
                }, function(data) {
                    $(".loader", form).hide();
                    if (data.status == "OK") {
                        var elem = $(data.results[0].html);
                        comment.prepend($("> .content", elem));
                        content.remove();
                        init_comment(comment);
                    } else {
                        $(".error", form).text(data.message);
                    }
                }).error(function(err) {
                    $(".loader", form).hide();
                    $(".error", form).text(err.status + ' ' + err.statusText);
                });
            });
            $(".cancel", form).click(function(ev) {
                ev.preventDefault();
                form.slideUp(penguin, function() {
                    $(".words", content).html(old_words);
                    form.remove();
                });
            });
            api("/api/safe/comment_get/", {
                comment_id: comment_id
            }, function(data) {
                if (data.status == "OK") {
                    var res = data.results[0];
                    var words = $(".words", content);
                    old_words = words.html();
                    $("textarea", form).val(res.content);
                    $("textarea", form).markdown_preview(words);
                    form.slideDown(penguin, function() {
                        $("textarea", form).focus();
                    });
                }
            });
        });

        $(".up", content).click(function(ev) {
            ev.preventDefault();
            if ($(".up", content).hasClass("upvoted"))
                return;
            api("/api/comment_upvote/", {
                "comment": comment_id
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
        });

        $(".down", content).click(function(ev) {
            ev.preventDefault();
            if ($(".down", content).hasClass("downvoted"))
                return;
            api("/api/comment_downvote/", {
                "comment": comment_id
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
        });

        $(".permalink", content).click(function(ev) {
            content.addClass("highlight");
        });

        $(".delete", content).click(function(ev) {
            ev.preventDefault();
            if (!confirm("Sure you want to delete this comment?"))
                return;
            api("/api/comment_delete/", {
                "comment_id": comment_id
            }, function(data) {
                if (data.status != "ERROR") {
                    comment.remove();
                    $("#comment-count").numberAdd(-1);
                } else {
                    alert(data.message);
                }
            });
        });

        $(".remove", content).click(function(ev) {
            ev.preventDefault();
            var action = $(".remove", content).text();
            api("/api/comment_remove/", {
                "comment_id": comment_id,
                "action": action
            }, function(data) {
                if (data.status != "ERROR") {
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
        });
    }

    // export stuff
    article_init = init;

})();
