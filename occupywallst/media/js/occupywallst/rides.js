var maps_init;

(function() {
    "use strict";
    var geocoder;
    var infowindow;
    var address;
    var marker;
    
    function geocodePosition(pos) {
      geocoder.geocode({
        latLng: pos
      }, function(responses) {
        if (responses && responses.length > 0) {
          
           updateMarkerAddress(responses[0].formatted_address);
            
        } else {
          updateMarkerAddress('Cannot determine address at this location.');
        }
      });
    }

    function updateMarkerPosition(latLng) {
        $('#id_rendezvous_lat').val(latLng.lat());
        $('#id_rendezvous_lng').val(latLng.lng());
    }

    function updateMarkerAddress(str) {
        infowindow.setContent('<b>Approximant Address</b><br>'+str+'');
        $('#id_rendezvous_address').val(str);
        address = str;
    }

    function initialize(args) {
        
        geocoder = new google.maps.Geocoder();
        var latLng = new google.maps.LatLng(-34.397, 150.644);
        var map = new google.maps.Map(args.map, {
            zoom: args.zoom,
            center: args.center,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        });
    
         //create route
        if (args.initial_polyline) {
            var bounds = new google.maps.LatLngBounds();
            //does this really work?
            var polyline_arr = args.initial_polyline.map(function(e) {
                var latlng = new google.maps.LatLng(e[0],e[1]);
                bounds.extend(latlng);
                return latlng;
            })
            
            var polyline = happy_line(polyline_arr);
            map.setCenter(bounds.getCenter());
            map.fitBounds(bounds);
        }

        //create rendezvous marker
        if (args.rendezvous) {
            var len = args.rendezvous.length;
            var rmarker;
            var position; 
            var rWindow = new google.maps.InfoWindow();
            while (len--){
                position = new google.maps.LatLng(args.rendezvous[len][0],args.rendezvous[len][1]);
                rmarker = new google.maps.Marker({
                    position: position,
                    title: 'rendezvous Point',
                    map: map,
                    draggable: false
                });
                
                google.maps.event.addListener(rmarker, 'click', (function(rmarker, len) {
                    return function() {
                      rWindow.setContent("<b>"+args.rendezvous[len][3]+"</b><br>approximate rendezvous<br> "+args.rendezvous[len][2]);
                      rWindow.open(map, rmarker);
                    }
                  })(rmarker, len));
                  
            }
        }   
            //create marker
        if (typeof args.marker  != 'undefined'){
                var position = (args.marker ? pos_to_latlng(args.marker) : map.getCenter());
                marker = new google.maps.Marker({
                position: position,
                title: 'Pick up Point',
                map: map,
                draggable: args.draggable
            });
            
            //create info window
            infowindow = new google.maps.InfoWindow();
            infowindow.setContent(args.address || "Please Select a Rendezvous");
            infowindow.open(map, marker);
            
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.open(map, marker);
            });
            
            // Update current position info.
            updateMarkerPosition(latLng);
          
            // Add dragging event listeners.
            google.maps.event.addListener(marker, 'dragstart', function() {
                updateMarkerAddress("<img src='/media/img/ajax-loader-32.gif'>");
                
                
            });
          
            google.maps.event.addListener(marker, 'drag', function() {
                
                
            });
          
            google.maps.event.addListener(marker, 'dragend', function() {
                updateMarkerPosition(marker.getPosition());
                geocodePosition(marker.getPosition());
                $('input[type="submit"]').removeAttr('disabled');
                //$('button').removeAttr('style');
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

        function pos_to_latlng(position) {
            return new google.maps.LatLng(position[0], position[1]);
        }
      

    }
   
    maps_init = initialize;
})();


var rides_init;

(function() {
    "use strict";

    var geocoder;
    var map;
    var dserv;
    var lines = {}
    var current_line = null;
    var directionsDisplay;
    var waypoints = new Array(2); 
    var waypoints_points = []; 
    
    function clear_map() {
        $.each(lines, function(i, e) {
            console.log(e);
            e.setMap(null);
        });
        if (current_line) {
            current_line.setMap(null);
        }
        lines = {}
    }

    $("form select[name='status']").change(function() {
        var option = $(this).val();
        var form = $(this).parent();
        $.post(form.attr('action'), form.serialize(), function() {
            var status = form.parent().parent().find(".req-status");
        });
    });
    
    $("#id_start_address").change(function(){
        waypoints[0] = $(this).val();
        draw_route();
    });

    $("#id_end_address").change(function(){
        waypoints[waypoints.length-1] = $(this).val();
        draw_route();
    });
    
    $("#id_waypoints").change(function() {
        var new_points = $("#id_waypoints").val().split(/\r\n|\r|\n/);
        waypoints.splice(1, waypoints.length-2, new_points);
        waypoints = flatten(waypoints);
        draw_route();
    });
    


    function init(args) {
        geocoder = new google.maps.Geocoder();
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
        
        //draw route
        var bounds = new google.maps.LatLngBounds();
        if (args.initial_polyline) {
            var polyline_arr = args.initial_polyline.map(function(e) {
                var latlng = new google.maps.LatLng(e[0],e[1]);
                bounds.extend(latlng);
                return latlng;
            });
            current_line = happy_line(polyline_arr);
            map.fitBounds(bounds);

        }

        waypoints[0] = $("#id_start_address").val();
        waypoints[waypoints.length-1] = $("#id_end_address").val();   
        draw_route();   
        //create rendezvous marker
        if (args.rendezvous) {
            var len = args.rendezvous.length;
            var rmarker;
            var position; 
            var infowindow = new google.maps.InfoWindow();
            while (len--){
                position = new google.maps.LatLng(args.rendezvous[len][0],args.rendezvous[len][1]);
                rmarker = new google.maps.Marker({
                    position: position,
                    title: 'rendezvous Point',
                    map: map,
                    draggable: false
                });
                
                google.maps.event.addListener(rmarker, 'click', (function(rmarker, len) {
                    return function() {
                      infowindow.setContent("<b>"+args.rendezvous[len][3]+"</b><br>approximate rendezvous<br> "+args.rendezvous[len][2]);
                      infowindow.open(map, rmarker);
                    }
                  })(rmarker, len));
                  
            }
        }
    };

    function update_rides() {
        var bounds = { bounds: map.getBounds().toUrlValue() };

        $.getJSON("/rides/api/safe/rides/", bounds, function(rides) {
            
            rides.results.forEach(function(ride, i) {
                var line = happy_line(ride.route.map(function(p) {
                    var point = new google.maps.LatLng(p[1],p[0]);
                    return point;
                }),ride.title,ride.address,ride.id );
                google.maps.event.addListener(line, 'click', function(e) {
                    window.location = "/rides/"+ride.id+"/";
                });
                lines[ride.id]=line;
                console.log(line);
            });
        });
    }

    function happy_line(path,title,info,id) {
		 var line = new google.maps.Polyline({
				map: map,
				path: path,
				strokeOpacity: 0.4,
				strokeWeight: 5,
				strokeColor: 'blue',
				zIndex: 1
		});
	
	
        if(typeof info !== 'undefined'){
			var lmaker = new google.maps.Marker({
				position: path[0],
				title: '<b>'+title+'</b><br>'+info,
				map: map,
				draggable: false,
				icon: "http://www.google.com/uds/samples/places/temp_marker.png"
			});
			
			var infowindow = new google.maps.InfoWindow();
			google.maps.event.addListener(lmaker, 'click', (function(lmaker) {
				return function() {
					//google.maps.event.trigger(line, 'mouseover');
					infowindow.setContent('<b>'+title+'</b><br>'+info +'<br><a href="/rides/'+id+'/">View Ride</a>');
					infowindow.open(map, lmaker);
				}
			})(lmaker));

			google.maps.event.addListener(infowindow, 'closeclick', (function(lmaker) {
				return function() {
					//google.maps.event.trigger(line, 'mouseout');
				}
			})(lmaker));			
		}
        
       
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
    
    function draw_route(){
        if(waypoints.length >= 2 &&  waypoints[waypoints.length-1] && waypoints[0]){        
            show_route(waypoints);
        }
    };

    function show_route(waypoints, info) {
        var i;
        var from = waypoints[0];
        var to = waypoints[waypoints.length - 1];
        var mids = waypoints.slice(1, waypoints.length - 1);
        waypoints = [];
        for (i in mids) {
            waypoints.push({location: mids[i], stopover: true});
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
                if(status == "ZERO_RESULTS")
                    alert("Route Not Found!");
                return;
            }   
            clear_map();

            waypoints_points = [];
            //get waypoint cordinates change to map
            result.routes[0].legs.filter(function(e,i){
                if(i == 0){
                    waypoints_points.push(e.start_location);
                }
                waypoints_points.push(e.end_location);
            });
            //store points to the way points. this is retard ):
            var pointvals = [];
            waypoints_points.filter(function(e){
                    pointvals.push( e.lat() +' '+ e.lng());
                });
            $('#id_waypoints_points_wkt').val("LINESTRING ("+pointvals.join(',')+")");
            //drawline
            current_line = happy_line(result.routes[0].overview_path);
            
        });
    }
    
    function flatten(array){
        var flat = [];
        for (var i = 0, l = array.length; i < l; i++){
            var type = Object.prototype.toString.call(array[i]).split(' ').pop().split(']').shift().toLowerCase();
            if (type) { flat = flat.concat(/^(array|collection|arguments|object)$/.test(type) ? flatten(array[i]) : array[i]); }
        }
        return flat;
    }
    // export stuff
    rides_init = init;
})();
