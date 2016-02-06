# Swift experiments

In standalone mode, Swift uses the Coaster System to execute tasks on pilots. 

Related paper at: https://bitbucket.org/shantenujha/aimes

* [Experimental Workflow](#experimental-workflow)
* [Data Analysis Workflow](#data-analysis-workflow)

## Experimental Workflow

Yadu: Please add a descitpion of how to run experiments with one or two XSEDE resources.

1. Prerequisites:
1. Clone this repository:

  ```
  git clone git@github.com:radical-experiments/AIMES-Swift.git
  ```

1. Clone the Swift software stack:

  ```
  git clone -b devel git@github.com:
  git clone git@github.com:
  ...
  ```

1. Install the Swift software stack:

  ```
  ...
  ```

1. Set up experiment environment:

  ```
  ...
  ```

1. Edit the file ```...``` to set:

  * **...**: ...
  * **...**: ...
  * ...

1. Run the script...:

  ```
  ...
  ```

  ...


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
