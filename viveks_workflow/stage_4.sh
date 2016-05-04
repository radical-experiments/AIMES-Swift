#!/bin/sh

IDX=$1
INPUT_SHARED_1_5=$2
OUTPUT_3_1_I=$3

OUTPUT_4_1_I="output_4_1_$IDX.txt"

cat  $INPUT_SHARED_1_5 >> $OUTPUT_4_1_I
cat  $OUTPUT_3_1_I     >> $OUTPUT_4_1_I
echo "4:$IDX"          >> $OUTPUT_4_1_I

. $HOME/bin.rp/ve/bin/activate

radical-synapse-sample -f 10000000000

