"""
Use this script for running all steps for one given country
for example, for Colombia (code ISO2 = CO) :
    python run.py circuitlength CO
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import argparse
from pathlib import Path
import subprocess

import pandas as pd

SCRIPT_PATH = Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument("action", help="Action")
parser.add_argument("obj", help="Objecttype")
parser.add_argument("-c", "--country", help="Country code iso a2")
parser.add_argument("-d", "--date", type=str, help="Date of layer", default="CURRENT_TIMESTAMP")

args = parser.parse_args()

df = pd.read_csv(configapps.OUTPUT_WORLD_FOLDER_PATH / "wikidata_countries_info_brut.csv")
#codeiso2,country,countryLabel,wikipedia,area_km2,flag_image,osm_rel_id,continent,languages,locator_map,population,gdp_bd
country_osm_rel_id = df[df["codeiso2"]==args.country].iloc[0]["osm_rel_id"]

if args.action == "layerbuild": # Quality and Grid Stats
    if args.obj == "ln":
        subprocess.run(f"python {SCRIPT_PATH}/layerbuilder_linesxnodes.py -c {country_osm_rel_id} -d {args.date} -f shapes/{args.country}/",
                       shell=True)
    elif args.obj == "sub":
        subprocess.run(f"python {SCRIPT_PATH}/layerbuilder_substations.py -c {country_osm_rel_id} -d {args.date} -f shapes/{args.country}/",
                       shell=True)
    else:
        raise ValueError(f"Unknown object type : {args.obj}")