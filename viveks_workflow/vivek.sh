#!/bin/sh

error(){
    echo $*
    exit 1
}

INPUT_SHARED_1_1="input_shared_1_1.txt"
INPUT_SHARED_1_2="input_shared_1_2.txt"
INPUT_SHARED_1_3="input_shared_1_3.txt"
INPUT_SHARED_1_4="input_shared_1_4.txt"
INPUT_SHARED_1_5="input_shared_1_5.txt"

test -f $INPPUT_SHARED_1_1 || error 'INPUT_1_1 missing'
test -f $INPPUT_SHARED_1_2 || error 'INPUT_1_2 missing'
test -f $INPPUT_SHARED_1_3 || error 'INPUT_1_3 missing'
test -f $INPPUT_SHARED_1_4 || error 'INPUT_1_4 missing'
test -f $INPPUT_SHARED_1_5 || error 'INPUT_1_5 missing'

# ------------------------------------------------------------------------------
# STAGE 1
N=128
IDX=0
while test $IDX -lt $N
do
    IDX=$((IDX+1))

    OUTPUT_1_1_I="output_1_1_$IDX.txt"
    OUTPUT_1_2_I="output_1_2_$IDX.txt"
    OUTPUT_1_3_I="output_1_3_$IDX.txt"

    ./stage_1.sh $IDX $INPUT_SHARED_1_1 \
                      $INPUT_SHARED_1_2 \
                      $INPUT_SHARED_1_3 \
                      $INPUT_SHARED_1_4 \
                      $INPUT_SHARED_1_5

    test -f $OUTPUT_1_1_I || error 'OUTPUT_1_1_I missing'
    test -f $OUTPUT_1_2_I || error 'OUTPUT_1_2_I missing'
    test -f $OUTPUT_1_3_I || error 'OUTPUT_1_3_I missing'
    
    echo "stage 1 done $IDX"
done

# ------------------------------------------------------------------------------
# STAGE 2
IDX=0
while test $IDX -lt $N
do
    IDX=$((IDX+1))

    OUTPUT_1_1_I="output_1_1_$IDX.txt"

    OUTPUT_2_1_I="output_2_1_$IDX.txt"
    OUTPUT_2_2_I="output_2_2_$IDX.txt"
    OUTPUT_2_3_I="output_2_3_$IDX.txt"
    OUTPUT_2_4_I="output_2_4_$IDX.txt"

    ./stage_2.sh $IDX $INPUT_SHARED_1_3 \
                      $INPUT_SHARED_1_4 \
                      $OUTPUT_1_1_I

    test -f $OUTPUT_2_1_I || error 'OUTPUT_2_1_I missing'
    test -f $OUTPUT_2_2_I || error 'OUTPUT_2_2_I missing'
    test -f $OUTPUT_2_3_I || error 'OUTPUT_2_3_I missing'
    test -f $OUTPUT_2_4_I || error 'OUTPUT_2_4_I missing'

    echo "stage 2 done $IDX"
done

# ------------------------------------------------------------------------------
# STAGE 3
{
    OUTPUT_2_2=""
    J=1
    while test $J -le $N
    do
        OUTPUT_2_2="$OUTPUT_2_2 output_2_2_$J.txt"
        J=$((J+1))
    done

    OUTPUT_3_1="output_3_1.txt"

    ./stage_3.sh $INPUT_SHARED_1_3 \
                 $OUTPUT_2_2

    J=1
    while test $J -le $N
    do
        OUTPUT_3_1_I="output_3_1_$J.txt"
        test -f $OUTPUT_3_1_I || error 'OUTPUT_3_1_I missing'
        J=$((J+1))
    done

    echo "stage 3 done 1"
}

# ------------------------------------------------------------------------------
# STAGE 4
IDX=0
while test $IDX -lt $N
do
    IDX=$((IDX+1))

    OUTPUT_3_1_I="output_3_1_$IDX.txt"
    OUTPUT_2_1_I="output_4_1_$IDX.txt"

    ./stage_4.sh $IDX $INPUT_SHARED_1_5 \
                      $OUTPUT_3_1_I

    test -f $OUTPUT_4_1_I || error 'OUTPUT_4_1_I missing'

    echo "stage 4 done $IDX"
done

# ------------------------------------------------------------------------------

