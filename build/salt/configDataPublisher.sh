#!/bin/bash

chown -R ubuntu:ubuntu /home/ubuntu/createData
sed -i "0,/<ipaddress>/s//10.240.0.5/" /home/ubuntu/createData/config/createAssignments01.json
sed -i "0,/<login>/s//physiq01/" /home/ubuntu/createData/config/createAssignments01.json
sed -i "0,/<password>/s//physiqmq01/" /home/ubuntu/createData/config/createAssignments01.json


