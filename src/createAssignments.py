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

def dumpToRabbit(channel, exchange, routingKey, payload, compress):
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


def processInput(scenario, startTime, logger):
    thisTest=[]
    miss = False
    currentTime = None
    if randrange(0, 100) < scenario["probMiss"]:
        miss = True
    if not miss:
        currentTime = startTime
        for item in scenario["items"]:
            picks=[]
            if isinstance(item["choices"], list):
                if item["multi"] == "Y":
                    picks = random.sample(item["choices"], randrange(1, len(item["choices"])-1))
                else:
                    picks = random.sample(item["choices"], 1)               
            elif isinstance(item["choices"], basestring):
                if item["choices"] == "Date":
                    picks.append((startTime+timedelta(days=randrange(-5,5))).strftime('%Y-%m-%d'))
                elif item["choices"] == "Time":
                    picks.append((startTime+timedelta(seconds=randrange(1,60*60*24))).strftime('%H:%M'))
                elif item["choices"] == "Datetime":
                    picks.append((startTime+timedelta(seconds=randrange(1,60*60*24))).strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            if scenario["answerDuration"]["type"] == "random":
                responseTime = randrange(1, scenario["answerDuration"]["seconds"])
            else:
                responseTime = scenario["answerDuration"]["seconds"]
            thisTest.append({"value":picks,"start":currentTime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),"end":(currentTime+timedelta(seconds=responseTime)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
            currentTime = currentTime + timedelta(seconds=responseTime)
        status = "completed"
    else:
        status = "expired"
        thisTest = None
    return thisTest, status, currentTime

def executeScenario(channel, scenario, logger):
    betweenDays = int(scenario["scheduleFreq"])
    numTimesPerDay =  len(scenario["scheduleTimes"])
    assignmentDate = datetime.strptime(scenario["assignmentTime"], '%Y-%m-%dT%H:%M:%S.%fZ')
    compressOption = False
    if scenario["compress"] == "True":    
        compressOption = True
    totalCount = 0
    if "startID" in scenario:
        startID = int(scenario["startID"])
    else:
        startID = 0
    for x in range(1, scenario["numTargets"]+1):
        if scenario["subjectIDType"] == "uuid":
            subjectID = uuid.uuid4()
        else:
            subjectID = x +startID
        for numDays in range(1, scenario["numDays"]+1):
            currentDay = assignmentDate + timedelta(days=numDays)
            for perDay in range(1, numTimesPerDay+1):
                for qSource in scenario["qSource"]:
                    if ((numDays % (betweenDays)) == 0):
                        # do a test
                        payload = {}
                        payload["questionnaire_assignment_id"] = scenario["assignmentID"]
                        payload["questionnaire_response_id"] = str(uuid.uuid4())
                        payload["assigned_date"] = assignmentDate.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        if isinstance(subjectID, int):
                            payload["subject_id"] = subjectID
                        else:
                            payload["subject_id"] = str(subjectID)
                        payload["questionnaire_id"] = qSource["qSourceID"]
                        if scenario["scheduleTimes"][perDay-1] == "Random":
                            offset = randint(0,86400)
                        else:
                            offset = scenario["scheduleTimes"][perDay-1] *60*60
                        startTime = currentDay + timedelta(seconds=offset)    
                        #payload["execute_on"] = startTime.strftime('%Y-%m-%d %H:%M:%S')
                        payload["responses"], payload["status"], completedTime = processInput(qSource,startTime, logger)
                        # Subroutine this, please...
                        log = []
                        logEntry = {}
                        availableTime = startTime - timedelta(seconds=randrange(1,60*40))
                        logEntry["status"] = "Available"
                        logEntry["time"] = availableTime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        log.append(logEntry)
                        if payload["status"] == "expired":
                            if randrange(0, 100) > 20:
                                logEntry = {}
                                logEntry["status"] = "In Progress"
                                logEntry["time"] = startTime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                                log.append(logEntry)
                            logEntry = {}
                            logEntry["status"] = "Expired"
                            logEntry["time"] = (availableTime + timedelta(seconds=randrange(1,60*60*4))).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                            log.append(logEntry)
                        else:
                            logEntry = {}
                            logEntry["status"] = "In Progress"
                            logEntry["time"] = startTime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                            log.append(logEntry)
                            logEntry = {}
                            logEntry["status"] = "Completed"
                            logEntry["time"] = completedTime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                            log.append(logEntry)
                            logEntry = {}
                            logEntry["status"] = "Submitted"
                            logEntry["time"] = (completedTime + timedelta(seconds=randrange(1,60*3))).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                            log.append(logEntry)
                        payload["log"] = log
                        if channel != None:
                            dumpToRabbit(channel, scenario["routing"]["exchange"], scenario["routing"]["routingKey"], json.dumps(payload), compressOption)
                        #else:
                            #print(json.dumps(payload))
                            
                        totalCount = totalCount+1
                        if (totalCount % 1000) == 0:
                                logger.info('Wrote '+str(totalCount) +' records to RabbitMQ')



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
