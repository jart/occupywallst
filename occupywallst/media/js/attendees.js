
var attendees_init;

(function() {
    "use strict";

    attendees_init = function(args) {
        geocoder = new google.maps.Geocoder();
        map = new google.maps.Map(args.elem, {
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
    var max_markers = 100;
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
        is_fetching = true;
        $.getJSON("/api/attendees/", {
            "bounds": bounds_to_string(map.getBounds())
        }, function(data) {
            if (data.status == "OK") {
                attendees = data.results;
                $.each(attendees, function (n, attendee) {
                    attendee.latlng = pos_to_latlng(attendee.position);
                });
                refresh();
            }
            is_fetching = false;
        }).error(function(resp) {
            $("html").html(resp.responseText);
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

    function new_marker(pin) {
        var marker = new google.maps.Marker({
            map: map,
            position: pin.attendee.latlng,
            title: pin.attendee.username
        });
        google.maps.event.addListener(marker, "click", function() {
            $.getJSON("/api/user/", {
                "username": pin.attendee.username
            }, function(data) {
                if (pin.flag_remove)
                    return;
                var details = "No Information Available";
                console.log(data);
                if (data.status == "OK" && data.results.length == 1) {
                    var user = data.results[0];
                    details  = "<p><b>" + user.username + "</b></p><br />";
                    if (user.info)
                        details += "<p>" + user.info + "</p>";
                    details += "<p><a href=\"/users/" + user.username +
                        "/\">More Info</a></p>";
                }
                if (balloon)
                    balloon.close();
                balloon = new google.maps.InfoWindow({
                    content: details
                });
                balloon.open(map, marker);
                pin.balloon = balloon;
            }).error(function(resp) {
                $("html").html(resp.responseText);
            });
        });
        return marker;
    }

})();
