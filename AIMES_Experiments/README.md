# AIMES only experiments

In standalone mode, AIMES uses Skeletons to describe distributed applications.
Skeleton provides both a description notation for multi-stage workloads, and a
task.c program that is executed on the remote resource. Once compiled, task.c
can be told to run for a certain amount of time, with a certain amount of
cores, and with a certain amount of input and output files of defined size.

Related paper at: https://bitbucket.org/shantenujha/aimes

* [Experimental Workflow](#experimental-workflow)
* [Data Analysis Workflow](#data-analysis-workflow)

## Experimental Workflow
1. Prerequisites: Python 2.7; pip; git
1. Clone this repository:

  ```
  git clone git@github.com:radical-experiments/AIMES-Swift.git
  ```

1. Clone the AIMES software stack:

  ```
  git clone -b devel git@github.com:radical-cybertools/aimes.emgr.git
  git clone git@github.com:radical-cybertools/aimes.bundle.git
  git clone -b fix/retval git@github.com:applicationskeleton/Skeleton.git
  ```

1. Install the AIMES software stack:

  ```
  virtualenv ~/ve/aimes-swift-experiments
  . ~/ve/aimes-swift-experiments/bin/activate
  cd aimes.emgr; pip install -U .; cd -
  cd aimes.bundle; pip install -U .; cd -
  cd Skeleton; pip install -U .; cd -
  ```

1. Set up experiment environment:

  ```
  cd AIMES-Swift/AIMES_Experiments/bin
  . setup.sh
  ```

1. Edit the file ```experiment.json``` to set:

  * **"mongodb"**: RADICAL-Pilot communication/coordination and experiment data.
  * **"scales"**: list of BoT sizes. E.g., [8, 32, 256, 2048].
  * **"iterations"**: number of times each run at any scale is repeated. E.g., 4.
  * **"project_ids"**: your XSEDE allocation/project for each resource.
  * **"log.email.recipients"**: add your e-mail address for notification.
  * **"bundle.resource.unsupported"**: list of resources to target.
  * **"skeleton.tasks.duration.max|min"**: use the same n of seconds. E.g., 900.

1. Copy and compile ```skeleton.c``` on each target resource. For example, with Stampede and assuming passwordless ssh auth and $HOME/bin in $PATH on Stampede:

  ```
  scp ../../../Skeleton/src/aimes/skeleton/task.c stampede.tacc.xsede.org:
  ssh stampede.tacc.xsede.org 'gcc -o task -lm task.c; cp task bin'
  ```

1. Run the experiment script:

  ```
  python aimes_only.py experiment.json
  ```

  The data of each run of the experiment are saved into a dedicated directory with the following naming convention: run\-\<scale\>\_late\_uniform\_\<n\_run\>.

## Data Analysis Workflow

<!-- The analysis wrokflow is designed to be automated, reusable, and extensible. It can be automated by running the following commands from a 'master' shell script (not provided). The wrokflow incrementally integrates new data to those previously collected. Raw, wrangled, and analysis data are all kept across runs preserving the reproducibility of the analysis and (to a certain extent) the provenance of the data. When needed, new analyses can be added to a single step of the workflow without altering the other steps.

1. Prerequisites: Bash on Linux. Bask on OSX requires GNU coreutils (brew install coreutils) and to export ```PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH"```

2. If the file ```AIMES_Swift_experiments/raw.tar.bz2``` exists, from the repository's root directory run:

  ```
  tar xfj AIMES_Swift_experiments/raw.tar.bz2 -C AIMES_Swift_experiments
  ```
3. Run the data Wrangler. From the repository's root directory run:

  ```
  . AIMES_Swift_experiments/bin/data_wrangling.sh
  ```

  The wrangler copies the run directories from the repository's root to ```AIMES_Swift_experiments/raw```. Each run is copied into a directory with the following name convention: ```run-<size-of-bag>_<type-of-binding>_<run-counter>```. The size of the bag and the type of binding are read from the file ```metadata.json``` within each run directory. The wrangler checks for previous directories and increments run counters of new directories accordingly. The wrangler copies the Swif.log of each run into ```AIMES_Swift_experiments/analysis/<type-of-binding>/<size-of-bag>/Swift.<milliseconds-since-epoch>.log```.

4. Extract timestamps for run and tasks from the Swift logs. From the ```AIMES_Swift_experiments/analysis``` directory run:

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

5. Compute timings from the timestamps of each run. From the ```AIMES_Swift_experiments/analysis``` directory run:

  ```
  . ../bin/compute_timings.sh
  ```

  ```compute_timings.sh``` calls the Python script ```get_timings.py``` for each timesteps file. A file ```<name-of-timing>.data``` is created in each ```<type-of-binding>/<size-of-bot>``` directory. Each file contains a list of timings in seconds since EPOCH for every run. When new runs are processed, their new timings are appended to the existing files. The existing files are backed up in place with the ```.bak``` extension before being appended.  ```get_timings.py``` can and *should* be extended to calculate and output all the timimngs as requested by the experiment analysis.

6. Aggregate each type of timing into a ```csv``` file. From the ```AIMES_Swift_experiments/analysis``` directory run:

  ```
  . ../bin/aggregate_timings.sh
  ```

  A file ```<name-of-timing>_<type-of-binding>.csv``` is created in ```AIMES_Swift_experiments/analysis``` (e.g., ```late_TTC.csv```). When new runs are added, their new timings are appended to the existing files. The existing files are backed up in place with the ```.bak``` extension. The columns of the cvs file are the sizes of the bot; the raw are the recorded timings:

  | 8 | 32 | 256 | 2048 |
  |---|----|-----|------|
  |1147|1168|1626|7719|
  |1142|1934|2167||
  |||2203||

7. Diverse approaches can be used to produce plots from the csv files.
 -->
