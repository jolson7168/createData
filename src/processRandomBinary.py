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

import pika

cfg = RawConfigParser()
gclient = RiakClient()
epoch = datetime.utcfromtimestamp(0)
gtable = ""
glogname = ""


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
    desc = 'Execute processRandomBinary'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config_file', default='../config/processRandomBinary.conf',
                        help='configuration file name (*.ini format)')

    return parser

def toUnixTime(dt):
    dt1 = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')
    td = dt1 - datetime.fromtimestamp(0)
    return int(td.total_seconds() * 100000.0)

def processRecord(id1, start, end, data):
    print('----------------------------------------------------------------')
    print('{0}: {1} - {2} / {3}'.format(id1, start, end, data))

def sendToRiakTS(dataSet1):
    global gtable
    global gclient
    logger = logging.getLogger("processRandomBinary")
    try:   
        startTime = time.time()
        table_object = gclient.table(gtable).new(dataSet1)
        result = table_object.store()
        duration = round((time.time() - startTime),3)
        logger.info("Record written: {0}, Time: {1}, Key: {2}".format(result, duration, dataSet1[0][1]))
    except Exception as e:
        print("Error: {}".format(e))

def getRandomBinary(size, units):
    if units == 'b':
        return os.urandom(size)
    elif units == 'kb':
        return os.urandom(size*1024)
    elif units == 'mb':
        return os.urandom(size*1024*1024)


def processData(ch, method, properties, body):
    results = []
    #s1 = zlib.decompress(body)
    payload = json.loads(body)
    #record = (payload['id'], toUnixTime(payload['start']), toUnixTime(payload['end']), getRandomBinary(payload['size'],payload['sizeUnits']))
    record = [(payload['id'], toUnixTime(payload['start']), getRandomBinary(payload['size'],payload['sizeUnits']))]
    sendToRiakTS(record)
    ch.basic_ack(delivery_tag = method.delivery_tag)

def main(argv):
    global gtable
    global gclient

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
    gclient = RiakClient(protocol='pbc',nodes=[{ 'host': cfg.get('riakts', 'ip'), 'pb_port': int(cfg.get('riakts', 'port')) }])
    gtable = cfg.get('riakts','table')

    # Get Rabbit going
    rabbitChannel = setUpRabbit(cfg.get('rabbitmq', 'ip'), int(cfg.get('rabbitmq', 'port')),cfg.get('rabbitmq', 'login'),cfg.get('rabbitmq', 'password'),cfg.get('rabbitmq', 'queue'))

    logger.info('RabbitMQ channel initialized...')
    rabbitChannel.basic_qos(prefetch_count=1)
    rabbitChannel.basic_consume(processData, queue=cfg.get('rabbitmq', 'queue'))
    logger.info('RabbitMQ consumer initialized...')
    rabbitChannel.start_consuming()


    # Clean up
    logger.info('Done! '+time.strftime("%Y%m%d%H%M%S")+'  ==========================')

if __name__ == "__main__":
    main(sys.argv[1:])