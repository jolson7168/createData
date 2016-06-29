#!/bin/bash
mv /home/ubuntu/createData/config/processAssignments.conf.template /home/ubuntu/createData/config/processAssignments.conf
chown -R ubuntu:ubuntu /home/ubuntu/createData
sed -i "0,/<ipaddress>/s//10.240.0.5/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<login>/s//physiq01/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<password>/s//physiqmq01/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<queue>/s//testQ/" /home/ubuntu/createData/config/processAssignments.conf
sed -i "0,/<compression>/s//True/" /home/ubuntu/createData/config/processAssignments.conf
