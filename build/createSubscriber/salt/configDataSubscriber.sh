#!/bin/bash
mv /home/ubuntu/createData/config/processAssignments.conf.template /home/ubuntu/createData/config/processAssignments.conf
chown -R ubuntu:ubuntu /home/ubuntu/createData
sed -i "0,/<ipaddress>/s//<rabbit ip>/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<log>/s//<log01>/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<pass>/s//<pass01>/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<queue>/s//<queue01>/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<compression>/s//False/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<riaktsipaddress>/s//<haproxy ip>/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<table>/s//<tableName>/" /home/ubuntu/createData/config/processAssignments.conf
