
var occupywallst_init;

(function() {
    "use strict";

    var MOUSE_LEFT = 1;
    var MOUSE_MIDDLE = 2;
    var MOUSE_RIGHT = 3;

    function init() {
        $(".clickdiv, .clickdiv a").click(function(e) {
            var url = ($(this).attr('href') ||
                       $("a.primary", this).attr('href'));
            if (e.which == MOUSE_LEFT) {
                window.location.href = url;
                return false;
            } else if (e.which == MOUSE_MIDDLE) {
                window.open(url);
                return false;
            }
        });
    };

    // export stuff
    occupywallst_init = init;

})();
