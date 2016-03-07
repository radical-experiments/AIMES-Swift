#!/bin/bash


var1="input_data_00"
var2="input_data_0"
var3="input_data_"
end=".txt"

for i in `seq 1000 2023`; do

	touch "$var3$i$end"
for j in `seq 1 5`; do

	echo "DUMMY_FILE" >> "$var3$i$end"

done
done
