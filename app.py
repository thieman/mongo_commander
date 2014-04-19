#!/usr/bin/env python

""" Central module responsible for instantiating the other app components
and parsing command line configs. """

import sys
import logging
import argparse

from mongo_commander.data import ClusterData

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=None, help="Location of YAML config file")
    args = parser.parse_args()

    data = ClusterData(args.config)
    data.start_polling()

    import time
    while True:
        with data.lock:
            logging.info(data._dict.keys())
        time.sleep(1)

if __name__ == '__main__':
    main()
