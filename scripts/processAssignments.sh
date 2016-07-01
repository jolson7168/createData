#!/bin/bash

for i in $(seq 1 $1); do
   python ../src/processAssignments.py -c ../config/processAssignments.conf &
done;

