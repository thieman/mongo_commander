#!/usr/bin/env python

""" Central module responsible for instantiating the other app components
and parsing command line configs. """

import sys
import logging
import argparse
import time

from mongo_commander.data import ClusterData
from mongo_commander.windows import WindowManager

logging.basicConfig(filename='app.log', level=logging.INFO)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=None, help="Location of YAML config file")
    args = parser.parse_args()

    data = ClusterData(args.config)
    data.start_polling()

    windows = WindowManager(data)
    windows.start()

if __name__ == '__main__':
    main()
