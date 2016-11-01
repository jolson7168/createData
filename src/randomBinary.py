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
    desc = 'Execute createRandomBinar'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config_file', default='../config/createRandomBinary.conf',
                        help='configuration file name (*.ini format)')
    parser.add_argument('-s', '--scenario_file', default='../config/createRandomBinaryf.json',
                        help='scenario file name')

    return parser

def getPayloadData(timeAmount, timeUnits, payloadSize, payloadUnits, payloadRate, payloadRateUnits):

    # Finish this!    
    if timeUnits == payloadRateUnits:
        return round(((float(timeAmount) / float(payloadRate)) * payloadSize),2)
    #else:
            

def  getPayloadFrequency(freqProfile):
    # timeOffset, timeOffsetUnits, payloadSize, payloadUnits
    if 'frequency' in freqProfile:
        return freqProfile['frequency'],freqProfile['frequency units'], freqProfile['payload size'], freqProfile['payload units']  
    else:
        random = randint(freqProfile['frequencyMin'],freqProfile['frequencyMax'])
        payloadSize = getPayloadData(random, freqProfile['frequency units'], freqProfile['payload size'], freqProfile['payload units'], freqProfile['payload rate'], freqProfile['payload rate units'])
        return random, freqProfile['frequency units'], payloadSize, freqProfile['payload units'] 

def getPayload(frequencyRules):
    if len(frequencyRules) == 1:
        return getPayloadFrequency(frequencyRules[0])
    else:
        random = randint(1,100)
        for eachFreq in frequencyRules:
            if random >= eachFreq['probability'][0] and random <= eachFreq['probability'][1]:
                return getPayloadFrequency(eachFreq)

def swapTwo(payloads, target, distance):
    temp = payloads[target]
    temp2 = payloads[distance]
    temp['orig pos'] = target
    temp2['orig pos'] = distance
    temp['new pos'] = distance
    temp2['new pos'] = target
    if 'num times swapped' in temp:
        temp['num times swapped'] = temp['num times swapped'] +1
    else:
        temp['num times swapped'] = 1
    if 'num times swapped' in temp2:
        temp2['num times swapped'] = temp2['num times swapped'] +1
    else:
        temp2['num times swapped'] = 1
    payloads[target] = temp2
    payloads[distance]= temp
    return payloads


def shuffleScenario(shuffleScenario, payloads):
    for x in range(0, len(payloads)-1):
        randomNum = randint(1, 100)
        if randomNum <= shuffleScenario['probability']:
            randomShift = randint(-1 * shuffleScenario['distance'], shuffleScenario['distance'])
            if randomShift <= x :
                payloads = swapTwo(payloads, x, x + abs(randomShift)) 
            elif (randomShift + x) > len(payloads):
                payloads = swapTwo(payloads, x, x + randomShift * -1)
            else:
                payloads = swapTwo(payloads, x, x + randomShift)

    return payloads


def executeScenario(channel, scenario, logger):
    startDate = datetime.strptime(scenario["startDate"], '%Y-%m-%dT%H:%M:%S.%fZ')
    endDate = datetime.strptime(scenario["endDate"], '%Y-%m-%dT%H:%M:%S.%fZ')

    totalCount = 0
    for x in range(1, scenario["numTargets"]+1):
        if scenario["subjectIDType"] == "uuid":
            subjectID = str(uuid.uuid4())
        elif isinstance(scenario["subjectIDType"], (int, long)):
            subjectID = x +startID
        else:
            startAt = 0
            if 'startID' in scenario:
                startAt = int(scenario['startID'])
            if (startAt + x) < 10:
                xS = '{0}{1}'.format('0',startAt+x)
            else:
                xS = '{0}'.format(startAt+x)
            subjectID = '{0}{1}'.format(scenario["subjectIDType"], xS)
        now = startDate
        payloads = []
        pos = 0
        while now <= endDate:
            timeStart = now
            timeOffset, timeOffsetUnits, payloadSize, payloadUnits = getPayload(scenario['frequency'])
            if timeOffsetUnits == 'seconds':
                timeEnd = timeStart + timedelta(seconds = timeOffset)
            elif timeOffsetUnits == 'minutes':
                timeEnd = timeStart + timedelta(minutes = timeOffset)
            elif timeOffsetUnits == 'hours':
                timeEnd = timeStart + timedelta(hours = timeOffset)
            elif timeOffsetUnits == 'days':
                timeEnd = timeStart + timedelta(days = timeOffset)
            now = timeEnd
            payloads.append({'id':subjectID, 'start':timeStart.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'end':timeEnd.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'size':payloadSize, 'sizeUnits':payloadUnits,'pos':pos})
            pos = pos +1
            

        if 'shuffle' in scenario:
            payloads = shuffleScenario(scenario['shuffle'], payloads)
        pos = 0     
        for payload in payloads:
            if channel != None:
                dumpToRabbit(channel, scenario["routing"]["exchange"], scenario["routing"]["routingKey"], json.dumps(payload))
            else:
                print('{0}: {1}'.format(pos, json.dumps(payload)))
                pos = pos + 1


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

    # Execute the scenarios
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
