#!/bin/sh

IDX=$1; shift
INPUT_SHARED_1_3=$1; shift

OUTPUT_2_2=""
IDX=0
while ! test -z "$1"
do
    IDX=$((IDX+1))
    OUTPUT_2_2_I="$1"; shift
    OUTPUT_3_1_I="output_3_1_$IDX.txt"

    cat $OUTPUT_2_2_I >> "$OUTPUT_3_1_I"; echo "3:1,$IDX" >> "$OUTPUT_3_1_I"
done

# sleep 2

