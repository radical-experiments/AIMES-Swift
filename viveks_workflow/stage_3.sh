#!/bin/sh

INPUT_SHARED_1_3=$1; shift

IDX=0
while ! test -z "$1"
do
    for f in $1
    do
        IDX=$((IDX+1))
        OUTPUT_2_2_I="$f"
        OUTPUT_3_1_I="output_3_1_$IDX.txt"

        cat $OUTPUT_2_2_I >> "$OUTPUT_3_1_I"; echo "3:1,$IDX" >> "$OUTPUT_3_1_I"
    done
    shift
done

# sleep 2
