import datetime
import json
import time
import sys
import logging

from riak.client import RiakClient
from datetime import timedelta
from ConfigParser import RawConfigParser
from datetime import datetime

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
    desc = 'Execute calculateCoverage'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config_file', default='../config/calculateCoverage.conf',
                        help='configuration file name (*.ini format)')
    return parser


def unix_time_millis(dt):
    td = dt - datetime.utcfromtimestamp(0)
    return int(td.total_seconds() * 1000.0)

def getCoverage(client, table, rid, qid, t1, t2):
    fmt = "select payload from {table} where time > {t1} and time < {t2} and rid = {r_id} and qid = '{q_id}'"
    query = fmt.format(table=table, t1=t1, t2=t2, r_id = rid, q_id = qid)
    startTime = time.time()
    ts_obj = client.ts_query(table, query)
    duration = round((time.time() - startTime),3)
    coverage=[]
    for q in ts_obj.rows:
        q1 = json.loads(q[0])
        status = q1["status"]
        lastStatus =  q1["log"][len(q1["log"])-1]["status"]
        lastStatusTime = q1["log"][len(q1["log"])-1]["time"]
        coverage.append({"status":status,"time":lastStatusTime})
    return {"duration":duration,"coverage":coverage}

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

    startDate = datetime.strptime(cfg.get('coverage', 'startTime'), '%Y-%m-%d')
    t1 = unix_time_millis(startDate)
    qid = cfg.get('coverage', 'qid')
    table = cfg.get('coverage', 'table')

    client = RiakClient(host=cfg.get('riak', 'ip'), pb_port=int(cfg.get('riak', 'port')))
    epoch = datetime.utcfromtimestamp(0)

    counter = 0
    for pid in range(int(cfg.get('coverage', 'startID')), int(cfg.get('coverage', 'numIDs'))):
        for dayOffset in range(1, int(cfg.get('coverage', 'numDays'))+1):
            counter = counter +1
            t2 = unix_time_millis(startDate + timedelta(days=dayOffset))
            startTime = time.time()
            coverage = getCoverage(client, table, pid, qid, t1, t2)
            duration = round((time.time() - startTime),3)
            if (dayOffset-1)*2 == len(coverage["coverage"]):
                pass1 = "PASS!"
            else:
                pass1 = "FAIL!"
            results = "Test #{counter}: ID: {x}: total: {dur1}s, riak: {dur2}s, numdays: {numDays}, result: {result}".format(counter=counter, x=pid, dur1 = duration, dur2 = coverage["duration"], numDays = dayOffset, result = pass1)
            logger.info(results)

if __name__ == "__main__":
    main(sys.argv[1:])
