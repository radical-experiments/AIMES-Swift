# Swift experiments

In standalone mode, Swift uses the Coaster System to execute tasks on pilots. 

Related paper at: https://bitbucket.org/shantenujha/aimes

* [Experimental Workflow](#experimental-workflow)
* [Data Analysis Workflow](#data-analysis-workflow)

## Experimental Workflow

1. Prerequisites:

  * Execute the experiment from a machine with a **public IP**.
  * Coreutils. Under OSX install with ```brew install coreutils```, and modify ```runner.sh``` to use ```gshuf``` instead of ```shuf``` or create a ```shuf``` symlink to ```gshuf``` with ```sudo ln -s /usr/local/bin/gshuf /usr/local/bin/shuf```.

1. Clone this repository:

  ```
  git clone git@github.com:radical-experiments/AIMES-Swift.git
  ```

1. Download Swift:

   ```
   wget http://swift-lang.org/packages/swift-0.96.2.tar.gz
   tar xvfz swift-0.96.2.tar.gz
   ```

1. Make Swift available in your PATH:

  ```
  cd swift-0.96.2
  export PATH=$PWD/bin:$PATH
  ```

1. Set up experiment environment: To run swift only experiments, ensure that you have ssh keys setup to allow for passwordless access to stampede and gordon. You should be able to ssh to ```stampede.tacc.utexas.edu``` and ```gordon.sdsc.edu```, without a password prompt.

1. ```cd AIMES-Swift/Swift_Experiments``` and edit the following files:

  * ```swift.conf``` and set the sites where you want to run your experiment(s). For example:
    
    ```
    sites: [stampede, gordon]  # runs both sites
    sites: stampede            # runs only stampede
    ```
    
  * ```experiment.sh``` and set:
  
    ```
    REPEAT determines the times the experiment is repeated [4])
    ```
  
  * ```runner.sh``` and set:
  
    ```
    TESTLOG=test_$(date +%Y-%m-%d:%H:%M:%S).log # The name of the run log file
    SLEEPDUR=900                                # Task duration
    EMAIL_TO="matteo.turilli@gmail.com"         # E-mail where to send exec report
    EMAIL_FROM="matteo.turilli@gmail.com"
    ```

1. Run the experiments:

  ```
  export GLOBUS_HOSTNAME="YOUR_IP"
  ./test_runner_runner.sh
  ```

## Data Analysis Workflow

The analysis wrokflow is designed to be automated, reusable, and extensible. The wrokflow incrementally integrates new data to those previously collected. Raw, wrangled, and analysis data are all kept across runs preserving the reproducibility of the analysis and (to a certain extent) the provenance of the data. When needed, new analyses can be added to a single step of the workflow without altering the other steps.

1. Prerequisites: python and Bash on Linux or OSX.

1. Raw data are kept in the directory ```raw_data/name_of_resource(s)/exp-xxx```. Raw data are **NOT** uploaded to git dur to space limitations. Raw data are tarred and b2zipped into a single file for archive purposes.

1. Data wrangling. Raw data are recorded in ```swift.log```. Here an annotated sample of the logs for a task execution:

  ```
  22:57:48,775 JOB_INIT           swift            jobid=sleep-koblgxkm
  22:57:48,775 JOB_SITE_SELECT    swift            jobid=sleep-koblgxkm
  22:57:48,785 JOB_START          swift            jobid=sleep-koblgxkm host=stampede 
  22:57:48,785 JOB_TASK           Execute          jobid=sleep-koblgxkm taskid=urn:R-2-13-1453935467203 

  22:58:10,682 BLOCK_REQUESTED    RemoteLogHandler                                                                      id=0127-5804100-000000, cores=16, coresPerWorker=1, walltime=1440

  22:58:22,743 TASK_STATUS_CHANGE Execute                               taskid=urn:R-2-13-1453935467203 status=8
  22:58:22,815 TASK_STATUS_CHANGE Execute                               taskid=urn:R-2-13-1453935467203 status=1

  01:01:14,281 BLOCK_ACTIVE       RemoteLogHandler                                                                      id=0127-5804100-000000

  01:02:19,467 WORKER_ACTIVE      RemoteLogHandler                                                                 blockid=0127-5804100-000000 id=000000 node=c401-403.stampede.tacc.utexas.edu cores=16

  01:02:19,780 TASK_STATUS_CHANGE Execute                               taskid=urn:R-2-13-1453935467203 status=16 workerid=0127-5804100-000000:000000
  01:02:19,952 TASK_STATUS_CHANGE Execute                               taskid=urn:R-2-13-1453935467203 status=2  workerid=0127-5804100-000000:000000
  01:17:20,124 TASK_STATUS_CHANGE Execute                               taskid=urn:R-2-13-1453935467203 status=17
  01:17:20,267 TASK_STATUS_CHANGE Execute                               taskid=urn:R-2-13-1453935467203 status=7

  01:17:20,267 JOB_END            swift            jobid=sleep-koblgxkm

  01:17:20,664 BLOCK_SHUTDOWN     RemoteLogHandler                                                                       id=0127-5804100-000000
  01:17:20,665 WORKER_LOST        RemoteLogHandler                                                                  blockid=0127-5804100-000000 id=000000
  01:17:20,665 WORKER_SHUTDOWN    RemoteLogHandler                                                                  blockid=0127-5804100-000000 id=000000
  01:17:21,718 BLOCK_DONE         RemoteLogHandler                                                                       id=0127-5804100-000000
  ```

 The following filters the log file calculating the timings for each relevant event. Each event is delimited by a state transition:

   ```
   for d in `find . -iname "exp-*"`; do echo "python ../../bin/swift-timestamps.py $d/swift.log $d/durations.json"; python ../../bin/swift-timestamps.py $d/swift.log $d/durations.json; done
   ```

1. Copy wrangled data to the analysis directory:

  ```
  for d in `find . -iname "exp-*"`; do cp $d/durations.json ../../analysis/stampede_gordon/$d-durations.json; done
  ```

1. Run the analusis on the wrangled data:

  ```
  cd ../../analysis/stampede_gordon/
  python ../../bin/swift-timings.py .
  ```

1. Analysis data are collected into files, each file named as the timing measured. At the moment, we measure only time to completion (TTC), so ```swift-timings.py``` saves ttc for each run in the indicated directory to a file named ```TTC.csv```. The csv file contains a first raw with the size of the bag run by the experiment and then raws of data for each size of the bag. The csv files can be further aggregated/filtered to produce the desired diagrams.
