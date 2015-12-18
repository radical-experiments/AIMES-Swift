#!/bin/bash

TESTLOG=test_$(date +%Y-%m-%d:%H:%M:%S).log
SLEEPDUR=900
AIMES_CONFIG=conf/yadu_test_config.json

arg_generate_full()
{
cat <<EOF | shuf &> task.count
8
16
32
64
128
256
512
1024
2048
EOF
}

arg_generate_test()
{
cat <<EOF | shuf &> task.count
8
32
EOF
}

execute_swift()
{
    swiftconf=$1      ; shift 1
    swiftscript=$1    ; shift 1
    task_count=$1     ; shift 1
    sleep_duration=$1 ; shift 1

    echo "Launching Swift with args : "
    echo "swift -config $swiftconf $swiftscript -N=$task_count -sleep=$sleep_duration"

    swift -config $swiftconf $swiftscript -N=$task_count -sleep=$sleep_duration

    if [ "$?" == "0" ]
    then
        echo "Swift run completed successfully"
        last_rundir=$(ls -td -- run*/ | head -n 1)
        last_aimesdir="exp-${last_rundir#run}"

        mkdir $last_aimesdir
        echo "Creating $last_aimesdir"

        cp $last_rundir/swift.log $last_aimesdir/
        cp $last_rundir/swift.out $last_aimesdir/
        cat <<EOF > $last_aimesdir/metadata.json
{
  "n_tasks": $task_count,
  "cores": {
    [$task_count, 1]
  },
  "durations": {
    [$task_count, $sleep_duration]
  }
}
EOF
    else
        echo "Test failed for args $swiftconf, $argstring"
    fi

}

#arg_generate_test
arg_generate_full
echo "Task counts : $(cat task.count)"

#execute_swift "swift.conf" "bag_of_tasks.swift" 4 10
#exit 0
for task_count in $(cat task.count)
do
    execute_swift "swift.conf" "bag_of_tasks.swift" $task_count $SLEEPDUR | tee -a $TESTLOG
done


export PATH=$HOME/notify:$PATH

cat<<EOF > message.txt
Experiment on Midway server complete.
EOF
#notify.py < message.txt

mailx -s "Test results from $HOSTNAME" -r swift@midway.rcc.uchicago.edu yadudoc1729@gmail.com < message.txt
