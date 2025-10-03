import argparse
import config
from utils_exec import execute_all_steps

parser = argparse.ArgumentParser()
parser.add_argument("--country", "-c", type=str, default="TZ", help="Country code iso a2")
args = parser.parse_args()

print("Country :", args.country)
config.COUNTRY_CODE = args.country
execute_all_steps()


