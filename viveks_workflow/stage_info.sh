#!/bin/sh -x

get_stats(){
    awk 'NR == 1 { max=$1; min=$1; sum=0 }
       { if ($1>max) max=$1; if ($1<min) min=$1; sum+=$1;}
       END {printf "Min: %f\tMax: %f\tAverage: %f\n", min, max, sum/NR}'
}

# pattern to select suitable profiles
regex_1='.*sander.MPI -O -i mdshort.in'
regex_2='.*sander.MPI -O -i min.in'
regex_3='pyCoCo'
regex_4='python postexec.py .*'

for idx in 1 2 3 4
do
    eval regex='$'regex_$idx
    stage="stage_$idx"
  # echo "$stage: $regex"

    echo $stage
    profiles=`grep -le "$regex" profiles/*.json`
    grep -e '^        "real":' $profiles \
        | uniq  \
        | rev \
        | cut -f 1 -d : \
        | rev \
        | cut -f 1 -d , \
        | get_stats
    echo
done

