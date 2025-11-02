#!/bin/bash

# Grid Engine options (lines prefixed with #$)
# Job name
#$ -N Batch_Bluesky_CHS_Analysis
#$ -o Batch_Bluesky_CHS_Analysis.o$JOB_ID
#$ -e Batch_Bluesky_CHS_Analysis.e$JOB_ID

# Use the current working dir
#$ -cwd

# Request one GPU in the gpu queue:
#$ -q gpu 
#$ -l gpu=2

# Email me when job is done
#$ -m bea -M s1732775@ed.ac.uk 

## Walltime (hh:mm:ss)
#$ -l h_rt=24:00:00
## Memory
#$ -l mem=32G


# Initialise the environment modules
. /etc/profile.d/modules.sh
# You have to load anaconda so that you can use conda
module load anaconda
micromamba activate HTB2026

echo "Running CHS batched analysis on host: $(hostname)"
echo "Job id: $JOB_ID"
echo "Working dir: $(pwd)"

# make sure results dir exists
mkdir -p results

# run the python script - customize python path if needed
python3 run_batch_analysis.py --batch-size 32 --topk-mean 3 --threshold 0.25

echo "Done"

### Notes:
### - If your Grid Engine uses a different GPU resource name (for example 'gpus' or 'cuda'), change the '#$ -l gpu=2' line accordingly.
### - Activate your conda/venv environment that has `transformers`, `torch`, and other dependencies before calling python3.pip