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

    function setup(elem, preview) {
        if (!preview) {
            preview = $('<div class="markdown-preview"/>');
            elem.after(preview);
        }
        function update() {
            preview.html(converter.makeHtml(elem.val()));
        }
        update();
        update = ows_inactivity_delay(300, update);
        elem.keyup(update).bind('cut paste', update);
    }

})();
