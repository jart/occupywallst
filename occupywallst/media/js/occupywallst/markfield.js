/*
 * The purpose of this script is to display a google map to modify
 * hidden geography-related form fields when signing up or editing
 * a user profile.
 */

var markfield_init;
var markfield_clear;

(function() {
    "use strict";

    var map;
    var mark;
    var geocoder;

    function init(args) {
        /* set initial marker if we're editing user profile */
        var center;
        var lat = parseFloat($("#id_position_lat").val());
        var lng = parseFloat($("#id_position_lng").val());
        var initial_mark = false;
        if (lat && lng) {
            center = new google.maps.LatLng(lat, lng);
            initial_mark = true;
        } else {
            /* otherwise just zoom to manhattan */
            lat = 40.717712644386026;
            lng = -74.00913921356198;
            center = new google.maps.LatLng(lat, lng);
        }

        /* initialize google stuff */
        geocoder = new google.maps.Geocoder();
        map = new google.maps.Map(args.elem, {
            zoom: 10,
            center: center,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            streetViewControl: false,
            panControl: false,
            zoomControl: true,
            scaleControl: false
        });

        /* relocate the pin when you click the map */
        google.maps.event.addListener(map, "click", on_map_click);

        if (initial_mark) {
            set_mark(center);
        }
    };

    function set_mark(latlng) {
        mark = new google.maps.Marker({
            map: map,
            position: latlng,
            title: "Click me to remove pin"
        });
        google.maps.event.addListener(mark, "click", unset_mark);
    }

    function unset_mark() {
        if (mark) {
            mark.setMap(null);
            mark = null;
            $("#id_formatted_address").val("");
            $("#id_position_lat").val("");
            $("#id_position_lng").val("");
            $("#id_address").val("");
            $("#id_city").val("");
            $("#id_region").val("");
            $("#id_zipcode").val("");
            $("#id_country").val("");
        }
    }

    function on_map_click(e) {
        /* turn lat/lng into an address.  MORE DATA!! */
        geocoder.geocode({"latLng": e.latLng}, function(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                var addr = addr_info(results[0]);
                if (!addr.address || !addr.city || !addr.country) {
                    console.log("bad click", addr.address, addr.city,
                                addr.country);
                    return;
                }
                unset_mark();
                $("#id_position_lat").val(e.latLng.lat());
                $("#id_position_lng").val(e.latLng.lng());
                $("#id_formatted_address").val(addr.formatted_address);
                $("#id_address").val(addr.address);
                $("#id_city").val(addr.city);
                $("#id_region").val(addr.region);
                $("#id_zipcode").val(addr.zipcode);
                $("#id_country").val(addr.country);
                set_mark(e.latLng);
            }
        });
    }

    function addr_info(addr) {
        return {
            formatted_address: addr.formatted_address,
            address: (addr_part(addr, "street_number").long_name + " " +
                      addr_part(addr, "route").long_name),
            city: (addr_part(addr, "locality").long_name ||
                   addr_part(addr, "sublocality").long_name),
            region: addr_part(addr, "administrative_area_level_1").short_name,
            zipcode: addr_part(addr, "postal_code").long_name,
            country: addr_part(addr, "country").short_name
        }
    }

    function addr_part(addr, name) {
        var i, j;
        for (i in addr.address_components) {
            for (j in addr.address_components[i].types) {
                if (addr.address_components[i].types[j] == name) {
                    return addr.address_components[i];
                }
            }
        }
        return {long_name: "", short_name: ""};
    }

    /* export stuff */
    markfield_init = init;
    markfield_clear = unset_mark;

})();
