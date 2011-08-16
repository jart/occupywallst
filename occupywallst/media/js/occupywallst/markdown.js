// transform textarea elements to show markdown previews

(function() {
    "use strict";

    var converter;

    jQuery.fn.markdown_preview = function(preview) {
        var elems = this;
        lazy_load('/media/js/showdown.min.js', function() {
            if (!converter)
                converter = new Showdown.converter();
            elems.each(function() {
                setup($(this), preview);
            });
        });
        return this;
    };

    /**
     * Defer function until it hasn't been called for delay milliseconds
     *
     * This is useful for decorating event functions that get called a
     * zillion times and you want to wait until things cool off before
     * actually doing something.
     *
     * Arguments and return values are eaten up in the process.
     */
    function inactivity_delay(delay, funk) {
        var timer = null;
        var last = Date.now();
        function invoke() {
            last = Date.now();
            if (timer)
                clearTimeout(timer);
            timer = setTimeout(function() {
                // console.log("firing for effect");
                timer = null;
                funk();
            }, delay);
        }
        return invoke;
    }

    function setup(elem, preview) {
        if (!preview) {
            preview = $('<div class="markdown-preview"/>');
            elem.after(preview);
        }
        function update() {
            preview.html(converter.makeHtml(elem.val()));
        }
        update();
        update = inactivity_delay(300, update);
        elem.keyup(update).bind('cut paste', update);
    }

})();
