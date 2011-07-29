
var occupywallst_init;

(function() {
    "use strict";

    function init() {
        $(".clickdiv, .clickdiv a").click(function() {
            window.location.href = ($(this).attr('href') ||
                                    $("a.primary", this).attr('href'));
            return false;
        });
    };

    // export stuff
    occupywallst_init = init;

})();
