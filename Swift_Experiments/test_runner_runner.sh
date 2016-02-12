#!/bin/bash

REPEAT=4
for i in $(seq 1 1 $REPEAT)
do
    echo "Run $i"
    echo "******************************************"
    ./test_runner.sh
    echo "******************************************"
done
