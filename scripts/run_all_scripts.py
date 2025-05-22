import config
import shutil
from pathlib import Path

# Cross-script config
config.DATA_PATH = "../data/"
config.BUFFER_DISTANCE = 250

# Config for this script
COUNTRY_LIST = {'AO': 'Angola', 'BF': 'Burkina Faso', 'BI': 'Burundi'}

# set it to a two-digit country code to skip all countries until this one (the indicated code will be processed)
# Useful we re-running the script if an error has been encountered, without modifying country list
SKIP_LIST_UNTIL = None

# Processing -----------------------
list_errors = []
flag_skip = (SKIP_LIST_UNTIL is None) # Set to True to skip countries

for code, name in COUNTRY_LIST.items():
    if SKIP_LIST_UNTIL:
        if SKIP_LIST_UNTIL == code:
            flag_skip = False
        else:
            continue #Skip until country code
    print(f"> Starting execution for {name} ({code})")
    config.COUNTRY_CODE = code
    # Run scripts
    try:
        exec(open("./step1_download_data_overpass.py").read())
        exec(open("./step2_prepare_for_graph.py").read())
        exec(open("./step3_build_graph.py").read())
    except Exception as e:
        print("SCRIPT ERROR", e)
        list_errors.append((code, name))
    print(f"> End {code}\n")

print("\nEnd of processing country lists")
if list_errors:
    print("Errors have been encountered for the following countries = ", list_errors)
