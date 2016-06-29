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

def setUpRabbit(ip, port, login, password, queueName):
    credentials = pika.PlainCredentials(login, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(ip,port,'/',credentials))
    channel = connection.channel()  
    channel.queue_declare(queue=queueName, durable=True)  
    return channel


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
    desc = 'Execute processAssignments'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config_file', default='../config/processAssignments.conf',
                        help='configuration file name (*.ini format)')

    return parser

def sendToRiakTS(payloadJSON):
    payload = json.loads(payloadJSON)
    id1 = payload["subject_id"]
    event = "questionnaire response"
    timestr = payload["log"][(len(payload["log"])-1)]["time"]
    time = datetime.strptime(timestr, '%Y-%m-%dT%H:%M:%S.%fZ')
    newRow = [id1, event, time, payloadJSON]
    #print(newRow)

def processAssignment(ch, method, properties, body):
    jsonString = zlib.decompress(body)
    sendToRiakTS(jsonString)
    ch.basic_ack(delivery_tag = method.delivery_tag)

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

    # Execute the assignment scenarios
    rabbitChannel = setUpRabbit(cfg.get('rabbitmq', 'ip'), int(cfg.get('rabbitmq', 'port')),cfg.get('rabbitmq', 'login'),cfg.get('rabbitmq', 'password'),cfg.get('rabbitmq', 'queue'))


    rabbitChannel.basic_qos(prefetch_count=1)
    rabbitChannel.basic_consume(processAssignment, queue=cfg.get('rabbitmq', 'queue'))

    rabbitChannel.start_consuming()


    # Clean up
    logger.info('Done! '+time.strftime("%Y%m%d%H%M%S")+'  ==============================')

if __name__ == "__main__":
    main(sys.argv[1:])
