#!/usr/bin/env python

import logging
import sys
import time
import json
import random
import pika 
import uuid
import zlib

from ConfigParser import RawConfigParser
from datetime import datetime
from datetime import timedelta
from random import randrange
from random import randint

import pika

cfg = RawConfigParser()

def setUpRabbit(ip, port, login, password):
    credentials = pika.PlainCredentials(login, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(ip,port,'/',credentials))
    channel = connection.channel()    
    return channel

def dumpToRabbit(channel, exchange, routingKey, payload, compress = False):
    if compress:
        channel.basic_publish(exchange=exchange,routing_key=routingKey,body=zlib.compress(payload))
    else:
        channel.basic_publish(exchange=exchange,routing_key=routingKey,body=payload)


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
    desc = 'Execute createAssignments'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config_file', default='../config/createAssignments.conf',
                        help='configuration file name (*.ini format)')
    parser.add_argument('-s', '--scenario_file', default='../config/createAssignments.json',
                        help='scenario file name')

    return parser



def executeScenario(channel, scenario, logger):
    startDate = datetime.strptime(scenario["startDate"], '%Y-%m-%dT%H:%M:%S.%fZ')
    endDate = datetime.strptime(scenario["endDate"], '%Y-%m-%dT%H:%M:%S.%fZ')

    totalCount = 0
    for x in range(1, scenario["numTargets"]+1):
        if scenario["subjectIDType"] == "uuid":
            subjectID = uuid.uuid4()
        else:
            subjectID = x +startID
        now = startDate
        while now <= endDate:
            timeStart = now
            if scenario['frequency units'] == 'seconds':
                timeEnd = timeStart + timedelta(seconds = scenario['frequency'])
            elif scenario['frequency units'] == 'minutes':
                timeEnd = timeStart + timedelta(minutes = scenario['frequency'])
            elif scenario['frequency units'] == 'hours':
                timeEnd = timeStart + timedelta(hours = scenario['frequency'])
            elif scenario['frequency units'] == 'days':
                timeEnd = timeStart + timedelta(days = scenario['frequency'])
            now = timeEnd
            payload = {'id':subjectID, 'start':timeStart.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'end':timeEnd.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'size':int(scenario['payload size'])}
            if channel != None:
                dumpToRabbit(channel, scenario["routing"]["exchange"], scenario["routing"]["routingKey"], json.dumps(payload))
            else:
                print(json.dumps(payload))
 


def main(argv):

    # Overhead to manage command line opts and config file
    p = getCmdLineParser()
    args = p.parse_args()
    cfg.read(args.config_file)

    # Get the logger going
    rightNow = time.strftime("%Y%m%d%H%M%S")
    logger = initLog(rightNow)
    logger.info('Starting Run: '+time.strftime("%Y%m%d%H%M%S")+'  ==============================')
   
    # Load the scenario
    session = json.loads(open(args.scenario_file).read())

    # Execute the assignment scenarios
    if session["printOnly"] =="True":
        rabbitChannel = None
    else:
        rabbitChannel = setUpRabbit(session["target"]["ip"],int(session["target"]["port"]),session["target"]["login"],session["target"]["password"])
    for scenario in session["scenarios"]:
        executeScenario(rabbitChannel, scenario, logger)

    # Clean up
    logger.info('Done! '+time.strftime("%Y%m%d%H%M%S")+'  ==============================')

if __name__ == "__main__":
    main(sys.argv[1:])
