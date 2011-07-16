
var rides_init;

(function() {
    "use strict";

    rides_init = function() {
        philadelphia = new google.maps.LatLng(39.95, -75.16);
        dserv = new google.maps.DirectionsService();
        map = new google.maps.Map($("#map").get(0), {
            zoom: 14,
            center: philadelphia,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            streetViewControl: false,
            panControl: false,
            zoomControl: true,
            scaleControl: true,
        });
        google.maps.event.addListener(map, 'idle', get_events);
    };

    //////////////////////////////////////////////////////////////////////
    // PRIVATE STUFF

    var map;
    var dserv;
    var markers = [];
    var glob = {};
    var philadelphia;

    function happy_line(path) {
        var line = new google.maps.Polyline({
            map: map,
            path: path,
            strokeOpacity: 0.4,
            strokeWeight: 5,
            strokeColor: 'blue',
            zIndex: 1,
        })
        google.maps.event.addListener(line, 'mouseover', function(e) {
            line.setOptions({strokeColor: 'red',
                             strokeOpacity: 0.7,
                             strokeWeight: 10,
                             zIndex: 10});
        });
        google.maps.event.addListener(line, 'mouseout', function(e) {
            line.setOptions({strokeColor: 'blue',
                             strokeOpacity: 0.4,
                             strokeWeight: 5,
                             zIndex: 1});
        });
        return line;
    }

    function show_route(from, to) {
        var dreq = {
            origin: from,
            destination: to,
            travelMode: google.maps.TravelMode.DRIVING
        }
        dserv.route(dreq, function(result, status) {
            if (status != google.maps.DirectionsStatus.OK) {
                alert(status);
                return;
            }
            var line = happy_line(result.routes[0].overview_path);
            google.maps.event.addListener(line, 'click', function(e) {
                var balloon = new google.maps.InfoWindow({content: 'we\'re driving from ' + from + '<br /> so you should carpool with us :3'});
                balloon.open(map, new google.maps.Marker({position: e.latLng}));
            })
            if (glob.bounds) {
                glob.bounds.union(result.routes[0].bounds);
            } else {
                glob.bounds = result.routes[0].bounds;
            }
            map.fitBounds(glob.bounds);
        });
    }

})();
