
var forum_init;

(function() {
    "use strict";

    var map;
    var mark;
    var latlng;

    var per_page;
    var is_loading = false;
    var is_done = false;

    function init(args) {
        per_page = args.per_page;
        init_newthreadform($(".newthreadform"));
        pagination();
        $(".newthreadlink").click(function(ev) {
            ev.preventDefault();
            $(".newthreadform").toggle(400, function() {
                $(".newthreadform .title").focus();
            });
        });
    }

    function load_more(list, url) {
        if (is_loading || is_done || !list.length)
            return;
        is_loading = true;
        var count = $(".item", list).length;
        api(url, {
            "after": count,
            "count": per_page
        }, function(data) {
            if (data.status == "OK") {
                $.each(data.results, function(k, html) {
                    var luv = $("<div>" + html + "</div>");
                    article_init(luv);
                    list.append(luv);
                });
                $(".clickdiv").clickdiv();
                is_loading = false;
            } else if (data.status == "ZERO_RESULTS") {
                is_done = true;
            } else {
                $("#loady").parent().text(data.message);
                is_done = true;
            }
        }).error(function(err) {
            $("#loady").parent().text(err.status + ' ' + err.statusText);
            is_done = true;
        });
    }

    function pagination() {
        $(window).scroll(function(ev) {
            if ($("#loady").scrolledToShow(250)) {
                load_more($("#thread-list"), "/api/safe/forumlinks/");
                load_more($("#comment-list"), "/api/safe/commentfeed/");
            }
        }).scroll();
    }

    function init_newthreadform(form) {
        $(".save", form).click(function(ev) {
            ev.preventDefault();
            $(".loader", form).show();
            $(".error", form).text("");
            api("/api/article_new/", {
                "title": $(".title", form).val(),
                "content": $(".content", form).val(),
                "is_forum": "true"
            }, function(data) {
                $(".loader", form).hide();
                if (data.status == "OK") {
                    var thread = data.results[0];
                    window.location.href = thread.url;
                } else {
                    $(".error", form).text(data.message);
                }
            }).error(function(err) {
                $(".loader", form).hide();
                $(".error", form).text(err.status + ' ' + err.statusText);
            });
        });
    }

    // export stuff
    forum_init = init;

})();
