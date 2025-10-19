"""
Use this script for running all steps for one given country
for example, for Comlombia (code ISO2 = CO) :
    python run.py CO
    python run.py CO -d # download only data
    python run.py CO -g # process only graph analysis
"""

import argparse
import config
from pathlib import Path
from utils_exec import execute_all_steps

parser = argparse.ArgumentParser()
parser.add_argument("country", help="Country code iso a2")
parser.add_argument("-d", "--download", action="store_true", help="Download only")
parser.add_argument("-g", "--graph", action="store_true", help="Graph analysis only")
parser.add_argument("-o", "--outpath", type=str, help="Output folder path")
args = parser.parse_args()

d, g = args.download, args.graph
if (not d) & (not g):
    d, g = True, True

print(f"> Starting execution for {args.country}")
if args.outpath:
    config.DATA_PATH = Path(args.outpath)
execute_all_steps(args.country, d, g)


