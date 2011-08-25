
var userpage_init;

(function() {
    "use strict";

    var map;
    var mark;
    var latlng;

    function init(args) {
        if (args.map) {
            latlng = new google.maps.LatLng(args.lat, args.lng);
            map = new google.maps.Map(args.map, {
                zoom: 10,
                center: latlng,
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                streetViewControl: false,
                panControl: false,
                zoomControl: true,
                mapTypeControl: false,
                scaleControl: false
            });
            mark = new google.maps.Marker({map: map, position: latlng});
        }

        init_postform($(".postform"));
        $(".message").each(function(i) {
            init_message($(this));
        });
    }

    function init_postform(form) {
        $(".save", form).click(function(ev) {
            ev.preventDefault();
            $(".loader", form).show();
            $(".error", form).text("");
            api("/api/message_send/", {
                "to_username": $(".username").attr("id"),
                "content": $("textarea", form).val()
            }, function(data) {
                $(".loader", form).hide();
                if (data.status == "OK") {
                    var res = data.results[0];
                    var message = $(res.html);
                    init_message(message);
                    message.hide();
                    $("#messages").prepend(message);
                    message.fadeIn();
                    $("textarea", form).val("");
                } else {
                    $(".error", form).text(data.message);
                }
            }).error(function(err) {
                $(".loader", form).hide();
                $(".error", form).text(err.status + ' ' + err.statusText);
            });
        });
    }

    function init_message(message) {
        var message_id = message.attr("id").split("-")[1];
        $(".delete", message).click(function(ev) {
            ev.preventDefault();
            if (!confirm("Sure you want to delete this message?"))
                return;
            api("/api/message_delete/", {
                "message_id": message_id
            }, function(data) {
                if (data.status != "ERROR") {
                    message.remove();
                } else {
                    alert(data.message);
                }
            });
        });
    }

    // export stuff
    userpage_init = init;

})();
