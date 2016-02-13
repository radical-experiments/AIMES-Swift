# Swift experiments

In standalone mode, Swift uses the Coaster System to execute tasks on pilots. 

Related paper at: https://bitbucket.org/shantenujha/aimes

* [Experimental Workflow](#experimental-workflow)
* [Data Analysis Workflow](#data-analysis-workflow)

## Experimental Workflow

1. Prerequisites:
1. Clone this repository:

  ```
  git clone git@github.com:radical-experiments/AIMES-Swift.git
  ```

1. Clone the Swift software stack:

  ```
    git clone https://github.com/swift-lang/swift-k.git
    cd swift-k
    git fetch
  ```

1. Install the Swift software stack:

  ```
    # Please make sure you have java and ant installed
    cd swift-k
    ant redist
    export PATH=$PWD/dist/swift-svn/bin:$PATH
  ```

1. Set up experiment environment: To run swift only experiments, ensure that you have ssh keys setup to allow for passwordless access to stampede and gordon. You should be able to ssh to ```stampede.tacc.utexas.edu``` and ```gordon.sdsc.edu```, without a password prompt.

1. Edit the files:
  * ```AIMES-Swift/Swift_Experiments/swift.conf``` to set:
    
    ```
    sites: [stampede, gordon]  # runs both sites
    sites: stampede            # runs only stampede
    ```
    
  * test_runner_runner.sh:
  
    ```
    REPEAT determines the times the experiment is repeated [4])
    ```
  
  * test_runner.sh:
  
    ```
    Set emails, remote sleep DUR, etc
    ```

1. Run the script...:

  ```
    ./test_runner_runner.sh
  ```

## Data Analysis Workflow

The analysis wrokflow is designed to be automated, reusable, and extensible. The wrokflow incrementally integrates new data to those previously collected. Raw, wrangled, and analysis data are all kept across runs preserving the reproducibility of the analysis and (to a certain extent) the provenance of the data. When needed, new analyses can be added to a single step of the workflow without altering the other steps.

1. Prerequisites: python and Bash on Linux or OSX.

1. Raw data are kept in the directory ```raw_data/name_of_resource(s)/exp-xxx```. Raw data are **NOT** uploaded to git dur to space limitations. Raw data are tarred and b2zipped into a single file for archive purposes.

1. Data wrangling:

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
