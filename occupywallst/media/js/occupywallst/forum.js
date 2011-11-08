
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
        init_postform($(".postform"));
        pagination();
        $("#newlink").click(function(ev) {
            ev.preventDefault();
            $(".postform").toggle(400, function() {
                $(".postform .title").focus();
            });
        });
    }

    function load_more() {
        if (is_loading || is_done)
            return;
        is_loading = true;
        var list = $("#thread-list");
        var count = $(">.item", list).length;
        api("/api/safe/forumlinks/", {
            "after": count,
            "count": per_page
        }, function(data) {
            if (data.status == "OK") {
                $.each(data.results, function(k, html) {
                    list.append($(html));
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
                load_more();
            }
        }).scroll();
    }

    function init_postform(form) {
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
