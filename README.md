# AIMES-Swift
Measuring trade offs of AIMES and Swift integration. A set of three experiments is planned to compare the time to completion of a set of workloads/workflows when executed via Swift, AIMES, or the integration of the two.

Related paper at: https://bitbucket.org/shantenujha/aimes

* [Experimental Workflow](#experimental-workflow)
* [Data Analysis Workflow](#data-analysis-workflow)

## Experimental Workflow
1. Prerequisites: Python 2.7; ant; pip; git
1. Clone this repository:

  ```
  git clone git@github.com:radical-experiments/AIMES-Swift.git
  ```

1. Clone AIMES and Swift software stack:

  ```
  git clone git@github.com:radical-cybertools/aimes.emgr.git
  git clone git@github.com:radical-cybertools/aimes.bundle.git
  git clone git@github.com:swift-lang/swift-k.git
  ```

1. Install the AIMES software stack:
 
  ```
  virtualenv ~/ve/aimes-swift-experiments
  . ~/ve/aimes-swift-experiments/bin/activate
  cd aimes.emgr; git checkout devel; pip install -U .; cd -
  cd aimes.bundle; pip install -U .; cd -
  pip install pandas
  ```

1. Install the Swift software stack:

  ```
  cd swift-k/
  git checkout release-0.96-swift
  ant redist
  export PATH=$PWD/dist/swift-svn/bin:$PATH
  cd -
  ```

1. Move into the ```AIMES-Swift``` directory.
1. Edit the file ```bag_of_tasks.swift``` or write a new Swift script describing the workflow you want to use for the experiment.
1. Edit the file ```swift.conf``` to use the ```"local:aimes-emanager"``` jobManager.
1. Edit the file ```experiment.json``` adding or removing unsupported resources:

  ```
  "bundle": {
    "resources": {
      "unsupported": {
        "supermic.cct-lsu.xsede.org": {
          "sched": "pbs",
          "fconf": "conf/xsede.supermic.json"
        },
        "comet.sdsc.xsede.org": {
          "sched": "slurm",
          "fconf": "conf/xsede.comet.json"
        },
        "gordon.sdsc.xsede.org": {
          "sched": "pbs",
          "fconf": "conf/xsede.gordon.json"
        }
      }
    }
  },
  ```

  If needed, write a file in ```conf/<name_resource>.json``` with the configuration options for the chosen resources.

1. In a dedicated terminal, start the AIMES rest interface:

  ```
  . ~/ve/aimes-swift-experiments/bin/activate
  cd AIMES-Swift/
  aimes-emgr-rest experiment.json
  ```

1. In the initial terminal, run the swift script:

  ```
  swift <experiment_script>.swift
  ```

1. Stop the AIMES rest interface with ```Ctrl+c```.
1. Download session for the experiment:

  ```
  aimes-emgr-rest-experiments experiment.json
  ```

1. Upon success of the previous command, create a directory ```exp-n``` where ```n``` uniquely and incrementally indicates the number of the experiment just run.
1. Create a file inside ```exp-n``` called ```metadata.json``` with the following information:

  ```
  {
    "n_tasks": <int>,
    "cores": [
      [<int tasks>, <int n_cores>],
      [<int tasks>, <int n_cores>]
    ],
    "durations": [
      [<int tasks>, <int duration>],
      [<int tasks>, <int duration>]
    ]
  }
  ```
  
  Example:
  
  ```
  {
    "n_tasks": 128,
    "cores": {
      [128, 1]
    },
    "durations": {
      [128, 15]
    }
  }
  ```
  
  Note:
  * Durations are in minutes.
  * ```"cores"``` and ```"durations"``` are used to describe partions of the set of tasks. At the moment, we use just 1 core and 15 minutes duration for each task but we will have to use more complex distributions or cores and durations.

1. Copy the Swift log file into data:
 
  ```
  cp run<nnn>/swift.log data/swift/emgr_sid.<nnnn>.<nnnn>/
  ```
  
1. Copy the ```data``` directory into ```exp-n```.
1. Pull and push the repository. 

## Data Analysis Workflow

The following wrokflow is designed to be automated, reusable, and extensible. It can be fully automated by running the following commands from a 'master' shell script. The wrokflow incrementally integrate new data without overwriting data previously corrected. Raw, wrangled, and analysis data are all kept across runs preserving the reproducibility of the analysis and (to a certain extent) the provenance of the data. When needed, new analytical steps can be added to a single step of the workflow without altering the other steps.

1. Prerequisites: Bash on Linux.
2. If the file ```AIMES_Swift_experiments/raw.tar.bz2``` exists, from the repository's root directory run:

  ```
  tar xfj AIMES_Swift_experiments/raw.tar.bz2 -C AIMES_Swift_experiments
  ```
1. Run the data Wrangler. From the repository's root directory run: 

  ```
  . AIMES_Swift_experiments/bin/data_wrangling.sh
  ```
  
  The wrangler copies the run directories from the repository's root to ```AIMES_Swift_experiments/raw```. Each run is copied into a directory with the following name convention: ```run-<size-of-bag>_<type-of-binding>_<run-counter>```. The size of the bag and the type of binding are read from the file ```metadata.json``` within each run directory. The wrangler checks for previous directories and increments run counters of new directories accordingly. The wrangler copies the Swif.log of each run into ```AIMES_Swift_experiments/analysis/<type-of-binding>/<size-of-bag>/Swift.<milliseconds-since-epoch>.log```.
  
2. Extract timestamps for run and tasks from the Swift logs. From the ```AIMES_Swift_experiments/analysis``` directory run:

  ```
  . ../bin/get_timestamps.sh
  ```
  
  ```get_timestamps.sh``` calls the Swift log parser ``swift-timestamps.py``` for each log file. The parser outputs a json file with the following timestamps:
  
  ```json
  {
    "Tasks": {
        "R-4-1-1448926016471": {
            "Active": 1448872242, 
            "New": 1448872022, 
            "Completed": 1448873163, 
            "Submitting": 1448872022, 
            "Submitted": 1448872022
        },
        ...
    },
    "Run": {
        "Start": 1448872016, 
        "Finish": 1448873163, 
        "ID": "run006"
    }
  }
  ```
  and backups the oringal log files to ```<type-of-binding>/<size-of-bot>/swift.<epoch>.bak```.  

3. Compute timings from the timestamps of each run. From the ```AIMES_Swift_experiments/analysis``` directory run:
 
  ```
  . ../bin/compute_timings.sh
  ```
  
  ```compute_timings.sh``` calls the Python script ```get_timings.py``` for each timings file. A file ```<name-of-timing>.data``` is created in each ```<type-of-binding>/<size-of-bot>``` directory. Each file contains a list of timings of every run. When new runs are added, their new timings are appended to the existing files. The existing files are backed up in place with the ```.bak``` extension. This script can and should be extended to calculate and output all the timimngs as requested by the experiment analysis.

3. Aggregate each type of timing into a ```csv``` file. From the ```AIMES_Swift_experiments/analysis``` directory run:

  ```
  . ../bin/aggregate_timings.sh
  ```
  
  A file ```<name-of-timing>_<type-of-binding>.csv``` is created in ```AIMES_Swift_experiments/analysis``` (e.g., ```late_TTC.csv```). When new runs are added, their new timings are appended to the existing files. The existing files are backed up in place with the ```.bak``` extension. The columns of the cvs file are the sizes of the bot; the raw are the recorded timings:
  
  | 8 | 32 | 256 | 2048 |
  |---|----|-----|------|
  |1147|1168|1626|7719|
  |1142|1934|2167||
  |||2203||
  
3. Diverse approaches can be used to produce plots from the csv files.
