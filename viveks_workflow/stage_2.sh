#!/bin/sh

IDX=$1
INPUT_SHARED_1_3=$2
INPUT_SHARED_1_4=$3
OUTPUT_1_1_I=$4

OUTPUT_2_1_I="output_2_1_$IDX.txt"
OUTPUT_2_2_I="output_2_2_$IDX.txt"
OUTPUT_2_3_I="output_2_3_$IDX.txt"
OUTPUT_2_4_I="output_2_4_$IDX.txt"

cat $INPUT_SHARED_1_3 >> $OUTPUT_2_1_I; echo "2:$IDX" >> $OUTPUT_2_1_I
cat $INPUT_SHARED_1_4 >> $OUTPUT_2_2_I; echo "2:$IDX" >> $OUTPUT_2_2_I
cat $OUTPUT_1_1_I     >> $OUTPUT_2_3_I; echo "2:$IDX" >> $OUTPUT_2_3_I
cat $OUTPUT_1_1_I     >> $OUTPUT_2_4_I; echo "2:$IDX" >> $OUTPUT_2_4_I

. $HOME/bin.rp/ve/bin/activate

radical-synapse-sample -f 1000000000000


