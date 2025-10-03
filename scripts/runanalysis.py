"""
Use this script for running all steps for one given country
for example, for Comlombia (code ISO2 = CO) :
    python runanalysis.py CO
    python runanalysis.py CO -d # download only data
    python runanalysis.py CO -g # process only graph analysis
"""

import argparse
import config
from utils_exec import execute_all_steps

parser = argparse.ArgumentParser()
parser.add_argument("country", help="Country code iso a2")
parser.add_argument("-d", "--download", action="store_true", help="Download only")
parser.add_argument("-g", "--graph", action="store_true", help="Graph analysis only")
args = parser.parse_args()

d, g = args.download, args.graph
if (not d) & (not g):
    d, g = True, True

print(f"> Starting execution for {args.country}")
execute_all_steps(args.country, d, g)


