import config
import runpy
from pathlib import Path

def execute_all_steps():
    selfpathfolder = Path(__file__).parent
    print(">> Step1 - Download data (country shape, towers and transitions, lines)")
    runpy.run_path(selfpathfolder / "step1a_overpass_country_line_tower.py", run_name="__main__")
    print(">> Step1a - Download data (substations)")
    runpy.run_path(selfpathfolder / "step1b_overpass_substation.py", run_name="__main__")
    print(">> Step1b - Download data")
    runpy.run_path(selfpathfolder / "step1c_overpass_circuit.py", run_name="__main__")
    print(">> Step2 - Prepare for graph (pre-graph)")
    runpy.run_path(selfpathfolder / "step2_prepare_for_graph.py", run_name="__main__")
    print(">> Step2o - Integrate circuit in pre-graph.py")
    runpy.run_path(selfpathfolder / "step2o_manage_circuit.py", run_name="__main__")
    print(">> Step3 - Build graph and analyse connectivity (post-graphe)")
    runpy.run_path(selfpathfolder / "step3_build_graph.py", run_name="__main__")