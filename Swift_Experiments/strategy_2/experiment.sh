#!/bin/bash

REPEAT=1
for i in $(seq 1 1 $REPEAT)
do
    echo "Run $i"
    echo "******************************************"
    ./runner.sh
    echo "******************************************"
done
