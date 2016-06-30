#!/bin/bash

chown -R ubuntu:ubuntu /home/ubuntu/createData
sed -i "0,/<ipaddress>/s//10.240.0.5/" /home/ubuntu/createData/config/createCoverage.json
sed -i "0,/<log>/s//physiq01/" /home/ubuntu/createData/config/createCoverage.json
sed -i "0,/<pass>/s//physiqmq01/" /home/ubuntu/createData/config/createCoverage.json
sed -i "0,/<ipaddress>/s//10.240.0.5/" /home/ubuntu/createData/config/createRandom.json
sed -i "0,/<log>/s//physiq01/" /home/ubuntu/createData/config/createRandom.json
sed -i "0,/<pass>/s//physiqmq01/" /home/ubuntu/createData/config/createRandom.json


