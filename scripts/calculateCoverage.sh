#!/bin/bash

for i in $(seq 1 $1); do
   python ../src/calculateCoverage.py -c ../config/calculateCoverage.conf &
   sleep 5s
done;

