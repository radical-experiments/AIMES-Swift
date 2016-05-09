#!/bin/sh

INPUT_SHARED_1_5=$1
OUTPUT_4_1="output_4_1.txt"

IDX=0
while ! test -z "$1"
do
    for f in $1
    do
        cat  $f         >> $OUTPUT_4_1
        echo "4:1,$IDX" >> $OUTPUT_4_1
    done
    shift
done

. $HOME/bin.rp/ve/bin/activate

radical-synapse-sample -f 10000000000

