
var index_init;

(function() {
    "use strict";

    var is_working = false;

    function init(args) {
        // $(window).scroll(function(ev) {
        //     if (is_working)
        //         return;
        //     $("#archives article.unloaded").each(function() {
        //         if ($(this).scrolledToShow(250)) {
        //             $(this).removeClass("unloaded");
        //             $(".loady", this).fadeIn();
        //             load_article($(this));
        //             return false;
        //         }
        //     });
        // }).scroll();
    }

    // function load_article(article) {
    //     is_working = true;
    //     api("/api/safe/article_get/", {
    //         "article_slug": article.attr("id"),
    //         "read_more": "true"
    //     }, function(data) {
    //         is_working = false;
    //         if (data.status == "OK") {
    //             article.replaceWith($(data.results[0].html));
    //         } else {
    //             $(".loady", article).parent().text(data.message);
    //         }
    //     }).error(function(err) {
    //         is_working = false;
    //         $(".loady", article).parent().text(err.status + ' ' + err.statusText);
    //     });
    // }

    // export stuff
    index_init = init;

})();
