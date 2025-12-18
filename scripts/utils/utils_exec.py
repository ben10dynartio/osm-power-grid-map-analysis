import config
import json
import runpy
from pathlib import Path

def execute_all_steps(country_code, download=True, graph=True, skipdownload=""):
    scriptfolder = Path(__file__).parent.parent
    config.COUNTRY_CODE = country_code

    if download:
        if 'a' not in skipdownload:
            print(">> Step1a - Download data (country shape, towers and transitions, lines)")
            runpy.run_path(scriptfolder / "step1a_overpass_country.py", run_name="__main__")
        if 'b' not in skipdownload:
            print(">> Step1b - Download line and nodes")
            runpy.run_path(scriptfolder / "step1b_overpass_line_tower.py", run_name="__main__")
        if 'c' not in skipdownload:
            print(">> Step1c - Download substations")
            runpy.run_path(scriptfolder / "step1c_overpass_substation.py", run_name="__main__")
        if 'd' not in skipdownload:
            print(">> Step1d - Download circuit")
            runpy.run_path(scriptfolder / "step1d_overpass_circuit.py", run_name="__main__")

    if graph:
        print(">> Step2 - Prepare for graph (pre-graph)")
        runpy.run_path(scriptfolder / "step2_prepare_for_graph.py", run_name="__main__")
        print(">> Step2o - Integrate circuit in pre-graph.py")
        runpy.run_path(scriptfolder / "step2o_manage_circuit.py", run_name="__main__")
        print(">> Step3 - Build graph and analyse connectivity (post-graphe)")
        runpy.run_path(scriptfolder / "step3_build_graph.py", run_name="__main__")


def add_error(errorlist, errordict, log_level=config.LOG_LEVEL):
    if log_level == "DEBUG":
        print("  * ERROR :", errordict)
    errorlist.append(errordict)

def errors_to_file(data, country_code, filename):
    Path(config.ERRORS_PATH).mkdir(exist_ok=True)
    Path(config.ERRORS_PATH / country_code).mkdir(exist_ok=True)
    with open(config.ERRORS_PATH / country_code / filename, "w", encoding="utf-8") as f:
        json.dump(data, f)

