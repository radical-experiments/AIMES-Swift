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

# pattern to select suitable profiles
regex_1='.*sander.MPI -O -i mdshort.in'
regex_2='.*sander.MPI -O -i min.in'
regex_3='pyCoCo'
regex_4='python postexec.py .*'

regex="$regex_2"

# select and count profiles
profiles=`grep -le "$regex" $HOME/bin.rp/samples/*.prof`
n_profiles=`echo $profiles | wc -w`

# select a random profile
n_random=`awk "BEGIN{srand();print int($n_profiles * rand()) + 1;}"`
profile=`for profile in $profiles; do echo $profile; done | head -n $n_random | tail -n 1`
samples="${profile%.prof}.json"

test -f "$samples" || echo "$samples does not exist"
test -f "$samples" || exit 1

echo "sampling $samples"

. $HOME/bin.rp/ve/bin/activate

radical-synapse-emulate -i "$samples" || true

