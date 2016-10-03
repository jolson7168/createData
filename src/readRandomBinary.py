#!/usr/bin/env python

import logging
import sys
import time
import json
import random
import pika 
import uuid
import zlib
import os

from ConfigParser import RawConfigParser
from datetime import datetime
from datetime import timedelta
from random import randrange
from random import randint
from riak import RiakClient

cfg = RawConfigParser()
PRECISION = 100000.0

def currentDayStr():
    return time.strftime("%Y%m%d")

def currentTimeStr():
    return time.strftime("%H:%M:%S")

def initLog(rightNow):
    logger = logging.getLogger(cfg.get('logging', 'logName'))
    logPath=cfg.get('logging', 'logPath')
    logFilename=cfg.get('logging', 'logFileName')  
    hdlr = logging.FileHandler(logPath+rightNow+logFilename)
    formatter = logging.Formatter(cfg.get('logging', 'logFormat'),cfg.get('logging', 'logTimeFormat'))
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    logger.setLevel(logging.INFO)
    return logger

def getCmdLineParser():
    import argparse
    desc = 'Execute readRandomBinary'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config_file', default='../config/readRandomBinary.conf',
                        help='configuration file name (*.ini format)')

    return parser


def toUnixTime(dt, precision):
    dt1 = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')
    td = dt1 - datetime.fromtimestamp(0)
    return int(td.total_seconds() * precision)

def fromUnixTime(dt, precision):
    return datetime.fromtimestamp(dt/precision).strftime("%Y-%m-%dT%H:%M:%S.%fZ")




def processRecord(id1, start, end, data):
    print('----------------------------------------------------------------')
    print('{0}: {1} - {2} / {3}'.format(id1, start, end, data))

def readRiakTS(client, tableName, startTime, endTime, assetID, expected, logger):
    qry = "SELECT data FROM {0} WHERE time >= {1} and time < {2} and assetid = '{3}'".format(tableName, startTime, endTime, assetID)
    #print(qry)
    try:   
        startQTime = time.time()
        data_set = client.ts_query(tableName, qry)
        riakDuration = round((time.time() - startQTime),3)
        total = ''
        for row in data_set.rows:
            total = total + row[0]
        totalDuration = round((time.time() - startQTime),3)
        if len(total) == expected:
            print('Match! T1: {2} T2: {3} rt: {0} tt: {1} e: {4}'.format(riakDuration, totalDuration, fromUnixTime(startTime, PRECISION), fromUnixTime(endTime, PRECISION)), expected)
        else:
            print('Mismatch! duration: {0} expected: {1} got: {2}'.format(riakDuration, expected, len(total)))        
        #logger.info("Record written: {0}, Time: {1}, Key: {2}".format(result, riakduration, dataSet1[0][1]))
    except Exception as e:
        print("Error: {}".format(e))


def main(argv):

    # Overhead to manage command line opts and config file
    p = getCmdLineParser()
    args = p.parse_args()
    cfg.read(args.config_file)

    # Get the logger going
    glogname = cfg.get('logging', 'logName')
    rightNow = time.strftime("%Y%m%d%H%M%S")
    logger = initLog(rightNow)
    logger.info('Starting Run: '+time.strftime("%Y%m%d%H%M%S")+'  =========================')

    # Get Riak going    
    client = RiakClient(protocol='pbc',nodes=[{ 'host': cfg.get('riakts', 'ip'), 'pb_port': int(cfg.get('riakts', 'port')) }])
    table = cfg.get('riakts','table')
    startDate = toUnixTime('2016-01-02T00:00:00.00000Z',PRECISION)
    endDate = toUnixTime('2016-01-02T23:59:59.99999Z',PRECISION)


    blockSize = 1024        # kb
    intervalSize = 450      # seconds
    numIntervals = 24*60*60 / intervalSize    # a day
    interval = int(intervalSize * PRECISION * numIntervals)
    expected = int((blockSize*1024)*numIntervals)
    now = startDate
    while now < endDate:
        #readRiakTS(client, table, fromUnixTime(now,PRECISION), fromUnixTime(now+interval,PRECISION), 'asset01', expected, logger)
        readRiakTS(client, table, now, now+interval, 'asset01', expected, logger)
        now = now + interval

    # Clean up
    logger.info('Done! '+time.strftime("%Y%m%d%H%M%S")+'  ==========================')

if __name__ == "__main__":
    main(sys.argv[1:])
