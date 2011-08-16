// lazily load javascript files on demand
//
// sometimes you don't want the performance hit of loading a
// javascript file on page load.  this tool allows you to defer the
// loading of a javascript file until you actually need it.  You can
// call lazy_load a zillion times if you like, but the script will
// only be downloaded/executed once.
//
// You would think that jQuery.getScript() would have this same
// behavior but unfortunately it will re-download and re-execute the
// script each time it's called.
//
// Example usage:
//
//   lazy_load('/media/js/lolcat.js', function() {
//     lolcat();
//   });
//
// 

var lazy_load;

(function() {
    "use strict";

    var loaded = {};
    var loading = {};
    var callbacks = {};

    function load(script, callback) {
        if (loaded[script]) {
            callback();
        } else if (loading[script]) {
            callbacks[script].push(callback);
        } else {
            loading[script] = true;
            callbacks[script] = [callback];
            $.getScript(script, function() {
                $.each(callbacks[script], function(i, callback) {
                    callback();
                });
                delete loading[script];
                delete callbacks[script];
                loaded[script] = true;
            });
        }
    }

    // export stuff
    lazy_load = load;

})();
