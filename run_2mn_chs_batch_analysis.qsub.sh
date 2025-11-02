#!/bin/bash

# Grid Engine options (lines prefixed with #$)
# Job name
#$ -N Batch_2mn_Bluesky_CHS
#$ -o Batch_2mn_Bluesky_CHS.o$JOB_ID
#$ -e Batch_2mn_Bluesky_CHS.e$JOB_ID

# Use the current working dir
#$ -cwd

# Request GPU nodes (adjust to your cluster's resource name)
#$ -q gpu
#$ -l gpu=2
#$ -pe sharedmem 4

# Email me when job is done (customize)
#$ -m bea -M s1732775@ed.ac.uk

## Walltime (hh:mm:ss)
#$ -l h_rt=24:00:00
## Memory
#$ -l mem=32G

# Initialise the environment modules
. /etc/profile.d/modules.sh
# Load conda/micromamba environment (customize)
module load anaconda
micromamba activate HTB2026

echo "Running 2M CHS sampled analysis on host: $(hostname)"
echo "Job id: $JOB_ID"
echo "Working dir: $(pwd)"

# make sure results dir exists
mkdir -p results

# run the python script - customize python path if needed
python3 2mn_chs_batch_analysis.py --n-samples 10000 --batch-size 32 --topk-mean 3 --threshold 0.25

echo "Done"

# Notes:
# - Activate your environment that has `transformers`, `datasets`, `torch` before running.
# - Adjust GPU/resource request lines to match your cluster configuration.
