Bug status
==========


Symptom:
When these bag of tasks script is run on both stampede and gordon, with sleep tasks of 30 mins which extend past the walltime of the jobs and the workers, there are some silent failures which are missed by swift.
Somehow active blocks are lost without swift noticing that tasks that were active have gone missing.
and
Swift reports that there are jobs submitted to the queue, while there are no jobs waiting in the queue on either sites.
