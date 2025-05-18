import config

config.DATA_PATH = "../data/"
config.BUFFER_DISTANCE = 250

COUNTRY_LIST = {
    "MG":"Madagascar",
    "LB":"Lebanon",
    "EC":"Ecuador",
    "SZ":"Eswatini",
}

# Intialize config
for code, name in COUNTRY_LIST.items():
    print(f"> Starting execution for {name} ({code})")
    config.COUNTRY_CODE = code
    # Run scripts
    exec(open("./step1_download_data_overpass.py").read())
    exec(open("./step2_prepare_for_graph.py").read())
    exec(open("./step3_build_graph.py").read())
    print(f"> End {code}")