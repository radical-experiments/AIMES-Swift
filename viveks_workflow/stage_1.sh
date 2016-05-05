#!/bin/sh

IDX=$1
INPUT_SHARED_1_1=$2
INPUT_SHARED_1_2=$3
INPUT_SHARED_1_3=$4
INPUT_SHARED_1_4=$5
INPUT_SHARED_1_5=$6

OUTPUT_1_1_I="output_1_1_$IDX.txt"
OUTPUT_1_2_I="output_1_2_$IDX.txt"
OUTPUT_1_3_I="output_1_3_$IDX.txt"

cat $INPUT_SHARED_1_1 >> $OUTPUT_1_1_I; echo "1:$IDX" >> $OUTPUT_1_1_I
cat $INPUT_SHARED_1_2 >> $OUTPUT_1_2_I; echo "1:$IDX" >> $OUTPUT_1_2_I
cat $INPUT_SHARED_1_3 >> $OUTPUT_1_3_I; echo "1:$IDX" >> $OUTPUT_1_3_I

. $HOME/bin.rp/ve/bin/activate

radical-synapse-sample -f 1000000000000

