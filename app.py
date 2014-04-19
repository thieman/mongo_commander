#!/usr/bin/env python

""" Central module responsible for instantiating the other app components
and parsing command line configs. """

import argparse

from mongo_commander.data import ClusterData

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=None, help="Location of YAML config file")
    args = parser.parse_args()

    data = ClusterData(args.config)
    data.start_polling()

    import time
    while True:
        time.sleep(5)
        print data._dict.keys()

if __name__ == '__main__':
    main()
