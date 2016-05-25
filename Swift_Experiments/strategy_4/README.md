Analysis
========

Tasks are bound to both Stampede and Gordon and then pilots are submitted to both resource to execute them. This behavior is the same of Strategy 2. Strategy 4 was designed to let Swift to do dynamic (re)scheduling of tasks across *resources* so to avoid having to wait for pilots to become active on both resources to complete the execution of the bag of task. Without this behavior, Strategy 4 and 2 are the same.

Bug status
==========

Symptom:
When this bag of tasks script is run on both stampede and gordon, with sleep tasks of 30 mins which extend past the walltime of the jobs and the workers, there are some silent failures which are missed by swift. Somehow active blocks are lost without swift noticing that tasks that were active have gone missing. Swift reports that there are jobs submitted to the queue, while there are no jobs waiting in the queue on either sites.
