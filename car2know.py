"""
Created on Feb 19, 2014

@author: paco
"""
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from logging.handlers import RotatingFileHandler
from urllib.error import URLError
import http.client
import json
import logging
import math
import random
import signal
import sys
import time
import urllib.request

logger = logging.getLogger(__name__)


def sigint_handler(signal, frame):
    print('Keyboard Interrupt Caught! Exiting')
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


def init_logging(level=logging.DEBUG):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s ' +
                                  '-%(lineno)d - %(message)s')

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    rotating_handler = RotatingFileHandler('car2.log', maxBytes=20000000,
                                           backupCount=5)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    rotating_handler.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    logger.addHandler(rotating_handler)
    http.client.HTTPConnection.setdebuglevel=1


def signal_handler(signal, frame):
    logger.critical('You pressed Ctrl+C!')
    sys.exit(0)


class Car:
    """Sets up a car object with all attendant attributes"""
    def __init__(self, name, coords, fuel, home):
        self.home = home
        self.name = name
        self.fuel = fuel
        self.seen = False
        self.d_from_home = haversine(coords, self.home)
        self.cur_location = coords
        self.old_location = None
        self.updated = int(time.time())

    def update_location(self, coords, fuel):
        self.fuel = fuel
        if coords != self.cur_location:
            movement = haversine(self.cur_location, coords)
#            #There can be some jitter in its location
#            #make sure it moves over 3 meters before making a new entry
            if movement > .03:
                self.old_location = self.cur_location
                self.cur_location = coords
                self.updated = int(time.time())
                self.d_from_home = haversine(coords, self.home)
                return True
            else:
                logger.info("{} moved {}m".format(self.name, movement))
            self.cur_location = coords
        return False

    def __str__(self):
        return self.name


def get_cars(location, key):
    """Fetches all cars in a given area"""
    url = "https://www.car2go.com/api/v2.1/vehicles?loc=" + location.lower() +\
          "&oauth_consumer_key=" + key + "&format=json"
    logger.debug(url)
    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req)
    except URLError as ue:
        logger.error(ue.reason)
    except urllib.error.HTTPError as he:
        logger.error(he)
        logger.error(he.code)
        logger.error(he.reason)
    logger.debug(response.status)
    logger.debug(response.code)
    payload = response.read().decode()
    return json.loads(payload)['placemarks']


def write_out(file_name, car_data):
    """takes a car instance and appends it to a json file for record keeping"""
    local_time = time.asctime(time.localtime(time.time()))
    car_data['time'] = local_time
    with open(file_name, 'a') as file_out:
        file_out.write(json.dumps(car_data) + "\n")


def haversine(first, second):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    Source: http://gis.stackexchange.com/a/56589/15183
    """
    lon1, lat1, lon2, lat2 = first[0], first[1], second[0], second[1]
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km


def parse_args(argv=None):
    if argv:
        sys.argv.extend(argv)
    else:
        argv = sys.argv
    parser = ArgumentParser(description='finds car2go near your location',
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-a", "--latitude", dest="lat", metavar="LATITUDE",
                        help="Latitude of location [default: %(default)s]",
                        default=47.6097, nargs="?", type=float)
    parser.add_argument("-o", "--longitude", dest="long", metavar="LONGITUDE",
                        help="Longitude of location [default: %(default)s]",
                        default=122.3331, nargs="?", type=float)
    parser.add_argument("-c", "--city", dest="city", metavar="CITY",
                        help="City location you want to find cars in car2go [default: %(default)s]",
                        default='seattle', nargs="?")
    parser.add_argument("-k", "--key", dest="key", metavar="APIKEY",
                        help="API key from car2go.com", nargs="?")
    return parser.parse_args()


def main(args):
    lat = args.lat
    long = args.long
    k = args.key
    c = args.city
    logger.debug("{} {} {} {}".format(lat, long, k, c))
#     time.sleep(10)
    known_cars = {}
    in_transit_cars = {}
    broken_iter = False
    while True:
        parked_cars = {}
        all_cars = 'RETRY'
        while all_cars == 'RETRY':
            all_cars = get_cars('seattle', k)
        for entry in all_cars:
            try:
                name, location, fuel = entry['name'], entry['coordinates'], + \
                                       entry['fuel']
            except KeyError as ke:
                logger.error(ke)
                return_type = type(entry)
                logger.error("Received {} for entry".format(return_type))
                broken_iter = True
                break
            seen_count = len(all_cars)
            if name not in known_cars.keys():
                known_cars[name] = Car(name, location, fuel, [long, lat])
                write_out(name + ".json", entry)
                parked_cars[name] = known_cars.get(name)
            else:
                car = known_cars.get(name)
                parked_cars[name] = car
                if car.update_location(location, fuel):
                    write_out(name + ".json", entry)
                try:
                    in_transit_cars.pop(car.name)
                except KeyError:
                    pass
        if not broken_iter:
            logger.debug("{} seen {} known".format(seen_count, len(known_cars)))
            if seen_count < len(known_cars):
                for car in known_cars.values():
                    if car not in parked_cars.values():
                        in_transit_cars[car.name] = car
                if seen_count + len(in_transit_cars) != len(known_cars):
                    logger.debug("{} seen {} known {} in transit".format(
                             seen_count, len(known_cars), len(in_transit_cars)))
            for _, c in parked_cars.items():
                if c.d_from_home < 0.5 and c not in in_transit_cars.values():
                    logger.info("{} {:.2f}km fuel: {}".format(c.name,
                                                              c.d_from_home,
                                                              c.fuel))

            logger.info("NEW ENTRIES********************")
            time.sleep(20)

if __name__ == '__main__':
    init_logging()
    sys.exit(main(parse_args()))

