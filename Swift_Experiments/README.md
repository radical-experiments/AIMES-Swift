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

1. Data wrangling. Raw data are recorded in ```swift.log```. Here an cleaned up sample of the logs for a task execution:

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

  01:17:20,664 BLOCK_SHUTDOWN                                                                            id=0127-5804100-000000
  01:17:20,665 WORKER_LOST        RemoteLogHandler                                                                  blockid=0127-5804100-000000 id=000000
  01:17:20,665 WORKER_SHUTDOWN    RemoteLogHandler                                                                  blockid=0127-5804100-000000 id=000000
  01:17:21,718 BLOCK_DONE         RemoteLogHandler                                                                       id=0127-5804100-000000
  ```
  
 Description of relevant log entries:
 ```
 | #  | Log tag            | Location           | Component |
 |----|--------------------|--------------------|-----------|
 | 1  | JOB_INIT           | Workstation (WS)   | Swift     |
 | 2  | JOB_SITE_SELECT    | WS                 | Swift     |
 | 3  | JOB_START          | WS                 | Swift     |
 | 4  | JOB_TASK           | Head node (HN)     | Coaster   |
 | 5  | BLOCK_REQUESTED    | HN                 | Coaster   |
 | 6  | TASK_STATUS_CHANGE | HN                 | Coaster   |
 | 7  | TASK_STATUS_CHANGE | HN                 | Coaster   | 
 | 7  | BLOCK_ACTIVE       | Compute nodes (CN) | LRMS      |
 | 8  | WORKER_ACTIVE      | CN                 | Worker(s) |
 | 9  | TASK_STATUS_CHANGE | HN, WS, CN         | Coaster   |
 | 10 | TASK_STATUS_CHANGE | HN, CN             | Worker    | 
 | 11 | TASK_STATUS_CHANGE | HN, CN, (WS?)      | Coaster   | 
 | 12 | TASK_STATUS_CHANGE | HN                 | Coaster   | 
 | 13 | JOB_END            | WS                 | Swift     | 
 | 14 | BLOCK_SHUTDOWN     | HN                 | Coaster   | 
 | 15 | WORKER_SHUTDOWN    | HN                 | Coaster   | 
 | 16 | BLOCK_DONE         | HN                 | Coaster   | 

 Descriptions
 ------------
 
 1.  Creates a job.
 2.  Selects a site for that job.
 3.  Schedules that job on the selected site (meaning that is scheduled, 
      not that has started to execute it).
 4.  Gets the job on the selected site and assigns to it a taskid. For 
      Coaster, a job is a task.
 5.  Submits to the local LRMS one or more blocks depending on the amount 
      of tasks it gets, the user configuration, and its own algorithms. 
      Blocks are therefore jobs on a resource LRMS.
 6.  (Meanwhile?) marks tasks as submitting (state 8)
 7.  Marks tasks as submitted (state 1)
 8.  Schedules blocks/jobs on the compute nodes. Active blocks are 
      therefore pilots.
 9.  Bootstrap on each active block. More than one worker can bootstrap 
      for each block/pilot depending on how many cores each worker needs 
      as indicated by the user in swift.conf. Workers are pilot agents.
 10. Stages in the input files of the tasks that are ready to be executed 
      on the workers that have become active, if any (task state 16).
 11. Executes tasks (state 2).
 12. Stages out the output files of the tasks that have terminated 
      (state 17). Note that this includes stderr.txt, stdout.txt, 
      wrapper.error, wrapper.log for every task.
 13. Marks tasks as completed (state 7).
 14. Marks the jobs referring to the completed tasks as ended.
 15. Shuts down the blocks (i.e. jobs running on the compute node(s)). 
      **NOTE**: this happens also when jobs are waiting for execution 
      on the resource on which this block is active. This means that in its 
      current configuration, Swift+Coaster do not reuse pilots. After 
      executing the first batch of tasks, the pilot is shut down. Coaster 
      queue enough pilots of the maximum size (i.e. with the maximum amount 
      of compute node configured by the user in swift.config) to guarantee 
      as much concurrency as the maximum amount of jobs allowed to be queue 
      on that specific resource (also configured in swift.conf). This should 
      be visible in our measurements as multiple (and concurrent) queue time 
      for each scheduled pilot.
 16. Marks the workers that were running on the blocks that have been shut 
      down as shut down too.
 17. Marks the blocks as done.
 ```

  Timings derived from the logs:
  ```
 | Name | Owner   | Entities       | timing        | Start tag | End tag   |
 |------|---------|----------------|---------------|-----------|-----------|
 | TTC* | Swift   | Session        | TTC           | start     | end       |
 | Tss  | Swift   | Jobs           | Setting_up    | init      | task      |
 | Tse  | Swift   | Jobs           | Executing     | task      | end       |
 | Tw   | Coaster | Jobs/Tasks     | Submitting    | task      | active    |
 | Te * | Coaster | Tasks          | Executing     | active    | completed |
 | Tsi  | Coaster | Tasks          | Staging_in    | stage_in  | active    |
 | Tso  | Coaster | Tasks          | Staging_out   | stage_out | completed |
 | Tq * | Coaster | Blocks         | Queuing       | requested | active    |
 | Ta   | Coaster | Blocks         | Executing     | active    | done      |
 | Tb   | Coaster | Blocks/Workers | Bootstrapping | active    | active    |
 | Twe  | Coaster | Workers        | Executing     | active    | shutdown  |

 Descriptions
 ------------
 - TTC : total time to completion of the whole session.
 - Tss : Time taken by Swift to set up each task for execution. Can be used
          to determine the percentage of TTC spent on interpreting the given
          swift script. In our experiments this is very short.
 - Tse : Time taken to execute each task as logged by Swift. It can be
          compared to the executing time recorded by Coaster for
          sanity/consistency check purposes. Did the sanity check, seems fine.
 - Tw  : Time taken by Coaster to schedule a block (i.e., job) on the local
          LRMS + block queuing time of that block. Equivalent to AIMES Tw
 - Te  : Time taken by Coaster to execute each task on a worker (i.e.,
          agent). Includes staging in and out timings. Equivalent to AIMES Te.
 - Tsi : Time taken by Coaster to stage the task's input file(s) if any.
          Useful if we will decide to include data-related timings in the
          paper.
 - Tso : Time taken by Coaster to stage the task's output file(s).  Useful to
          measure Coaster's overhead in saving out/err files after task
          execution.
 - Tq  : Time spent by each Block, i.e. pilot, in the resource's queue.
          NOTE: All the time stamps recording by RemoteLogHandler may be
          inaccurate.
 - Ta  : Time spent by each block, i.e. pilot, executing. NOTE: All the
          time stamps recording by RemoteLogHandler may be inaccurate. This
          needs further verification.
 - Tb  : Time required by the worker, i.e. agent, to bootstrap. NOTE:
          This timing is NOT accurate.
 - Twe : Time spent by each worker, i.e, agent, executing. NOTE: All
          the time stamps recording by RemoteLogHandler may be inaccurate.
          This needs further verification.
  ```

  State model:
  
  ```
         | start | init | task | requested | B active | W active | stg_in | T active | stg_out | completed | shutdown | B done | end |
  |------|---|------|------|---------|-----------|----------|---------|---------|---------|----------|----------|----------|------|--|
  | TTC* |   |********************************************************************************************************************|  |
  | Tss  |          |......|                                                                                                         |
  | Tse  |                 |......................................................................................................|  |
  | Tw * |                 |******************************************|                                                              |
  | Te * |                                                            |******************************|                               |
  | Tsi  |                                                            |.........|                                                    |
  | Tso  |                                                                                |..........|                               |
  | Tq   |                           |...........|                                                                                   |
  | Ta   |                                       |.........................................................................|         |
  | Tb   |                                       |..........|                                                                        |
  | Twe  |                                                  |...................................................|                    |
  
  NOTE: This state diagram repeats for every resource with or without temporal
        overlapping.
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
