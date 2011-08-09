
var rides_init;

(function() {
    "use strict";

    var map;
    var dserv;
    var markers = [];
    var philadelphia;

    function init(args) {
        dserv = new google.maps.DirectionsService();
        map = new google.maps.Map(args.map, {
            center: args.center,
            zoom: args.zoom,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            streetViewControl: false,
            panControl: false,
            zoomControl: true,
            scaleControl: true
        });

        show_route(["phila pa", "new york ny"]);
        show_route(["washington dc", "new york ny"]);
        show_route(["danbury ct", "new york ny"]);
        show_route(["toronto ca", "new york ny"]);

        // $("#addroute").click(function () {
        //     show_route($("textarea").val().split('\n'));
        //     return false;
        // });

    };

    function happy_line(path) {
        var line = new google.maps.Polyline({
            map: map,
            path: path,
            strokeOpacity: 0.4,
            strokeWeight: 5,
            strokeColor: 'blue',
            zIndex: 1
        });
        google.maps.event.addListener(line, 'mouseover', function(e) {
            line.setOptions({
                strokeColor: 'red',
                strokeOpacity: 0.7,
                strokeWeight: 10,
                zIndex: 10
            });
        });
        google.maps.event.addListener(line, 'mouseout', function(e) {
            line.setOptions({
                strokeColor: 'blue',
                strokeOpacity: 0.4,
                strokeWeight: 5,
                zIndex: 1
            });
        });
        return line;
    }

    function show_route(waypoints) {
        var i;
        var from = waypoints[0];
        var to = waypoints[waypoints.length - 1];
        var mids = waypoints.slice(1, waypoints.length - 1);
        waypoints = [];
        for (i in mids) {
            waypoints.push({location: mids[i], stopover: false});
        }

        var dreq = {
            origin: from,
            destination: to,
            waypoints: waypoints,
            travelMode: google.maps.TravelMode.DRIVING,
            optimizeWaypoints: true,
            provideRouteAlternatives: false
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
            });
            // if (glob.bounds) {
            //     glob.bounds.union(result.routes[0].bounds);
            // } else {
            //     glob.bounds = result.routes[0].bounds;
            // }
            // map.fitBounds(glob.bounds);
        });
    }

    // export stuff
    rides_init = init;

})();
