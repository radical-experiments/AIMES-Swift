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

# pattern to select suitable profiles
regex_1='.*sander.MPI -O -i mdshort.in'
regex_2='.*sander.MPI -O -i min.in'
regex_3='pyCoCo'
regex_4='python postexec.py .*'

regex="$regex_3"

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

