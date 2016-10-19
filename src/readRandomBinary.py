#!/usr/bin/env python

from __future__ import print_function

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
PRECISION = 1000.0
MAX_PAYLOAD_SIZE = 1024
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
    parser.add_argument('-s', '--scenario_file', default='../config/readRandomBinary.json',
                        help='scenario file name')

    return parser


def toUnixTime(dt, precision = 1000.0):
    dt1 = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')
    td = dt1 - datetime.fromtimestamp(0)
    return int(td.total_seconds() * precision)

def fromUnixTime(dt, precision = 1000.0):
    return datetime.fromtimestamp(dt/precision).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def splitIntervals(start, end, interval):
    retval = []
    if (end - start) >= interval:
        now = start
        offset = 0 #int(interval *.20)
        while now < end:
            if (now + interval) > end:
                retval.append((now, end))
            else:
                retval.append((now, now+interval - offset))
            now = now + interval - offset
    else:
        retval.append((start,end))
    return retval

def executeQuery(client, table, asset, start, end, maxInt, expectedPayloadSize, destination):
    intervals = []
    results = []
    totQueries = 0
    retries = 0
    if (end - start) >= maxInt:
        queryStart = time.time()
        intervals = splitIntervals(start, end, maxInt)
        for interval in intervals:
            fmt = "select data from {3} where time >= {0} and time < {1} and id ='{2}'".format(interval[0], interval[1], asset, table)
            done = False
            retries = 0
            while (not done) and (retries <=5):
                try:
                    data_set = client.ts_query(table, fmt)
                    done = True
                except RiakException as e:
                    if 'no response from backend' in e:
                        pass
                        retries = retries +1
                    else
                        raise e
            results.append(data_set.rows)
        queryDuration = round((time.time() - queryStart),3)
        totQueries = len(intervals)
    else:
        fmt = "select data from {3} where time >= {0} and time < {1} and id ='{2}'".format(start, end, asset, table)
        queryStart = time.time()
        done = False
        retries = 0
        while (not done) and (retries <=5):
            try:
                data_set = client.ts_query(table, fmt)
                done = True
            except RiakException as e:
                if 'no response from backend' in e:
                    pass
                    retries = retries +1
                else
                    raise e
            
        queryDuration = round((time.time() - queryStart),3)
        results.append(data_set.rows)
        totQueries = 1
    tot = 0
    for result in results:
        for row in result:
            tot = tot + len(row[0])
    if tot == expectedPayloadSize:
        status = 'Pass!'
    else:
        status = 'Fail!'
    if retries == 0:
        print('{0},{1},{2},{3},{4},{5},{6}'.format(status, expectedPayloadSize, tot, fromUnixTime(start),fromUnixTime(end), queryDuration, totQueries), file = destination)
    else:
        print('{0},{1},{2},{3},{4},{5},{6},{7}'.format(status, expectedPayloadSize, tot, fromUnixTime(start),fromUnixTime(end), queryDuration, totQueries, retries), file =
 destination)


def processRecord(id1, start, end, data):
    print('----------------------------------------------------------------')
    print('{0}: {1} - {2} / {3}'.format(id1, start, end, data))


def readRiakTS(client, tableName, startTime, endTime, assetID, expected, logger):
    qry = "SELECT data FROM {0} WHERE time >= {1} and time < {2} and id = '{3}'".format(tableName, startTime, endTime, assetID)
    try:   
        startQTime = time.time()
        data_set = client.ts_query(tableName, qry)
        riakDuration = round((time.time() - startQTime),3)
        total = ''
        for row in data_set.rows:
            total = total + row[0]
        totalDuration = round((time.time() - startQTime),3)
        if len(total) == expected:
            print('Match! T1: {2} T2: {3} rt: {0} tt: {1} e: {4}'.format(riakDuration, totalDuration, fromUnixTime(startTime, PRECISION), fromUnixTime(endTime, PRECISION), expected))
        else:
            print('Mismatch! duration: {0} expected: {1} got: {2}'.format(riakDuration, expected, len(total)))        
    except Exception as e:
        print("Error: {}".format(e))

def getPayload(amount, units):
    if units == 'bytes':
        return amount
    elif units == 'kb':
        return 1024 * amount
    elif units == 'mb':
        return 1024 * 1024 * amount


def getSource(params):
    table = params['table']
    
    if params['quantum']['units'] == 'hours':
        length = 60 * 60
    elif params['quantum']['units'] == 'days':
        length = 60 * 60 * 24
    maxInt = int(params['quantum']['precision'] * params['quantum']['maxPartitions'] * length * params['quantum']['num'] )
    return table, maxInt, params['quantum']['precision']

def getOffset(val, units, precision):
    if units == 'minutes':
        return int(precision * 60 * val)
    elif units == 'hours':
        return int(precision * 60 * 60 * val)
    elif units == 'days':
        return int(precision * 60 * 60 * 24 * val)

def executeScenario(scenario):
    client = RiakClient(protocol='pbc',nodes=[{ 'host': scenario["server"]["ip"], 'pb_port': scenario["server"]["port"] }])
    table, maxInterval, precision = getSource(scenario["dataSource"])
    asset = scenario["id"]
    destinationLoc = '{0}{1}{2}'.format('/tmp/',scenario["name"],'.csv')
    destination = open(destinationLoc,'w')
    if isinstance(scenario["interval"], dict):
        startTimeInt = toUnixTime(scenario["interval"]["startTime"], precision)
        endTimeInt = toUnixTime(scenario["interval"]["endTime"], precision)
        now = startTimeInt
        offset = getOffset(scenario["interval"]["value"],scenario["interval"]["units"], precision)
        expectedPayloadSize = getPayload(scenario["interval"]["expected"]["value"], scenario["interval"]["expected"]["units"])
        while now < endTimeInt:
            now = now + offset
            executeQuery(client, table, asset, now, now + offset, maxInterval, expectedPayloadSize, destination)
    elif isinstance(scenario["interval"], list):
        for interval in scenario["interval"]:
            expectedPayload = interval[2]
            expectedPayloadSize = getPayload(expectedPayload['value'], expectedPayload['units'])
            executeQuery(client, table, asset, toUnixTime(interval[0], precision), toUnixTime(interval[1], precision), maxInterval, expectedPayloadSize, destination)
    destination.close()
    


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

    # Load the scenarios
    scenarios = json.loads(open(args.scenario_file).read())

    for scenario in scenarios['scenarios']:
        executeScenario(scenario)

    # Clean up
    logger.info('Done! '+time.strftime("%Y%m%d%H%M%S")+'  ==========================')

if __name__ == "__main__":
    main(sys.argv[1:])
