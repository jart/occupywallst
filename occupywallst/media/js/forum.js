
var forum_init;

(function() {
    "use strict";

    var map;
    var mark;
    var latlng;

    function init(args) {
        init_postform($(".postform"));
    }

    function init_postform(form) {
        $(".save", form).click(function() {
            $(".loader", form).show();
            $(".error", form).text("");
            $.getJSON("/api/thread/new/", {
                "title": $(".title", form).val(),
                "content": $(".content", form).val()
            }, function(data) {
                $(".loader", form).hide();
                if (data.status == "OK") {
                    var thread = data.results[0];
                    window.location.href = thread.url;
                } else {
                    $(".error", form).text(data.message);
                }
            }).error(function(e) {
                $(".loader", form).hide();
                $(".error", form).text(e.status + e.statusText);
            });
            return false;
        });
    }

    // export stuff
    forum_init = init;

})();
