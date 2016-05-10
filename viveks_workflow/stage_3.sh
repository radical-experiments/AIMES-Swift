#!/bin/sh

CHUNK=$1; shift
CHUNKSIZE=$1; shift
INPUT_SHARED_1_3=$1; shift

I=0
while ! test -z "$1"
do
    for f in $1
    do
        I=$((I+1))
        IDX=$((CHUNK*CHUNKSIZE+I))
        OUTPUT_2_2_I="$f"
        OUTPUT_3_1_I="output_3_1_$IDX.txt"

        cat  $OUTPUT_2_2_I >> $OUTPUT_3_1_I
        echo "3:1,$IDX"    >> $OUTPUT_3_1_I
    done
    shift
    echo
done

. $HOME/bin.rp/ve/bin/activate

radical-synapse-sample -f 10000000000


