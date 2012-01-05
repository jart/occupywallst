
var attendees_init;

(function() {
    "use strict";

    attendees_init = function(args) {
        geocoder = new google.maps.Geocoder();
        map = new google.maps.Map(args.map, {
            zoom: args.zoom,
            center: args.center,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            streetViewControl: true,
            panControl: false,
            zoomControl: true,
            scaleControl: true
        });
        google.maps.event.addListener(map, "idle", on_idle);
    };

    //////////////////////////////////////////////////////////////////////
    // PRIVATE STUFF

    var map;
    var balloon;
    var geocoder;
    var pins = [];
    var attendees = [];
    var max_markers = 1000;
    var is_fetching = false;

    function pos_to_latlng(position) {
        return new google.maps.LatLng(position[0], position[1]);
    }

    function bounds_to_string(bounds) {
        var sw = bounds.getSouthWest();
        var nw = bounds.getNorthEast();
        return [sw.lat(), sw.lng(), nw.lat(), nw.lng()].join(",");
    }

    function latlng_to_string(latlng) {
        return "" + latlng.lat() + "," + latlng.lng();
    }

    function clear() {
        var n;
        for (n in pins) {
            var pin = pins[n];
            pin.marker.setMap(null);
        }
        pins.length = 0;
    }

    function find_pin(loc) {
        var n;
        for (n in pins) {
            var pin = pins[n];
            if (pin.attendee.id == loc.id)
                return pin;
        }
        return null;
    }

    function on_idle() {
        if (!is_fetching) {
            fetch();
        }
    }

    function fetch() {
        $("#loader").show();
        is_fetching = true;
        api("/api/safe/attendees/", {
            "bounds": bounds_to_string(map.getBounds())
        }, function(data) {
            if (data.status == "OK") {
                attendees = data.results;
                $.each(attendees, function (n, attendee) {
                    attendee.latlng = pos_to_latlng(attendee.position);
                });
                refresh();
            }
            $("#loader").hide();
            is_fetching = false;
        }).error(function(err) {
            $("#loader").hide();
            is_fetching = false;
        });
    }

    function refresh() {
        var n;
        var bounds = map.getBounds();

        for (n in pins) {
            var pin = pins[n];
            pin.flag_remove = true;
        }

        for (n in attendees) {
            var loc = attendees[n];
            if (bounds.contains(loc.latlng)) {
                var pin = find_pin(loc);
                if (pin) {
                    pin.flag_remove = false;
                } else {
                    var pin = {
                        marker: null,
                        balloon: null,
                        attendee: loc,
                        visible: true
                    };
                    pins.push(pin);
                }
            }
        }

        var pins2 = [];
        for (n in pins) {
            var pin = pins[n];
            if (pin.flag_remove || pins2.length >= max_markers) {
                if (pin.marker) {
                    pin.marker.setMap(null);
                }
                if (pin.balloon) {
                    pin.balloon.close();
                    balloon = null;
                }
            } else {
                pins2.push(pin);
            }
        }
        pins = pins2;

        for (n in pins) {
            var pin = pins[n];
            if (pin.marker)
                continue;
            pin.marker = new_marker(pin);
        }
    }

    function init_msgform(form, to_username) {
        $(".save", form).click(function(ev) {
            ev.preventDefault();
            $(".loader", form).show();
            $(".error", form).text("");
            api("/api/message_send/", {
                "to_username": to_username,
                "content": $("textarea", form).val()
            }, function(data) {
                $(".loader", form).hide();
                if (data.status == "OK") {
                    var res = data.results[0];
                    var message = $(res.html);
                    $("textarea", form).val("");
                    $(".error", form).text("Message Sent!");
                } else {
                    $(".error", form).text(data.message);
                }
            }).error(function(err) {
                $(".loader", form).hide();
                $(".error", form).text(err.status + ' ' + err.statusText);
            });
        });
    }

    function new_marker(pin) {
        var username = pin.attendee.username;
        var marker = new google.maps.Marker({
            map: map,
            position: pin.attendee.latlng,
            title: username
        });
        google.maps.event.addListener(marker, "click", function() {
            $("#loader").show();
            is_fetching = true;
            api("/api/safe/attendee_info/", {
                "username": username
            }, function(data) {
                if (pin.flag_remove)
                    return;
                if (data.status == "OK") {
                    var res = data.results[0];
                    if (balloon)
                        balloon.close();
                    var content = $(res.html);
                    init_msgform($(".postform", content), username);
                    balloon = new google.maps.InfoWindow({
                        content: content.get(0)
                    });
                    balloon.open(map, marker);
                    pin.balloon = balloon;
                } else {
                    alert(data.status);
                }
                $("#loader").hide();
                is_fetching = false;
            }).error(function(err) {
                $("#loader").hide();
                is_fetching = false;
            });
        });
        return marker;
    }

})();
