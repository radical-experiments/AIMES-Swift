#!/usr/bin/env bash

bindings='late'
bags='8 32 256 2048'

echo "Bak up current timestamps files..."
find . -type f -name '*.json' -exec bash -c 'mv -v $0 ${0/.json/.bak}' {} \;
find . -type f -name '*.json'
echo "Done."

echo "Extract timestamps from log files and save them to a json file..."
for bind in $bindings; do
    for bag in $bags; do

        cd "${bind}/${bag}"
        pwd

        while IFS= read -r -d '' file; do
            python ../../../bin/swift-timestamps.py $file $(basename ${file%.*}).json
        done < <(find . -type file -name 'swift.*.log' -print0)

        cd ../..
    done
done
echo "Done."

echo "Bak up log files..."
find . -type f -name '*.log' -exec bash -c 'mv -v $0 ${0/.log/.bak}' {} \;
find . -type f -name '*.log'
echo "Done."
