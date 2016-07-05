#!/bin/bash
mv /home/ubuntu/createData/config/processAssignments.conf.template /home/ubuntu/createData/config/processAssignments.conf
chown -R ubuntu:ubuntu /home/ubuntu/createData
sed -i "0,/<ipaddress>/s//104.196.2.20/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<log>/s//physiq01/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<pass>/s//physiqmq01/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<queue>/s//testQ/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<compression>/s//False/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<riaktsipaddress>/s//<haproxy ip>/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<table>/s//responses01/" /home/ubuntu/createData/config/processAssignments.conf
