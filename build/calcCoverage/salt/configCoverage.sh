#!/bin/bash
mv /home/ubuntu/createData/config/calculateCoverage.conf.template /home/ubuntu/createData/config/calculateCoverage.conf
chown -R ubuntu:ubuntu /home/ubuntu/createData
sed -i "0,/<RiakTS IP>/s//<haproxy ip>/" /home/ubuntu/createData/config/calculateCoverage.conf
sed -i "0,/<qid>/s//<quidID>/" /home/ubuntu/createData/config/calculateCoverage.conf
sed -i "0,/<table>/s//<tableName>/" /home/ubuntu/createData/config/calculateCoverage.conf
sed -i "0,/<startTime>/s//<startTime1>/" /home/ubuntu/createData/config/calculateCoverage.conf
sed -i "0,/<numDays>/s//<numberOfDays>/" /home/ubuntu/createData/config/calculateCoverage.conf
sed -i "0,/<numIDs>/s//<numberOfIDs>/" /home/ubuntu/createData/config/calculateCoverage.conf
sed -i "0,/<startID>/s//<startOnID>/" /home/ubuntu/createData/config/calculateCoverage.conf
