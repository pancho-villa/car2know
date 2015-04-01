'''
Created on Mar 26, 2015

@author: paco
'''
import logging
import time
import unittest

import car2know


class Test(unittest.TestCase):


    def setUp(self):
        car2know.init_logging()
        self.logger = logging.getLogger()


    def tearDown(self):
        pass


    def testName(self):
#         cars = car2know.get_cars('seattle')
#         known_cars = {}
#         in_transit_cars = {}
        all_cars = 'RETRY'
        while True:
#             parked_cars = {}
            all_cars = 'RETRY'
            while all_cars == 'RETRY':
                all_cars = car2know.get_cars('seattle')
                time.sleep(5)
                self.logger.debug(len(all_cars))



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()