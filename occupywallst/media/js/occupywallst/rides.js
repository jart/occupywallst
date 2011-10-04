
var rides_init;

(function() {
    "use strict";

    var map;
    var dserv;
    var markers = [];
    var lines = {}
    var current_line = null;
    var philadelphia;

    function clear_map() {
        $.each(lines, function(i, e) {
            console.log(e);
            e.setMap(null);
        });
        $.each(markers, function(i, e) {
            e.setMap(null);
        });
        if (current_line) {
            current_line.setMap(null);
        }
        markers = [];
        lines = {}

    }

    $("form select[name='status']").change(function() {
        var option = $(this).val();
        var form = $(this).parent();
        $.post(form.attr('action'), form.serialize(), function() {
            var status = form.parent().parent().find(".req-status");
        });
    });

    $("#id_waypoints").change(function() {
        clear_map();
        var waypoints = $(this).val().split("\n");
        if (waypoints.length > 1) {
            show_route(waypoints);
        }
    });

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
        if (args.update_rides) {
            google.maps.event.addListener(map, "idle", update_rides);
        }
        if (args.initial_polyline) {
            var bounds = new google.maps.LatLngBounds();
            var polyline_arr = args.initial_polyline.map(function(e) {
                var latlng = new google.maps.LatLng(e[0],e[1]);
                bounds.extend(latlng);
                return latlng;
            })
            var polyline = happy_line(polyline_arr);
            map.fitBounds(bounds);

        }
        // $("#addroute").click(function() {
        //     ev.preventDefault();
        //     show_route($("textarea").val().split('\n'));
        // });

    };

    function update_rides() {
        var bounds = { bounds: map.getBounds().toUrlValue() };

        $.getJSON("/api/safe/rides/", bounds, function(rides) {
            clear_map();
            rides.results.forEach(function(ride, i) {
                var line = happy_line(ride.route.map(function(p) {
                    var point = new google.maps.LatLng(p[1],p[0]);
                    return point;
                }));
                google.maps.event.addListener(line, 'click', function(e) {
                    window.location = "/rides/"+ride.id+"/";
                });
                lines[ride.id]=line;
                console.log(line);
            });
        });
    }

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

    function show_route(waypoints, info) {
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
            current_line = line;
            google.maps.event.addListener(line, 'click', function(e) {
                var balloon = new google.maps.InfoWindow({content: info});
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
