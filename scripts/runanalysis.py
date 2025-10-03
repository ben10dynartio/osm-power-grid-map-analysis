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

config.COUNTRY_CODE = args.country

execute_all_steps(d, g)


