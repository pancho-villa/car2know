#!/usr/local/bin/python2.7
# encoding: utf-8
'''
car2know.closest_car -- shortdesc

car2know.closest_car is a description

It defines classes_and_methods

@author:     user_name

@copyright:  2015 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pathlib import Path
import json
import os
import sys
import time

from car2know import Car, haversine


__all__ = []
__version__ = 0.1
__date__ = '2015-03-24'
__updated__ = '2015-03-26'

DEBUG = 1
TESTRUN = 0
PROFILE = 0


def read_cars(path=None):
    '''reads in all the json files in the current directory'''
    all_cars = {}
    if path is None:
        p = Path()
    else:
        p = Path(path)
    for car_file in sorted(p.glob('*.json')):
        if car_file.stat().st_mtime - time.time() <= 30:
            with car_file.open() as cf:
                for line in cf:
                    last = json.loads(line.rstrip())
                all_cars[last['name']] = Car(last['name'], last['coordinates'])
        else:
            print(car_file.stat().st_mtime - time.time())
    if all_cars:
        return all_cars
    else:
        return None


def find_closest(cars, home):
    cars_and_distance = []
    for car in cars.values():
        c_coords = car.cur_location
        print(c_coords)
        print(home)
        distance = haversine(c_coords[0], c_coords[1], home[0], home[1])
        cars_and_distance.append((car.name, distance))
    return cars_and_distance

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2015 organization_name. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
#         parser.add_argument("-h", "--home", dest="home", action="store_const", help="Set location of your")
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")

        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        # Process arguments
        args = parser.parse_args()
        verbose = args.verbose
        home = [-122.363552, 47.624457]
        if verbose > 0:
            print("Verbose mode on")

        known_cars = read_cars()
        if known_cars is not None:
            print(len(known_cars))
            closest = find_closest(known_cars, home)
            print(closest)
            close = min(x[1] for x in closest)
            for x, y in closest:
                if y == close:
                    print(x, y)
        else:
            return "No cars nearby"

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'car2know.closest_car_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())