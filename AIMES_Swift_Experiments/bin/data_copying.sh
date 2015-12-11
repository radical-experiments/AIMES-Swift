#!/usr/bin/env bash

bindings='late'
bags='8 32 256 2048'

experiment='.'
data='AIMES_Swift_Experiments'
raw='AIMES_Swift_Experiments/raw'
plots='AIMES_Swift_Experiments/plots'
analysis='AIMES_Swift_Experiments/analysis'

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
