#!/usr/bin/env python

import logging
import sys
import time
import json
import random

from ConfigParser import RawConfigParser
from datetime import datetime
from datetime import timedelta
from random import randrange


cfg = RawConfigParser()

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
    desc = 'Execute createData'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config_file', default='../config/createData.conf',
                        help='configuration file name (*.ini format)')
    parser.add_argument('-s', '--scenario_file', default='../config/input.json',
                        help='scenario file name')

    return parser

def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)

def getResults(result):
    retval = ""
    for item in result:
        retval = retval+str(item)+","
    retval =  retval[0:len(retval)-1]
    if "," in retval:
        retval = '"'+retval+'"'
    return retval

def delimitResults(results):
    retval = ""
    for result in results:
        retval = retval + getResults(result["results"])+","
    return retval[0:len(retval)-1]+"\n"

def dumpToFile(data, logger):
    filename = cfg.get('output', 'outputPath')+"/" + cfg.get('output', 'outputName') + "." + cfg.get('output', 'outputFormat')
    file = open(filename, "w")
    for item in data:
        line = str(item["id"])+", "+str(item["startTime"])+","+str(item["endTime"])+","+delimitResults(item["results"])
        file.write(line)
    file.close()


def executeScenario(scenario, logger):
    data=[]
    startDay = datetime.strptime(scenario["startDate"],'%b %d, %Y')
    numDays = scenario["numDays"]
    for thisItem in range(0, scenario["numThings"]):
        for day in range (0, scenario["numDays"]):
            today = startDay+timedelta(days=day)
            for instance in range (0, scenario["frequency"]):
                miss = False
                if randrange(0, 100) < scenario["probMiss"]:
                    miss = True
                if not miss:
                    startTime = random_date(today, today+timedelta(days=1))
                    endTime = startTime+timedelta(seconds=randrange(60,scenario["probDuration"]))
                    thisTest=[]
                    for item in scenario["items"]:
                        picks=[]
                        if isinstance(item["choices"], list):
                            if item["multi"] == "Y":
                                picks = random.sample(item["choices"], randrange(1, len(item["choices"])-1))
                            else:
                                picks = random.sample(item["choices"], 1)               
                        elif isinstance(item["choices"], basestring):
                            if item["choices"] == "Date":
                                picks.append((today+timedelta(days=randrange(-5,5))).strftime('%m/%d/%Y'))
                            elif item["choices"] == "Time":
                                picks.append((today+timedelta(seconds=randrange(1,60*60*24))).strftime('%H:%M'))
                            elif item["choices"] == "Datetime":
                                picks.append((today+timedelta(seconds=randrange(1,60*60*24))).strftime('%m/%d/%Y %H:%M'))
                        thisTest.append({"id":item["id"],"results":picks,"responsetime":randrange(1, scenario["probAnswerDuration"])})
                    thisOne={}
                    thisOne["id"] = thisItem
                    thisOne["startTime"] = startTime.strftime('%m/%d/%Y %H:%M:%S')
                    thisOne["endTime"] = endTime.strftime('%m/%d/%Y %H:%M:%S')
                    thisOne["results"] = thisTest
                    data.append(thisOne)
    dumpToFile(data, logger)

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
    scenario = json.loads(open(args.scenario_file).read())


    # Execute the scenario file
    executeScenario(scenario, logger)

    # Clean up
    logger.info('Done! '+time.strftime("%Y%m%d%H%M%S")+'  ==============================')

if __name__ == "__main__":
    main(sys.argv[1:])
