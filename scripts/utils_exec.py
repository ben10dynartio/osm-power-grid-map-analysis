import config
import json
import runpy
from pathlib import Path

def execute_all_steps(country_code, download=True, graph=True):
    selfpathfolder = Path(__file__).parent
    config.COUNTRY_CODE = country_code

    if download:
        print(">> Step1 - Download data (country shape, towers and transitions, lines)")
        runpy.run_path(selfpathfolder / "step1a_overpass_country_line_tower.py", run_name="__main__")
        print(">> Step1a - Download data (substations)")
        runpy.run_path(selfpathfolder / "step1b_overpass_substation.py", run_name="__main__")
        print(">> Step1b - Download data")
        runpy.run_path(selfpathfolder / "step1c_overpass_circuit.py", run_name="__main__")

    if graph:
        print(">> Step2 - Prepare for graph (pre-graph)")
        runpy.run_path(selfpathfolder / "step2_prepare_for_graph.py", run_name="__main__")
        print(">> Step2o - Integrate circuit in pre-graph.py")
        runpy.run_path(selfpathfolder / "step2o_manage_circuit.py", run_name="__main__")
        print(">> Step3 - Build graph and analyse connectivity (post-graphe)")
        runpy.run_path(selfpathfolder / "step3_build_graph.py", run_name="__main__")


def add_error(errorlist, errordict, log_level=config.LOG_LEVEL):
    if log_level == "DEBUG":
        print("  * ERROR :", errordict)
    errorlist.append(errordict)

def errors_to_file(data, country_code, filename):
    Path(config.ERRORS_PATH).mkdir(exist_ok=True)
    Path(config.ERRORS_PATH / country_code).mkdir(exist_ok=True)
    with open(config.ERRORS_PATH / country_code / filename, "w", encoding="utf-8") as f:
        json.dump(data, f)

