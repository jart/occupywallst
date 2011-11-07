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
            var text = elem.val();
            text = text.replace(/<!--.*?-->/g, '');
            preview.html(converter.makeHtml(text));
        }
        update();
        update = ows_inactivity_delay(1000, update);
        elem.keyup(update).bind('cut paste', update);
    }

})();
