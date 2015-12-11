#!/usr/bin/env bash

bindings='late'
bags='8 32 256 2048'

experiment='.'
data='AIMES_Swift_Experiments'
raw='AIMES_Swift_Experiments/raw'
plots='AIMES_Swift_Experiments/plots'
analysis='AIMES_Swift_Experiments/analysis'

if [ ! -d ${raw} ]; then
    mkdir -p ${raw}
fi

if [ ! -d ${plots} ]; then
    mkdir -p ${plots}
fi

if [ ! -d ${analysis} ]; then
    mkdir -p ${analysis}
fi

declare -A counters

#Initialize counters to 0
for binding in $bindings; do
    for bag in $bags; do
        tag=${bag}_${binding}
        counters["c_${tag}"]=0
    done
done

#Set counters to the current maximum value
for binding in $bindings; do
    for bag in $bags; do

        tag=${bag}_${binding}
        for dir in $(find $raw -type d -name "run-${tag}_*"); do

            cutoff="run-${tag}_"
            n_iteration=${dir:${#cutoff}+${#raw}+1}

            if (( $n_iteration > "${counters["c_${tag}"]}" )); then
                counters["c_${tag}"]=${n_iteration}
            fi
        done
    done
done

echo "Set counters for current max iteration for each run type..."
for counter in "${!counters[@]}"; do echo "$counter - ${counters["$counter"]}"; done

echo
echo "Copy local runs to raw data archive..."
for binding in $bindings; do
    for bag in $bags; do

        tag=${bag}_${binding}

        for run in $(find $experiment -type d -name "exp-*"); do
            if (( `cat $experiment/$run/metadata.json | python -c 'import sys, json; print json.load(sys.stdin)["n_tasks"]' ` == ${bag} )); then

                n_iteration=$((${counters["c_${tag}"]} + 1))

                echo "cp -rpi $run $raw/run-${tag}_${n_iteration}"
                cp -rpni $run $raw/run-${tag}_${n_iteration}

                counters["c_${tag}"]=${n_iteration}

            fi
        done
    done
done

echo
echo "Copying swift log file for analysis..."
for binding in $bindings; do
    for bag in $bags; do

        tag=${bag}_${binding}

        for run in $(find ${raw} -type d -name "run-${tag}_*"); do

            if [ ! -d ${analysis}/${binding}/${bag} ] ; then
                mkdir -p ${analysis}/${binding}/${bag}
            fi

            cp -pnv ${run}/swift.log ${analysis}/${binding}/${bag}/swift.`gdate +%s%N`.log

        done
    done
done

echo "Done."
