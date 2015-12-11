#!/usr/bin/env bash

bindings='late'
bags='8 32 256 2048'
#timings='Tx Th TTC Tc Ti To Ts'
timings='TTC'
#pilots='1 2 3'

echo "Bak up current aggregated csv files..."
find . -type f -name '*.csv' -exec bash -c 'mv -v $0 ${0/.csv/.bak}' {} \;
find . -type f -name '*.csv'
echo "Done."

echo "Aggregate new csv files..."
get_fdata()
{

    fdata=""

    for bag in $bags; do
        fdata+="${1}/${bag}/${2} "
    done

    echo "$fdata"
}

for binding in $bindings; do

    echo -e "\n$binding"

    for timing in $timings; do

        T=${timing}.data
        fdata=$(get_fdata "$binding" "$T")
        fout=${binding}/${binding}_${timing}.csv

        # Create csv file, bags are columns
        pr -m -t -s, $fdata > $fout;

        # Add bags to the header of the csv file
        # header=$(echo ${bags} | tr ' ' ,)
        # echo $header | cat - $fout > temp && mv temp $fout

        # if [[ 'late' =~ ${binding} ]]; then

        #     for pilot in $pilots; do

        #         T="${timing}_p${pilot}.data";
        #         echo "$T";

        #         fdata=$(get_fdata "$binding" "$T")
        #         fout=${binding}/${binding}_${T%.data}.csv

        #         pr -m -t -s, $fdata > $fout;

        #     done;
        # fi;
    done
done
echo "Done."
