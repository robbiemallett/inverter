#!/bin/bash -l

# Request minutes of wallclock time (format hours:minutes:seconds).
#$ -l h_rt=12:00:0

# Request gigabytes of RAM for each core/thread (must be an integer followed by M, G, or T)
#$ -l mem=1G

# Request gigabytes of TMPDIR space (default is 10 GB)
#$ -l tmpfs=2G

# Set the name of the job.
#$ -N SMRT_fitting

# Request cores.
#$ -pe smp 1

# Set up the job array.  In this instance we have requested 10000 tasks
# numbered 1 to 10000.
#$ -t 1-20

# Set the working directory to somewhere in your scratch space.
#$ -wd /home/ucfarm0/Scratch

# 8. Run the application.

#                                                     job_name      niter   hpc_flag

source /home/ucfarm0/inverse_smrt/bin/activate
python /home/ucfarm0/inverse_smrt/inverter/search_mode.py jan_2021_$SGE_TASK_ID 
2 -hpc
