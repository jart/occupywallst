
var ows_init;
var ows_timesince;
var ows_sockio_url;

(function() {
    "use strict";

    var MOUSE_LEFT = 1;
    var MOUSE_MIDDLE = 2;
    var MOUSE_RIGHT = 3;

    var sub;

    function init(args) {
        $.each(args.notifications, function(i, notify) {
            $("#notifications .items").append(notify_to_elem(notify));
        });
        if ($("#notifications .item").length > 0) {
            $("#notifications").slideDown();
        }
        $(".clickdiv").clickdiv();
        subscriber();
        setInterval(function() {
            $("#notifications .item span").each(function() {
                $(this).text(timesince($(this).data('published')) + ' ago');
            });
        }, 1000);
        var anchor = $(document.location.hash);
        if (anchor.hasClass("comment")) {
            $("> .content .words", anchor).addClass("highlight");
        }
    }

    function notify_to_elem(notify) {
        var elem;
        elem = $('<div class="item clickdiv"></div>');
        elem.append($('<a class="primary"/>')
                    .attr('href', notify.url)
                    .text(notify.message));
        elem.append($('<span class="time"/>')
                    .data('published', notify.published)
                    .text(timesince(notify.published) + ' ago'));
        return elem;
    }

    function subscriber() {
        if (typeof(io) == "undefined")
            return;
        sub = io.connect(sockio_url() + "notifications");
        sub.on('ows.notification', function(notify) {
            var elem = notify_to_elem(notify).clickdiv();
            if ($("#notifications .item").length > 0) {
                elem.hide();
                $("#notifications .items").prepend(elem);
                elem.slideDown();
            } else {
                $("#notifications .items").prepend(elem);
                $("#notifications").slideDown();
            }
        });
        sub.on('ows.broadcast', function(msg) {
        });
    }

    function timesince(timestamp) {
        var seconds = (Date.now() - timestamp) / 1000
        var x, s;
        if (seconds <= 60) {
            x = Math.round(seconds);
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
            $(this).click(function(e) {
                var url = ($(e.target).attr('href') || primary);
                if (e.which == MOUSE_LEFT) {
                    window.location.href = url;
                    return false;
                } else if (e.which == MOUSE_MIDDLE) {
                    window.open(url);
                    return false;
                }
            });
        });
    };

    // export stuff
    ows_init = init;
    ows_timesince = timesince;
    ows_sockio_url = sockio_url;

})();
