r"""

    occupywallst.geo
    ~~~~~~~~~~~~~~~~

    Useful geographic map type functions.

"""

import json
import urllib
import urllib2
from math import sqrt, cos, sin, atan2, pi


class GeocodeException(Exception):
    pass


def directions(waypoints):
    url = ('http://maps.googleapis.com/maps/api/directions/json?' +
           urllib.urlencode({'origin': waypoints[0],
                             'destination': waypoints[-1],
                             'waypoints': '|'.join(waypoints[1:-1]),
                             'sensor': 'false'}))
    response = json.loads(urllib2.urlopen(url).read())
    if response['status'] != "OK":
        raise Exception(response['status'], waypoints)
    for route in response['routes']:
        route['overview_polyline']['points'] = \
            polydecode(route['overview_polyline']['points'])
    return response['routes']


def polydecode(encoded):
    """Decodes a polyline that was encoded using the Google Maps method.

    See http://code.google.com/apis/maps/documentation/polylinealgorithm.html

    This is a straightforward Python port of Mark McClure's JavaScript
    polyline decoder (http://moourl.com/8hucs) and Peter Chng's PHP
    polyline decode (http://moourl.com/5hddu)
    """
    encoded_len = len(encoded)
    index = 0
    array = []
    lat = 0
    lng = 0
    while index < encoded_len:
        b = 0
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index = index + 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index = index + 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng
        array.append((lat * 1e-5, lng * 1e-5))
    return array


def geocode(address):
    """Get information about an address (like latitude/longitude)
    using Google's Maps API v3
    """
    url = ('http://maps.googleapis.com/maps/api/geocode/json?' +
           urllib.urlencode({'sensor': 'false',
                             'address': address}))
    response = json.loads(urllib2.urlopen(url).read())
    if response['status'] != "OK":
        raise GeocodeException(response['status'], address)
    return response['results']


def address_to_latlng(address):
    """Shortcut function to just get lat/lng from geocode()"""
    results = geocode(address)
    if not results:
        return None, None
    else:
        loco = results[0]['geometry']['location']
        return loco['lat'], loco['lng']


def haversine(lat1, lng1, lat2, lng2):
    """Calculate kilometer distance between two places on earth"""
    # convert to radians
    lng1 = float(lng1) * pi / 180
    lng2 = float(lng2) * pi / 180
    lat1 = float(lat1) * pi / 180
    lat2 = float(lat2) * pi / 180
    # haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    km = 6367 * c
    return km


if __name__ == '__main__':
    from pprint import pprint

    places = [{'address': '666 market st. philadelphia, pa'},
              {'address': '666 broadway, nyc'},
              {'address': 'tokyo, japan'},
              {'address': 'london, england'}]

    for place in places:
        place['geocode'] = geocode(place['address'])
        print
        print '\x1b[1m' + '=' * 70 + '\x1b[0m'
        print
        print "geocode(%r) ->" % (place['address'])
        print
        pprint(place['geocode'], indent=2)

    print
    print '\x1b[1m' + '=' * 70 + '\x1b[0m'
    print
    lat = lambda p: p['geocode'][0]['geometry']['location']['lat']
    lng = lambda p: p['geocode'][0]['geometry']['location']['lng']
    ids = range(len(places))
    combos = ((places[n1], places[n2]) for n1 in ids for n2 in ids if n1 != n2)
    for place1, place2 in combos:
        print "Distance:", place1['address']
        print "         ", place2['address']
        km = haversine(lat(place1), lng(place1), lat(place2), lng(place2))
        print "haversine(%f, %f, %f, %f) -> %f Km" % (
            lat(place1), lng(place1),
            lat(place2), lng(place2), km)
        print
