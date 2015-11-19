# AIMES-Swift
Measuring trade offs of AIMES and Swift integration. A set of three experiments is planned to compare the time to completion of a set of workloads/workflows when executed via Swift, AIMES, or the integration of the two.

Related paper at: https://bitbucket.org/shantenujha/aimes

## Prerequisites

Python 2.7; ant; pip; git

## Experimental Workflow
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
    "cores": {
      [<int tasks>, <int n_cores>],
      [<int tasks>, <int n_cores>]
    },
    "durations": {
      [<int tasks>, <int duration>],
      [<int tasks>, <int duration>]
    }
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

1. Cpy the Swift log file into data:
 
  ```
  cp run<nnn>/swift.log data/swift/emgr_sid.<nnnn>.<nnnn>/
  ```
  
1. Copy the ```data``` directory into ```exp-n```.
1. Pull and push the repository. 
