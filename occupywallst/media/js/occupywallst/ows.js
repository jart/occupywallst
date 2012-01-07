
var ows_init;
var ows_timesince;
var ows_sockio_url;
var ows_inactivity_delay;

(function() {
    "use strict";

    var MOUSE_LEFT = 1;
    var MOUSE_MIDDLE = 2;
    var MOUSE_RIGHT = 3;

    var sub;

    function init(args) {
        $.each(args.notifications, function(i, notify) {
            $("#notifications .items").prepend(notify_to_elem(notify));
        });
        if ($("#notifications .item").length > 0) {
            $("#notifications").slideDown();
        }
        $(".clickdiv").clickdiv();
        $(".hider").hider();
        // setTimeout(subscriber, 100);
        setInterval(function() {
            $("#notifications .item span").each(function() {
                $(this).text(timesince($(this).data('published')) + ' ago');
            });
        }, 1000);
        $("input.clearme").focus(function() {
            if ($(this).hasClass('clearme')) {
                $(this).removeClass('clearme');
                $(this).val('');
            }
        });
        init_setlang();
    }

    function init_setlang() {
        var langform = $("#setlanguage");
        $("a", langform).each(function() {
            $(this).click(function(ev) {
                ev.preventDefault();
                $('input[name="language"]', langform).val($(this).text());
                langform.submit();
            });
        });
    }

    function notify_to_elem(notify) {
        var elem = $('<div class="item clickdiv"></div>');
        elem.append($('<a class="primary"/>')
                    .attr('href', notify.url)
                    .text(notify.message));
        elem.append($('<span class="time"/>')
                    .data('published', notify.published)
                    .text(timesince(notify.published) + ' ago'));
        return elem;
    }

    function notification(elem) {
        if (!elem.jquery)
            elem = notify_to_elem(elem);
        elem.clickdiv();
        if ($("#notifications .item").length > 0) {
            elem.hide();
            $("#notifications .items").prepend(elem);
            elem.slideDown();
        } else {
            $("#notifications .items").prepend(elem);
            $("#notifications").slideDown();
        }
    }

    function subscriber() {
        if (typeof(io) == "undefined")
            return;
        sub = io.connect(sockio_url() + "notifications");
        sub.on('ows.notification', function(notify) {
            notification(notify);
        });
        sub.on('ows.broadcast', function(msg) {
        });
    }

    function timesince(timestamp) {
        var seconds = (Date.now() - timestamp) / 1000
        var x, s;
        if (seconds <= 60) {
            x = Math.max(0, Math.round(seconds));
            s = ['second', 'seconds'];
        } else if (seconds <= 60 * 60) {
            x = Math.round(seconds / 60);
            s = ['minute', 'minutes'];
        } else if (seconds <= 60 * 60 * 24) {
            x = Math.round(seconds / 60 / 60);
            s = ['hour', 'hours'];
        } else if (seconds <= 60 * 60 * 24 * 30) {
            x = Math.round(seconds / 60 / 60 / 24);
            s = ['day', 'days'];
        } else {
            x = Math.round(seconds / 60 / 60 / 24 / 30);
            s = ['month', 'months'];
        }
        return "" + x + " " + s[x == 1 ? 0 : 1];
    }

    function sockio_url() {
        // workaround bug in socket.io
        var schm = document.location.protocol;
        var port = (schm == "http:") ? "80" : "443";
        var host = document.location.host;
        return schm + "//chat." + host + ":" + port + "/";
    }

    jQuery.fn.clickdiv = function() {
        return this.each(function() {
            var primary = $("a.primary", this).attr('href');
            $(this).click(function(ev) {
                if (!jQuery(ev.target).is("a")) {
                    ev.preventDefault();
                    if (ev.metaKey || ev.which == MOUSE_MIDDLE) {
                        window.open(primary);
                    } else {
                        window.location.href = primary;
                    }
                }
            });
        });
    };

    jQuery.fn.hider = function() {
        return this.each(function() {
            var hidden = jQuery(".hidden", this);
            jQuery(".toggle", this).click(function(ev) {
                if (!hidden.is(":visible")) {
                    hidden.slideDown(250);
                } else {
                    hidden.slideUp(250);
                }
            });
        });
    };

    /**
     * Is page scrolled to make element visible?
     */
    jQuery.fn.scrolledToShow = function(expand) {
        if (!this.length)
            return;
        if (!expand)
            expand = 0;
        var wtop = $(window).scrollTop() - expand;
        var wbot = wtop + $(window).height() + expand;
        var etop = this.offset().top;
        var ebot = top + this.height();
        return ((etop >= wtop && etop <= wbot) ||
                (ebot >= wtop && ebot <= wbot));
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

    // export stuff
    ows_init = init;
    ows_timesince = timesince;
    ows_sockio_url = sockio_url;
    ows_inactivity_delay = inactivity_delay;

})();
