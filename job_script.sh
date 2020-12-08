#!/bin/bash -l

# Request minutes of wallclock time (format hours:minutes:seconds).
#$ -l h_rt=0:45:0

# Request gigabytes of RAM for each core/thread (must be an integer followed by M, G, or T)
#$ -l mem=1G

# Request gigabytes of TMPDIR space (default is 10 GB)
#$ -l tmpfs=5G

# Set the name of the job.
#$ -N testing

# Request cores.
#$ -pe smp 1

# Set up the job array.  In this instance we have requested 10000 tasks
# numbered 1 to 10000.
#$ -t 801-1000

# Set the working directory to somewhere in your scratch space.
#$ -wd /home/ucfarm0/Scratch

# 8. Run the application.

python3 /home/ucfarm0/SP_LG/SP_LG/master_script.py $SGE_TASK_ID 55000 1000 -hpc

